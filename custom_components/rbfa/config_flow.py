from homeassistant import config_entries
from .const import DOMAIN
import voluptuous as vol


class RbfaConfigFlow(config_entries.ConfigFlow, domain=DOMAIN):
    """Example config flow."""
    # The schema version of the entries that it creates
    # Home Assistant will call your migrate method if the version changes
    VERSION = 1
    MINOR_VERSION = 1


    async def async_step_user(self, user_input):

        if user_input is not None:
            team = user_input.get('team')

            await self.async_set_unique_id(f"{team}")
            self._abort_if_unique_id_configured()

            return self.async_create_entry(title=f"{team}", data=user_input)



        return self.async_show_form(
            step_id="user",
            data_schema=vol.Schema({vol.Required('team'): str}),
        )
