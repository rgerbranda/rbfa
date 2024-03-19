from homeassistant import config_entries
from homeassistant.core import callback
from homeassistant.const import UnitOfTime
from homeassistant.helpers import selector
from homeassistant.data_entry_flow import FlowResult

from .const import DOMAIN

import logging
import voluptuous as vol
from typing import Any

_LOGGER = logging.getLogger(__name__)

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

    @staticmethod
    @callback
    def async_get_options_flow(
        config_entry: config_entries.ConfigEntry,
    ) -> config_entries.OptionsFlow:
        """Create the options flow."""
        return OptionsFlowHandler(config_entry)

class OptionsFlowHandler(config_entries.OptionsFlow):
    def __init__(self, config_entry: config_entries.ConfigEntry) -> None:
        """Initialize options flow."""
        self.config_entry = config_entry
        _LOGGER.debug('data? %r', config_entry.data['duration'])

    async def async_step_init(
        self, user_input: dict[str, Any] | None = None
    ) -> FlowResult:
        """Manage the options."""
        if user_input is not None:
            return self.async_create_entry(title="test", data=user_input)

        if 'duration' in self.config_entry.options:
            duration = self.config_entry.options['duration']
        else:
            duration = self.config_entry.data['duration']

        return self.async_show_form(
            step_id="init",
            data_schema=vol.Schema(
                {
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
                }
            ),
        )
