from homeassistant import config_entries
from homeassistant.const import UnitOfTime
from .const import DOMAIN
import voluptuous as vol

from homeassistant.helpers import selector

class RbfaConfigFlow(config_entries.ConfigFlow, domain=DOMAIN):
    """Example config flow."""
    # The schema version of the entries that it creates
    # Home Assistant will call your migrate method if the version changes
    VERSION = 1
    MINOR_VERSION = 1


    async def async_step_user(self, user_input):

        if user_input is not None:
            team = user_input.get('team')
            duration = user_input.get('duration')

            await self.async_set_unique_id(f"{team}")
            self._abort_if_unique_id_configured()

            return self.async_create_entry(title=f"{team}", data=user_input)

        schema = vol.Schema(
            {
                vol.Required('team'): str,
                vol.Required('duration', default=105
                ): selector.NumberSelector(
                    selector.NumberSelectorConfig(
                        min=5,
                        max=120,
                        step=5,
                        mode=selector.NumberSelectorMode.BOX,
                        unit_of_measurement=UnitOfTime.MINUTES,
                    ),
                ),
            }
        )


        return self.async_show_form(
            step_id="user",
            data_schema=schema,
            errors={},
        )
