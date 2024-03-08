"""Platform for sensor integration."""
from __future__ import annotations

from homeassistant.components.sensor import (
    SensorDeviceClass,
    SensorEntity,
)
from homeassistant.core import HomeAssistant
from homeassistant.helpers.entity_platform import AddEntitiesCallback
#from homeassistant.helpers.typing import ConfigType, DiscoveryInfoType

from homeassistant.const import Platform

from .const import DOMAIN, CONF_TEAM

#from .API import TeamData

import logging

_LOGGER = logging.getLogger(__name__)

def setup_platform(hass, config, async_add_entities, discovery_info=None):

    if discovery_info and "config" in discovery_info:
        conf = discovery_info["config"]
    else:
        conf = config

    if not conf:
        return

    entities = [
        DateSensor(hass.data[DOMAIN][conf[CONF_TEAM]], conf),
        HomeSensor(hass.data[DOMAIN][conf[CONF_TEAM]], conf),
        AwaySensor(hass.data[DOMAIN][conf[CONF_TEAM]], conf),
        LocationSensor(hass.data[DOMAIN][conf[CONF_TEAM]], conf),
        LastDateSensor(hass.data[DOMAIN][conf[CONF_TEAM]], conf),
        ResultSensor(hass.data[DOMAIN][conf[CONF_TEAM]], conf),
    ]

    async_add_entities(entities)


class DateSensor(SensorEntity):
    """Representation of a Sensor."""
    _attr_device_class = SensorDeviceClass.TIMESTAMP

    def __init__(
        self,
        TeamData,
        config,
    ) -> None:

        self._attr_name      = f"{config[CONF_TEAM]} | Next match"
        self._attr_unique_id = f"{DOMAIN}_datetime_{config[CONF_TEAM]}"
        self.TeamData = TeamData
        self.config = config

    def update(self) -> None:
        """Fetch new state data for the sensor."""
        item = self.TeamData.upcoming()
        teamdata = self.TeamData.teamdata()
        self._attr_name = self._attr_name.replace(self.config[CONF_TEAM], teamdata['name'])
        self._attr_native_value = item['date']
        self._attr_extra_state_attributes = {
            'Series': item['series'],
            'MatchID' : item['uid'],
        }

class HomeSensor(SensorEntity):
    """Representation of a Sensor."""
    def __init__(
        self,
        TeamData,
        config,
    ) -> None:

        self._attr_unique_id = f"{DOMAIN}_home_team_{config[CONF_TEAM]}"
        self.TeamData = TeamData

    _attr_has_entity_name = True

    @property
    def translation_key(self):
        return "home_team"

    def update(self) -> None:
        """Fetch new state data for the sensor."""
        teamdata = self.TeamData.teamdata()
        item = self.TeamData.upcoming()

        self._attr_native_value = item['hometeam']
        self._attr_entity_picture = item['homelogo']
        self._attr_extra_state_attributes = {
            'Team': teamdata['name'],
            'Series': item['series'],
            'MatchID': item['uid'],
            'Date': item['date'],
        }


class AwaySensor(SensorEntity):
    """Representation of a Sensor."""
    def __init__(
        self,
        TeamData,
        config,
    ) -> None:

        self._attr_unique_id = f"{DOMAIN}_away_team_{config[CONF_TEAM]}"
        self.TeamData = TeamData

    _attr_has_entity_name = True

    @property
    def translation_key(self):
        return "away_team"

    def update(self) -> None:
        """Fetch new state data for the sensor."""
        teamdata = self.TeamData.teamdata()
        item = self.TeamData.upcoming()

        self._attr_native_value = item['awayteam']
        self._attr_entity_picture = item['awaylogo']
        self._attr_extra_state_attributes = {
            'Team': teamdata['name'],
            'Series': item['series'],
            'MatchID' : item['uid'],
            'Date': item['date'],
        }

class LocationSensor(SensorEntity):
    """Representation of a Sensor."""
    _attr_icon = "mdi:soccer"

    def __init__(
        self,
        TeamData,
        config,
    ) -> None:

        self._attr_unique_id = f"{DOMAIN}_location_{config[CONF_TEAM]}"
        self.TeamData = TeamData

    _attr_has_entity_name = True

    @property
    def translation_key(self):
        return "location"

    def update(self) -> None:
        """Fetch new state data for the sensor."""
        teamdata = self.TeamData.teamdata()

        item = self.TeamData.upcoming()
        self._attr_native_value = item['location']
        self._attr_extra_state_attributes = {
            'Team': teamdata['name'],
            'Series': item['series'],
            'MatchID' : item['uid'],
            'Date': item['date'],
        }


class LastDateSensor(SensorEntity):
    """Representation of a Sensor."""
    _attr_device_class = SensorDeviceClass.TIMESTAMP

    def __init__(
        self,
        TeamData,
        config,
    ) -> None:

        self._attr_name      = f"Previous {config[CONF_TEAM]}"
        self._attr_unique_id = f"{DOMAIN}_previous_datetime_{config[CONF_TEAM]}"
        self.TeamData = TeamData

    def update(self) -> None:
        """Fetch new state data for the sensor."""
        item = self.TeamData.lastmatch()
        self._attr_name = f"{item['hometeam']} - {item['awayteam']}"
        self._attr_native_value = item['date']
        self._attr_extra_state_attributes = {
            'Series': item['series'],
            'MatchID' : item['uid'],
        }

class ResultSensor(SensorEntity):
    """Representation of a Sensor."""
    _attr_icon = "mdi:scoreboard"

    def __init__(
        self,
        TeamData,
        config,
    ) -> None:

        self._attr_name      = f"Result {config[CONF_TEAM]}"
        self._attr_unique_id = f"{DOMAIN}_result_{config[CONF_TEAM]}"
        self.TeamData = TeamData

    def update(self) -> None:
        """Fetch new state data for the sensor."""
        item = self.TeamData.lastmatch()
        self._attr_name = f"{item['hometeam']} - {item['awayteam']}"
        self._attr_native_value = item['result']
        self._attr_extra_state_attributes = {
            'Series': item['series'],
            'MatchID' : item['uid'],
            'Ranking': item['ranking'],
            'TeamID': item['team'],
        }
