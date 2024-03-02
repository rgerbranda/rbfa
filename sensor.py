"""Platform for sensor integration."""
from __future__ import annotations

from homeassistant.components.sensor import (
    SensorDeviceClass,
    SensorEntity,
    SensorStateClass,
)
from homeassistant.const import UnitOfTemperature
from homeassistant.core import HomeAssistant
from homeassistant.helpers.entity_platform import AddEntitiesCallback
from homeassistant.helpers.typing import ConfigType, DiscoveryInfoType

from homeassistant.const import Platform

from .const import DOMAIN, CONF_TEAM

from .API import TeamData

import logging

_LOGGER = logging.getLogger(__name__)

def setup_platform(hass, config, async_add_entities, discovery_info=None):


    if discovery_info and "config" in discovery_info:
        conf = discovery_info["config"]
    else:
        conf = config

    if not conf:
        return

    entity = [
        DateSensor(hass.data[DOMAIN][conf[CONF_TEAM]]),
        HomeSensor(hass.data[DOMAIN][conf[CONF_TEAM]]),
        AwaySensor(hass.data[DOMAIN][conf[CONF_TEAM]]),
        LocationSensor(hass.data[DOMAIN][conf[CONF_TEAM]]),
        ]



    async_add_entities(entity)


class DateSensor(SensorEntity):
    """Representation of a Sensor."""

#    _attr_native_unit_of_measurement = UnitOfTemperature.CELSIUS
    _attr_device_class = SensorDeviceClass.TIMESTAMP
#    _attr_state_class = SensorStateClass.MEASUREMENT

    def __init__(
        self,
        TeamData: TeamData,
    ) -> None:

        self._attr_name = "Datum"
        self.TeamData = TeamData

    def update(self) -> None:
        """Fetch new state data for the sensor.

        This is the only method that should fetch new data for Home Assistant.
        """
        item = self.TeamData.upcoming()
        self._attr_native_value = item['date']
        self._attr_extra_state_attributes = {
            'test_attribute': 'test'
        }

class HomeSensor(SensorEntity):
    """Representation of a Sensor."""

#    _attr_native_unit_of_measurement = UnitOfTemperature.CELSIUS
#    _attr_device_class = SensorDeviceClass.TIMESTAMP
#    _attr_state_class = SensorStateClass.MEASUREMENT

    def __init__(
        self,
        TeamData: TeamData,
    ) -> None:

        self._attr_name = "Home team"
        self._attr_unique_id = f"home{CONF_TEAM}"
        self.TeamData = TeamData

    def update(self) -> None:
        """Fetch new state data for the sensor.

        This is the only method that should fetch new data for Home Assistant.
        """
        item = self.TeamData.upcoming()
        self._attr_native_value = item['hometeam']
        self._attr_entity_picture = item['homelogo']
        
class AwaySensor(SensorEntity):
    """Representation of a Sensor."""

#    _attr_native_unit_of_measurement = UnitOfTemperature.CELSIUS
#    _attr_device_class = SensorDeviceClass.TIMESTAMP
#    _attr_state_class = SensorStateClass.MEASUREMENT

    def __init__(
        self,
        TeamData: TeamData,
    ) -> None:

        self._attr_name = "Away team"
        self.TeamData = TeamData

    def update(self) -> None:
        """Fetch new state data for the sensor.

        This is the only method that should fetch new data for Home Assistant.
        """
        item = self.TeamData.upcoming()
        self._attr_native_value = item['awayteam']
        self._attr_entity_picture = item['awaylogo']
        
class LocationSensor(SensorEntity):
    """Representation of a Sensor."""

#    _attr_native_unit_of_measurement = UnitOfTemperature.CELSIUS
#    _attr_device_class = SensorDeviceClass.TIMESTAMP
#    _attr_state_class = SensorStateClass.MEASUREMENT

    def __init__(
        self,
        TeamData: TeamData,
    ) -> None:

        self._attr_name = "Location"
        self.TeamData = TeamData

    def update(self) -> None:
        """Fetch new state data for the sensor.

        This is the only method that should fetch new data for Home Assistant.
        """
        item = self.TeamData.upcoming()
        self._attr_native_value = item['location']
