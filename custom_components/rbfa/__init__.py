"""

Example config:
Configuration.yaml:
rbra:
    team: 123456
"""
#from __future__ import annotations

import logging
#from datetime import datetime
from datetime import timedelta
from homeassistant.config_entries import ConfigEntry
from homeassistant.const import Platform

from homeassistant.core import HomeAssistant
from homeassistant.helpers.typing import ConfigType
from homeassistant.components import persistent_notification

from .const import DOMAIN, PLATFORM_SCHEMA, CONF_TEAM, CONF_UPDATE_INTERVAL
from .API import TeamApp

from .coordinator import MyCoordinator

from homeassistant.config_entries import ConfigEntry

__version__ = "0.1"


_LOGGER = logging.getLogger(__name__)

PLATFORMS = [Platform.CALENDAR, Platform.SENSOR]

'''
async def async_setup(hass: HomeAssistant, config: ConfigType):
    _LOGGER.debug("Setup of RBFA component Rest API retriever")

    config = config.get(DOMAIN, None)
    if config is None:
        _LOGGER.debug("config not found")
        return True

    if not isinstance(config, list):
        config = [config]

    for conf in config:
        _LOGGER.debug('configuration: %r', conf)

        if conf[CONF_TEAM] != "":

            team = conf.get(CONF_TEAM)
            update_interval = conf.get(CONF_UPDATE_INTERVAL)

            data = TeamData(hass, team, update_interval)
            hass.data.setdefault(DOMAIN, {})[team] = data

            hass.helpers.discovery.load_platform(
                Platform.CALENDAR, DOMAIN, {"config": conf}, conf
            )

#            hass.helpers.discovery.load_platform(
#                Platform.SENSOR, DOMAIN, {"config": conf}, conf
#            )

            _LOGGER.debug("data schedule update")
            await data.schedule_update(timedelta())
        else:
            persistent_notification.create(
                hass,
                "Config invalid! Team id is required",
                "RBFA",
                DOMAIN + "_invalid_config",
            )

    return True
'''

async def async_setup_entry(hass, entry) -> bool:
    """Set up Elgato Light from a config entry."""
    coordinator = MyCoordinator(hass, entry)
    _LOGGER.debug('first refresh')
    await coordinator.async_config_entry_first_refresh()

    hass.data.setdefault(DOMAIN, {})[entry.entry_id] = coordinator
    await hass.config_entries.async_forward_entry_setups(entry, PLATFORMS)

    return True

#async def async_update_options(hass: HomeAssistant, config_entry: ConfigEntry) -> None:
#    """Update options."""
#    await hass.config_entries.async_reload(config_entry.entry_id)

