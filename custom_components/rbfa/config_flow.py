from homeassistant import config_entries
from homeassistant.core import callback
from homeassistant.const import UnitOfTime
from homeassistant.helpers import selector
from homeassistant.config_entries import ConfigFlowResult

from .const import DOMAIN

import voluptuous as vol
from typing import Any

class RbfaConfigFlow(config_entries.ConfigFlow, domain=DOMAIN):
    """Handle RBFA integration configuration."""
    # The schema version of the entries that it creates
    # Home Assistant will call your migrate method if the version changes
    VERSION = 1
    MINOR_VERSION = 1

    async def async_step_user(
        self,
        user_input: dict[str, Any] | None = None
    ) -> ConfigFlowResult:

        if user_input is not None:
            team = user_input['team']
        
            await self.async_set_unique_id(str(team))
            self._abort_if_unique_id_configured()
        
            return self.async_create_entry(
                title=str(team),
                data=user_input
            )

        schema = vol.Schema(
            {
                vol.Required('team'): str,
                vol.Optional('alt_name'): str,
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
                vol.Required('show_ranking', default=True): bool,
                vol.Required('show_referee', default=True): bool,
            }
        )


        return self.async_show_form(
            step_id="user",
            data_schema=schema,
            errors={},
        )

    @staticmethod
    @callback
    def async_get_options_flow(
        config_entry: config_entries.ConfigEntry,
    ) -> config_entries.OptionsFlow:
        return OptionsFlowHandler()

class OptionsFlowHandler(config_entries.OptionsFlow):
    async def async_step_init(
        self, user_input: dict[str, Any] | None = None
    ) -> ConfigFlowResult:
        """Manage the options."""
        if user_input is not None:
            return self.async_create_entry(title="", data=user_input)

        options = self.config_entry.options
        data = self.config_entry.data
        
        alt_name = options.get('alt_name', data.get('alt_name', ''))
        duration = options.get('duration', data.get('duration', 105))
        show_ranking = options.get('show_ranking', data.get('show_ranking', True))
        show_referee = options.get('show_referee', data.get('show_referee', True))

        return self.async_show_form(
            step_id="init",
            data_schema=vol.Schema(
                {
                    vol.Optional('alt_name', description={"suggested_value": alt_name}): str,
                    vol.Required('duration', default=duration
                    ): selector.NumberSelector(
                        selector.NumberSelectorConfig(
                            min=5,
                            max=120,
                            step=5,
                            mode=selector.NumberSelectorMode.BOX,
                            unit_of_measurement=UnitOfTime.MINUTES,
                        ),
                    ),
                    vol.Required('show_ranking', default=show_ranking): bool,
                    vol.Required('show_referee', default=show_referee): bool,
                }
            ),
        )
