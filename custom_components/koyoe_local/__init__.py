"""Read Koyoe inverter telemetry locally."""
from datetime import timedelta
import logging

from homeassistant.const import Platform, EVENT_HOMEASSISTANT_STOP
from homeassistant.helpers.update_coordinator import DataUpdateCoordinator

from .protocol import KoyoeClient
from .diagnostic_runner import DiagnosticRunner

DOMAIN = "koyoe_local"
LOGGER = logging.getLogger(__name__)


class KoyoeCoordinator(DataUpdateCoordinator):
    def __init__(self, hass, entry):
        super().__init__(hass, LOGGER, name="Koyoe Local", config_entry=entry,
                         update_interval=timedelta(seconds=30))
        self.client = KoyoeClient(entry.data["device"])
        self.runner = DiagnosticRunner(self.client)

    async def _async_update_data(self):
        data = await self.runner.poll()
        if data["consecutive_failed_cycles"] == 1:
            LOGGER.warning("Koyoe cycle failed after two attempts: %s; register %s; phase %s",
                data["last_error"], data["last_error_register"], data["last_error_phase"])
        elif data["collection_state"] == "recovered":
            LOGGER.info("Koyoe cycle recovered on fresh-connection retry")
        elif data["collection_state"] == "ok" and self.data and self.data["collection_state"] == "failed":
            LOGGER.info("Koyoe communication restored")
        return data


async def async_setup_entry(hass, entry):
    coordinator = KoyoeCoordinator(hass, entry)
    try:
        await coordinator.async_config_entry_first_refresh()
    except BaseException:
        await coordinator.client.close()
        raise
    entry.runtime_data = coordinator
    async def close_on_stop(event):
        await coordinator.client.close()
    entry.async_on_unload(hass.bus.async_listen_once(EVENT_HOMEASSISTANT_STOP, close_on_stop))
    try:
        await hass.config_entries.async_forward_entry_setups(entry, [Platform.SENSOR])
    except BaseException:
        await coordinator.client.close()
        raise
    return True


async def async_unload_entry(hass, entry):
    unloaded = await hass.config_entries.async_unload_platforms(entry, [Platform.SENSOR])
    if unloaded:
        await entry.runtime_data.client.close()
    return unloaded
