"""

Example config:
Configuration.yaml:
rbra:
    team: 123456
"""

import logging
#from datetime import datetime
from datetime import timedelta

from homeassistant.const import Platform

from homeassistant.core import HomeAssistant
from homeassistant.helpers.typing import ConfigType
from homeassistant.components import persistent_notification

from .const import DOMAIN, PLATFORM_SCHEMA, CONF_TEAM
from .API import get_rbfa_data_from_config


__version__ = "0.1"


_LOGGER = logging.getLogger(__name__)


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

            data = get_rbfa_data_from_config(hass, conf)
            hass.data.setdefault(DOMAIN, {})[conf[CONF_TEAM]] = data

            hass.helpers.discovery.load_platform(
                Platform.CALENDAR, DOMAIN, {"config": conf}, conf
            )

            hass.helpers.discovery.load_platform(
                Platform.SENSOR, DOMAIN, {"config": conf}, conf
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
