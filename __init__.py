"""

Example config:
Configuration.yaml:
rbra:
    team: 123456
"""

import logging
from datetime import datetime
from datetime import timedelta

from homeassistant.const import Platform

from homeassistant.core import HomeAssistant
from homeassistant.helpers.typing import ConfigType
from homeassistant.components import persistent_notification

from .const import DOMAIN, PLATFORM_SCHEMA, CONF_TEAM
from .API import get_wastedata_from_config


__version__ = "0.1"


_LOGGER = logging.getLogger(__name__)


async def async_setup(hass: HomeAssistant, config: ConfigType):
    _LOGGER.debug("Setup of Afvalbeheer component Rest API retriever")

    config = config.get(DOMAIN, None)
    if config is None:
        _LOGGER.debug("config not found")
        return True

    if not isinstance(config, list):
        config = [config]

    for conf in config:
        _LOGGER.debug(conf)

        if conf[CONF_TEAM] != "":

            data = get_wastedata_from_config(hass, conf)
            hass.data.setdefault(DOMAIN, {})[conf[CONF_TEAM]] = data

            hass.helpers.discovery.load_platform(
                Platform.CALENDAR, DOMAIN, {"config": conf}, conf
            )

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
