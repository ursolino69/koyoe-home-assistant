"""Select the existing HA serial proxy; reuse its stored credentials."""
import probatio

from homeassistant.config_entries import ConfigFlow
from homeassistant.helpers.selector import SerialPortSelector

from . import DOMAIN
from .protocol import KoyoeClient


class KoyoeConfigFlow(ConfigFlow, domain=DOMAIN):
    VERSION = 1

    async def async_step_user(self, user_input=None):
        errors = {}
        if user_input is not None:
            device = user_input["device"]
            self._async_abort_entries_match({"device": device})
            client = KoyoeClient(device)
            try:
                await client.read_all()
            except Exception:
                errors["base"] = "cannot_connect"
            else:
                return self.async_create_entry(title="Koyoe KY-EST20KH", data={"device": device})
            finally:
                await client.close()
        return self.async_show_form(
            step_id="user",
            data_schema=probatio.Schema({probatio.Required("device"): SerialPortSelector()}),
            errors=errors,
        )
