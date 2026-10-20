from homeassistant import config_entries
from homeassistant.core import callback
from homeassistant.const import UnitOfTime
from homeassistant.helpers import selector
from homeassistant.config_entries import ConfigFlowResult

from .const import DOMAIN
from .api import RbfaApi, RbfaApiError

import voluptuous as vol
from typing import Any


class RbfaConfigFlow(config_entries.ConfigFlow, domain=DOMAIN):
    """Handle RBFA integration configuration."""

    VERSION = 1
    MINOR_VERSION = 1

    def __init__(self):
        self._team_id = None
        self._team_name = ""

    async def async_step_user(
        self,
        user_input: dict[str, Any] | None = None,
    ) -> ConfigFlowResult:
        """Step 1: enter and validate the team ID."""
        errors = {}

        if user_input is not None:
            team_id = user_input['team'].strip()

            if not team_id:
                errors['team'] = 'invalid_team'
            else:
                await self.async_set_unique_id(team_id)
                self._abort_if_unique_id_configured()

                client = RbfaApi(self.hass, team_id)

                try:
                    result = await client.async_get_config_data()
                except RbfaApiError:
                    errors['base'] = 'cannot_connect'
                else:
                    teamdata = result['team']

                    self._team_id = team_id
                    self._team_name = (
                        f"{teamdata['clubName']} | {teamdata['name']}"
                    )

                    return await self.async_step_settings()

        return self.async_show_form(
            step_id="user",
            data_schema=vol.Schema({
                vol.Required('team'): str,
            }),
            errors=errors,
        )

    async def async_step_settings(
        self,
        user_input: dict[str, Any] | None = None,
    ) -> ConfigFlowResult:
        """Step 2: configure the selected team."""
        if user_input is not None:
            return self.async_create_entry(
                title=self._team_name,
                data={
                    **user_input,
                    'team': self._team_id,
                },
            )

        return self.async_show_form(
            step_id="settings",
            description_placeholders={
                'team_name': self._team_name,
            },
            data_schema=vol.Schema({
                vol.Optional('alt_name'): str,
                vol.Required(
                    'duration', default=105
                ): selector.NumberSelector(
                    selector.NumberSelectorConfig(
                        min=5,
                        max=120,
                        step=5,
                        mode=selector.NumberSelectorMode.BOX,
                        unit_of_measurement=UnitOfTime.MINUTES,
                    ),
                ),
            }),
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
                }
            ),
        )
