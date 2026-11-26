import asyncio
import importlib.util
from pathlib import Path
import unittest
from unittest.mock import patch

spec = importlib.util.spec_from_file_location(
    "protocol", Path(__file__).parent / "custom_components/koyoe_local/protocol.py")
p = importlib.util.module_from_spec(spec)
spec.loader.exec_module(p)

CORE_READINGS = dict(list(p.READINGS.items())[:3])
CORE_REPLIES = tuple(
    bytes.fromhex(frame) for frame in ("f703020002f190", "f70302019f31a9", "f703020096f03f")
)


class Writer:
    def __init__(self, *replies):
        self.reader = asyncio.StreamReader()
        self.replies = iter(replies)
        self.frames = []
        self.closed = False

    def write(self, frame):
        self.frames.append(frame)
        reply = next(self.replies)
        if reply is not None:
            self.reader.feed_data(reply)

    async def drain(self):
        pass

    def close(self):
        self.closed = True

    async def wait_closed(self):
        pass


class ProtocolTests(unittest.IsolatedAsyncioTestCase):
    def setUp(self):
        self.enterContext(patch.object(p, "INPUT_QUIET_TIME", 0.01))
        self.enterContext(patch.object(p, "INTER_REQUEST_DELAY", 0.01))

    async def connect_client(self, *writers, readings=CORE_READINGS):
        connections = iter(writers)

        async def connect(**kwargs):
            writer = next(connections)
            return writer.reader, writer

        self.enterContext(patch.object(p, "READINGS", readings))
        self.enterContext(patch.object(p.serialx, "open_serial_connection", connect))
        client = p.KoyoeClient("test")
        self.addAsyncCleanup(client.close)
        return client

    async def test_decodes_read_only_replies(self):
        writer = Writer(*CORE_REPLIES)
        client = await self.connect_client(writer)
        self.assertEqual(await client.read_all(), {
            "status": 2, "heatsink_temperature": 41.5, "battery_soc": 60.0})
        self.assertEqual([x.hex() for x in writer.frames], [
            "f703758700013ab9", "f703758b0001faba", "f703765f0001bac6"])
        await client.close()
        self.assertTrue(writer.closed)

    async def test_bad_crc_closes_and_next_poll_reconnects(self):
        bad = Writer(bytes.fromhex("f703020002f191"))
        good = Writer(*CORE_REPLIES)
        client = await self.connect_client(bad, good)
        with self.assertRaisesRegex(p.ProtocolError, "CRC"):
            await client.read_all()
        self.assertTrue(bad.closed)
        self.assertEqual((await client.read_all())["battery_soc"], 60.0)
        self.assertEqual(len(good.frames), 3)

    async def test_new_connection_discards_buffered_stale_reply_before_sending(self):
        writer = Writer(*CORE_REPLIES)
        writer.reader.feed_data(CORE_REPLIES[2])
        client = await self.connect_client(writer)
        self.assertEqual((await client.read_all())["status"], 2)
        self.assertEqual(len(writer.frames), 3)

    async def test_busy_connection_is_closed_without_sending(self):
        writer = Writer()
        writer.reader.feed_data(b"x" * p.INITIAL_DRAIN_MAX_BYTES)
        client = await self.connect_client(writer)
        with self.assertRaisesRegex(p.ProtocolError, "did not settle"):
            await client.read_all()
        self.assertEqual(client.phase, "settle_input")
        self.assertTrue(writer.closed)
        self.assertEqual(writer.frames, [])

    async def test_extra_same_width_reply_invalidates_cycle_before_next_request(self):
        writer = Writer(CORE_REPLIES[1] + CORE_REPLIES[0])
        client = await self.connect_client(writer)
        with self.assertRaisesRegex(p.ProtocolError, "no reply was pending"):
            await client.read_all()
        self.assertEqual(client.phase, "receive_idle")
        self.assertEqual(client.last_address, 30087)
        self.assertTrue(writer.closed)
        self.assertEqual(len(writer.frames), 1)

    async def test_unexpected_frame_after_last_reply_invalidates_cycle(self):
        writer = Writer(*CORE_REPLIES[:2], CORE_REPLIES[2] + CORE_REPLIES[0])
        client = await self.connect_client(writer)
        with self.assertRaisesRegex(p.ProtocolError, "no reply was pending"):
            await client.read_all()
        self.assertEqual(client.last_address, 30303)
        self.assertTrue(writer.closed)

    async def test_wrong_byte_count_closes_stream_without_using_reply(self):
        payload = bytes.fromhex("f7030400000002")
        writer = Writer(payload + p.crc(payload).to_bytes(2, "little"))
        client = await self.connect_client(writer)
        with self.assertRaisesRegex(p.ProtocolError, "Invalid byte count 4, expected 2"):
            await client.read_all()
        self.assertEqual(client.phase, "receive_header")
        self.assertTrue(writer.closed)

    async def test_timeout_after_valid_reply_does_not_continue_on_same_stream(self):
        self.enterContext(patch.object(p, "RESPONSE_TIMEOUT", 0.03))
        bad = Writer(CORE_REPLIES[0], None)
        good = Writer(*CORE_REPLIES)
        client = await self.connect_client(bad, good)
        with self.assertRaises(TimeoutError):
            await client.read_all()
        self.assertEqual(client.last_address, 30091)
        self.assertTrue(bad.closed)
        self.assertEqual(len(bad.frames), 2)
        self.assertEqual((await client.read_all())["heatsink_temperature"], 41.5)

    def test_32bit_and_signed_values(self):
        import struct
        for fmt, value in ((">I", 123456), (">i", -1200), (">h", -123)):
            data = struct.pack(fmt, value)
            frame = bytes([247, 3, len(data)]) + data
            frame += p.crc(frame).to_bytes(2, "little")
            self.assertEqual(struct.unpack(fmt, p.parse(frame, len(data)))[0], value)
        self.assertEqual(p.request(30163)[4:6], bytes([0, 2]))

    async def test_optional_exception_does_not_discard_good_readings(self):
        frame = bytes.fromhex("f78302")
        writer = Writer(*CORE_REPLIES, frame + p.crc(frame).to_bytes(2, "little"))
        subset = dict(list(p.READINGS.items())[:4])
        client = await self.connect_client(writer, readings=subset)
        data = await client.read_all()
        self.assertEqual(data["battery_soc"], 60.0)
        self.assertIsNone(data["pv1_voltage"])
        self.assertFalse(writer.closed)

    def test_rejects_other_registers_and_exceptions(self):
        with self.assertRaises(ValueError):
            p.request(40000)
        frame = bytes.fromhex("f78302")
        with self.assertRaises(ValueError):
            p.parse(frame + p.crc(frame).to_bytes(2, "little"))


if __name__ == "__main__":
    unittest.main()
