import asyncio
import importlib.util
from pathlib import Path
import sys
import types
import unittest
from unittest.mock import AsyncMock, patch

root = Path(__file__).parent / 'custom_components/koyoe_local'
pkg = types.ModuleType('diagnostic_test_package')
pkg.__path__ = [str(root)]
sys.modules[pkg.__name__] = pkg
for name in ('protocol', 'diagnostic_runner'):
    spec = importlib.util.spec_from_file_location(f'{pkg.__name__}.{name}', root / f'{name}.py')
    module = importlib.util.module_from_spec(spec)
    sys.modules[spec.name] = module
    spec.loader.exec_module(module)
r = sys.modules[f'{pkg.__name__}.diagnostic_runner']

class Client:
    last_address = 30087
    phase = 'receive_header'
    def __init__(self, outcomes):
        self.read_all = AsyncMock(side_effect=outcomes)
        self.close = AsyncMock()

class DiagnosticTests(unittest.IsolatedAsyncioTestCase):
    async def test_success_then_two_failures_clears_measurements_keeps_diagnostics(self):
        client = Client([{'status': 2}, TimeoutError(), OSError('secret URL')])
        runner = r.DiagnosticRunner(client)
        with patch.object(r.asyncio, 'sleep', AsyncMock()):
            first = await runner.poll()
            failed = await runner.poll()
        self.assertEqual(first['status'], 2)
        self.assertIsNone(failed['status'])
        self.assertEqual(failed['last_success'], first['last_success'])
        self.assertEqual(failed['failed_attempts'], 2)
        self.assertEqual(failed['failed_cycles'], 1)
        self.assertEqual(failed['read_attempts'], 3)
        self.assertEqual(failed['last_error'], 'OSError')
        self.assertEqual(failed['last_error_register'], 30087)
        self.assertEqual(client.close.await_count, 2)

    async def test_exactly_one_retry_and_recovery(self):
        client = Client([TimeoutError(), {'status': 2}])
        with patch.object(r.asyncio, 'sleep', AsyncMock()) as sleep:
            data = await r.DiagnosticRunner(client).poll()
        sleep.assert_awaited_once_with(3)
        self.assertEqual(client.read_all.await_count, 2)
        self.assertEqual(client.close.await_count, 1)
        self.assertEqual(data['retry_recoveries'], 1)
        self.assertEqual(data['failed_cycles'], 0)
        self.assertEqual(data['collection_state'], 'recovered')

    async def test_cancellation_not_retried(self):
        client = Client([asyncio.CancelledError()])
        with self.assertRaises(asyncio.CancelledError):
            await r.DiagnosticRunner(client).poll()
        self.assertEqual(client.read_all.await_count, 1)
        client.close.assert_awaited_once()

    async def test_failure_on_first_cycle_still_has_diagnostics(self):
        client = Client([TimeoutError(), TimeoutError()])
        with patch.object(r.asyncio, 'sleep', AsyncMock()):
            data = await r.DiagnosticRunner(client).poll()
        self.assertIsNone(data['last_success'])
        self.assertEqual(data['poll_cycles'], 1)
        self.assertEqual(data['consecutive_failed_cycles'], 1)
        self.assertEqual(data['collection_state'], 'failed')

if __name__ == '__main__':
    unittest.main()
