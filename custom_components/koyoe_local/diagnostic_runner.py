"""Bounded read-only diagnostic cycles, independent of Home Assistant."""
import asyncio
import logging
from datetime import datetime, timezone
from time import monotonic
from .protocol import READINGS, ProtocolError

LOGGER = logging.getLogger(__name__)
RETRY_DELAY = 3

DIAGNOSTIC_KEYS = {
    "last_success", "successful_polls", "unsupported_registers", "poll_cycles",
    "read_attempts", "failed_attempts", "failed_cycles", "retry_recoveries",
    "consecutive_failed_cycles", "last_error", "last_error_time", "poll_duration",
    "last_error_register", "last_error_phase", "collection_state",
}

class DiagnosticRunner:
    def __init__(self, client):
        self.client = client
        self.counters = dict.fromkeys(("successful_polls", "poll_cycles", "read_attempts",
            "failed_attempts", "failed_cycles", "retry_recoveries", "consecutive_failed_cycles"), 0)
        self.last_success = self.last_error_time = None
        self.last_error = "none"
        self.last_error_register = None
        self.last_error_phase = "none"

    async def poll(self):
        started = monotonic()
        self.counters["poll_cycles"] += 1
        values = None
        for attempt in range(2):
            self.counters["read_attempts"] += 1
            try:
                values = await self.client.read_all()
            except asyncio.CancelledError:
                await self.client.close()
                raise
            except Exception as error:
                self.counters["failed_attempts"] += 1
                self.last_error_time = datetime.now(timezone.utc)
                # Only our own parser errors may provide text. Never expose URLs/keys.
                self.last_error = str(error) if isinstance(error, ProtocolError) else type(error).__name__
                self.last_error_register = self.client.last_address
                self.last_error_phase = self.client.phase
                LOGGER.debug(
                    "Koyoe read attempt %d/2 failed: %s; register %s; phase %s",
                    attempt + 1, self.last_error, self.last_error_register, self.last_error_phase,
                )
                await self.client.close()
                if attempt == 0:
                    # Entire cycle retried once, serialized, with a fresh connection.
                    await asyncio.sleep(RETRY_DELAY)
            else:
                self.counters["successful_polls"] += 1
                self.counters["consecutive_failed_cycles"] = 0
                self.last_success = datetime.now(timezone.utc)
                if attempt:
                    self.counters["retry_recoveries"] += 1
                break
        if values is None:
            self.counters["failed_cycles"] += 1
            self.counters["consecutive_failed_cycles"] += 1
        result = {key: None for key in READINGS}
        if values is not None:
            result.update(values)
        result.update(self.counters)
        result.update(last_success=self.last_success, last_error=self.last_error,
            last_error_time=self.last_error_time, last_error_register=self.last_error_register,
            last_error_phase=self.last_error_phase,
            poll_duration=round(monotonic() - started, 3),
            unsupported_registers=sum(value is None for value in values.values()) if values is not None else None,
            collection_state="failed" if values is None else "recovered" if attempt else "ok")
        return result
