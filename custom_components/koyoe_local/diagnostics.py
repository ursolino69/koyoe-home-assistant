"""Sanitized HA diagnostic export, without port URI or credentials."""
from datetime import datetime

from homeassistant.loader import async_get_integration

from . import DOMAIN

async def async_get_config_entry_diagnostics(hass, entry):
    coordinator = entry.runtime_data
    integration = await async_get_integration(hass, DOMAIN)
    return {
        "integration_version": str(integration.version),
        "transport": "serialx",
        "unit_id": 247,
        "baud_rate": 9600,
        "data": {key: value.isoformat() if isinstance(value, datetime) else value
                 for key, value in (coordinator.data or {}).items()},
    }
