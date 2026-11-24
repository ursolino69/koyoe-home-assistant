import asyncio
import importlib.util
from pathlib import Path
import unittest
from unittest.mock import patch

spec = importlib.util.spec_from_file_location(
    "protocol", Path(__file__).parent / "custom_components/koyoe_local/protocol.py")
p = importlib.util.module_from_spec(spec)
spec.loader.exec_module(p)


class Writer:
    def __init__(self):
        self.frames = []
        self.closed = False
    def write(self, frame):
        self.frames.append(frame)
    async def drain(self):
        pass
    def close(self):
        self.closed = True
    async def wait_closed(self):
        pass


class ProtocolTests(unittest.IsolatedAsyncioTestCase):
    async def test_decodes_read_only_replies(self):
        reader = asyncio.StreamReader()
        for frame in ("f703020002f190", "f70302019f31a9", "f703020096f03f"):
            reader.feed_data(bytes.fromhex(frame))
        writer = Writer()
        async def connect(**kwargs):
            return reader, writer
        with patch.object(p, "READINGS", dict(list(p.READINGS.items())[:3])), patch.object(p.serialx, "open_serial_connection", connect):
            client = p.KoyoeClient("test")
            self.assertEqual(await client.read_all(), {
                "status": 2, "heatsink_temperature": 41.5, "battery_soc": 60.0})
            self.assertEqual([x.hex() for x in writer.frames], [
                "f703758700013ab9", "f703758b0001faba", "f703765f0001bac6"])
            await client.close()
            self.assertTrue(writer.closed)

    async def test_bad_crc_closes_and_next_poll_reconnects(self):
        readers = [asyncio.StreamReader(), asyncio.StreamReader()]
        readers[0].feed_data(bytes.fromhex("f703020002f191"))
        for frame in ("f703020002f190", "f70302019f31a9", "f703020096f03f"):
            readers[1].feed_data(bytes.fromhex(frame))
        writers = [Writer(), Writer()]
        calls = []
        async def connect(**kwargs):
            i = len(calls)
            calls.append(i)
            return readers[i], writers[i]
        with patch.object(p, "READINGS", dict(list(p.READINGS.items())[:3])), patch.object(p.serialx, "open_serial_connection", connect):
            client = p.KoyoeClient("test")
            with self.assertRaises(ValueError):
                await client.read_all()
            self.assertTrue(writers[0].closed)
            self.assertEqual((await client.read_all())["battery_soc"], 60.0)
            self.assertEqual(len(calls), 2)
            await client.close()

    def test_32bit_and_signed_values(self):
        import struct
        for fmt, value in ((">I", 123456), (">i", -1200), (">h", -123)):
            data = struct.pack(fmt, value)
            frame = bytes([247, 3, len(data)]) + data
            frame += p.crc(frame).to_bytes(2, "little")
            self.assertEqual(struct.unpack(fmt, p.parse(frame, len(data)))[0], value)
        self.assertEqual(p.request(30163)[4:6], bytes([0, 2]))

    async def test_optional_exception_does_not_discard_good_readings(self):
        reader = asyncio.StreamReader()
        for frame in ("f703020002f190", "f70302019f31a9", "f703020096f03f"):
            reader.feed_data(bytes.fromhex(frame))
        frame = bytes.fromhex("f78302")
        reader.feed_data(frame + p.crc(frame).to_bytes(2, "little"))
        writer = Writer()
        async def connect(**kwargs):
            return reader, writer
        subset = dict(list(p.READINGS.items())[:4])
        with patch.object(p, "READINGS", subset), patch.object(p.serialx, "open_serial_connection", connect):
            client = p.KoyoeClient("test")
            data = await client.read_all()
            self.assertEqual(data["battery_soc"], 60.0)
            self.assertIsNone(data["pv1_voltage"])
            self.assertFalse(writer.closed)
            await client.close()

    def test_rejects_other_registers_and_exceptions(self):
        with self.assertRaises(ValueError):
            p.request(40000)
        frame = bytes.fromhex("f78302")
        with self.assertRaises(ValueError):
            p.parse(frame + p.crc(frame).to_bytes(2, "little"))


if __name__ == "__main__":
    unittest.main()
