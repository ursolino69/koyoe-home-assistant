"""Narrow read-only KY-EST20KH bench protocol; no control registers."""
import asyncio
import logging
import struct

import serialx

LOGGER = logging.getLogger(__name__)
RESPONSE_TIMEOUT = 3
INPUT_QUIET_TIME = 0.1
INITIAL_DRAIN_TIMEOUT = 1
INITIAL_DRAIN_MAX_BYTES = 1024
INTER_REQUEST_DELAY = 0.5

READINGS = {
    "status": (30087, ">H", 1),
    "heatsink_temperature": (30091, ">h", 0.1),
    "battery_soc": (30303, ">H", 0.4),
    "pv1_voltage": (30097, ">H", 0.1),
    "pv2_voltage": (30098, ">H", 0.1),
    "pv1_current": (30107, ">H", 0.1),
    "pv2_current": (30108, ">H", 0.1),
    "grid_l1_voltage": (30137, ">H", 0.1),
    "grid_l2_voltage": (30138, ">H", 0.1),
    "grid_l3_voltage": (30139, ">H", 0.1),
    "grid_frequency": (30146, ">H", 0.01),
    "pv_power": (30163, ">I", 1),
    "grid_power": (30167, ">i", 1),
    "inverter_power": (30181, ">i", 1),
    "load_power": (30214, ">I", 1),
    "battery_current": (30301, ">h", 0.1),
    "battery_voltage": (30302, ">H", 0.1),
    "battery_soh": (30304, ">H", 0.4),
    "pv_energy_today": (30013, ">H", 0.1),
    "pv_energy_total": (30007, ">I", 0.1),

}


def crc(data):
    value = 0xFFFF
    for byte in data:
        value ^= byte
        for _ in range(8):
            value = (value >> 1) ^ (0xA001 if value & 1 else 0)
    return value


class ProtocolError(ValueError):
    pass


class ModbusException(ProtocolError):
    pass


def request(address):
    if address not in {item[0] for item in READINGS.values()}:
        raise ProtocolError("Register outside tested read-only profile")
    data_format = next(item[1] for item in READINGS.values() if item[0] == address)
    payload = struct.pack(">BBHH", 247, 3, address, struct.calcsize(data_format) // 2)
    return payload + struct.pack("<H", crc(payload))


def parse(reply, byte_count=2):
    if len(reply) < 5 or crc(reply[:-2]) != int.from_bytes(reply[-2:], "little"):
        raise ProtocolError("Invalid response CRC or length")
    if reply[0] != 247:
        raise ProtocolError("Unexpected unit")
    if reply[1] == 0x83 and len(reply) == 5:
        raise ModbusException(f"Modbus exception {reply[2]}")
    if len(reply) != byte_count + 5 or reply[1] != 3 or reply[2] != byte_count:
        raise ProtocolError("Unexpected function or byte count")
    return reply[3:-2]


class KoyoeClient:
    def __init__(self, device):
        self.device = device
        self.reader = self.writer = None
        self.last_address = None
        self.phase = "connect"

    async def close(self):
        writer, self.writer = self.writer, None
        self.reader = None
        if writer:
            writer.close()
            try:
                await asyncio.wait_for(writer.wait_closed(), 5)
            except Exception:
                pass

    async def _read_idle_input(self, quiet_time):
        """Return received bytes, or None after an uninterrupted quiet period."""
        try:
            async with asyncio.timeout(quiet_time):
                data = await self.reader.read(256)
        except TimeoutError:
            return None
        if not data:
            raise ConnectionError("Serial stream closed while waiting for silence")
        return data

    async def _settle_new_connection(self):
        """Discard bounded input on a new stream before sending any request."""
        discarded = 0
        try:
            async with asyncio.timeout(INITIAL_DRAIN_TIMEOUT):
                while discarded < INITIAL_DRAIN_MAX_BYTES:
                    data = await self._read_idle_input(INPUT_QUIET_TIME)
                    if data is None:
                        if discarded:
                            LOGGER.debug("Discarded %d bytes before the first Koyoe request", discarded)
                        return
                    discarded += len(data)
        except TimeoutError:
            pass
        raise ProtocolError("Serial input did not settle after connecting")

    async def _require_quiet_input(self, quiet_time):
        """Fail the cycle if bytes arrive while no reply is expected."""
        self.phase = "receive_idle"
        if await self._read_idle_input(quiet_time) is not None:
            raise ProtocolError("Unexpected serial bytes while no reply was pending")

    async def read_all(self):
        try:
            self.last_address = None
            if self.writer is None:
                self.phase = "connect"
                self.reader, self.writer = await asyncio.wait_for(
                    serialx.open_serial_connection(url=self.device, baudrate=9600), 15
                )
                self.phase = "settle_input"
                await self._settle_new_connection()
            else:
                await self._require_quiet_input(INPUT_QUIET_TIME)

            readings = {}
            for key, (address, data_format, scale) in READINGS.items():
                self.last_address = address
                self.phase = "send"
                self.writer.write(request(address))
                await asyncio.wait_for(self.writer.drain(), RESPONSE_TIMEOUT)
                self.phase = "receive_header"
                header = await asyncio.wait_for(self.reader.readexactly(3), RESPONSE_TIMEOUT)
                if header[0] != 247 or header[1] not in (3, 0x83):
                    raise ProtocolError(f"Invalid header {header.hex()}")
                byte_count = struct.calcsize(data_format)
                if header[1] == 3 and header[2] != byte_count:
                    raise ProtocolError(f"Invalid byte count {header[2]}, expected {byte_count}; header {header.hex()}")
                size = 2 if header[1] == 0x83 else byte_count + 2
                self.phase = "receive_data"
                tail = await asyncio.wait_for(self.reader.readexactly(size), RESPONSE_TIMEOUT)
                try:
                    raw = struct.unpack(data_format, parse(header + tail, byte_count))[0]
                except ModbusException:
                    if key in ("status", "heatsink_temperature", "battery_soc"):
                        raise
                    readings[key] = None
                else:
                    value = round(raw * scale, 2)
                    limit = 100000 if "power" in key else 1000 if key.endswith(("voltage", "current")) else 100 if key in ("battery_soh", "grid_frequency") else None
                    if key not in ("status", "heatsink_temperature", "battery_soc") and (raw in (65535, 4294967295) or (limit is not None and abs(value) > limit)):
                        readings[key] = None
                    else:
                        readings[key] = value
                # Modbus RTU read replies carry no register address. If an
                # extra reply appears here, even earlier values may be shifted.
                await self._require_quiet_input(INTER_REQUEST_DELAY)
            self.phase = "validate"
            if not 0 <= readings["battery_soc"] <= 100:
                raise ProtocolError("Battery SOC outside valid range")
            if not -50 <= readings["heatsink_temperature"] <= 150:
                raise ProtocolError("Temperature outside plausible range")
            return readings
        except BaseException:
            await self.close()
            raise
