"""Platform for sensor integration."""
from __future__ import annotations
from collections.abc import Callable
from dataclasses import dataclass

from homeassistant.components.sensor import (
    SensorDeviceClass,
    SensorEntity,
    SensorEntityDescription,
)
from homeassistant.core import HomeAssistant
from homeassistant.helpers.entity_platform import AddEntitiesCallback
#from homeassistant.helpers.typing import ConfigType, DiscoveryInfoType

#from homeassistant.const import Platform
from homeassistant.helpers.update_coordinator import CoordinatorEntity
from .const import DOMAIN, CONF_TEAM

#from .API import TeamData

from .coordinator import MyCoordinator

import logging

_LOGGER = logging.getLogger(__name__)

@dataclass(frozen=True, kw_only=True)
class RbfaSensorEntityDescription(SensorEntityDescription):
    """A class that describes AEMET OpenData sensor entities."""

    keys: list[str] | None = None
    value_fn: Callable[[str], datetime | float | int | str | None] = lambda value: value
    
SENSORS = [
    RbfaSensorEntityDescription(
        key="date",
        translation_key="date",
        device_class = SensorDeviceClass.TIMESTAMP,
    ),
    RbfaSensorEntityDescription(
        key="hometeam",
        translation_key="hometeam",
    ),
    RbfaSensorEntityDescription(
        key="awayteam",
        translation_key="awayteam",
    ),
    RbfaSensorEntityDescription(
        key="location",
        translation_key="location",
        icon="mdi:map-marker",
    ),
    RbfaSensorEntityDescription(
        key="prevposition",
        translation_key="prevposition",
    ),
    RbfaSensorEntityDescription(
        key="prevresulthome",
        translation_key="prevresulthome",
        icon = "mdi:scoreboard"
    ),
]

async def async_setup_entry(
    hass: HomeAssistant,
    entry: ConfigEntry,
    async_add_entities: AddEntitiesCallback,
) -> None:
    """Set up Elgato sensor based on a config entry."""
    coordinator: MyCoordinator = hass.data[DOMAIN][entry.entry_id]

    async_add_entities(
        RbfaSensor(
            coordinator,
            description,
            entry,
        )
        for description in SENSORS
    )

class RbfaEntity(CoordinatorEntity[MyCoordinator]):
    """Defines an Elgato entity."""

    _attr_has_entity_name = True

    def __init__(self, coordinator: MyCoordinator) -> None:
        """Initialize an Elgato entity."""
        super().__init__(coordinator=coordinator)
        
class RbfaSensor(RbfaEntity, SensorEntity):
    """Representation of a Sensor."""

    def __init__(
        self,
        coordinator: MyCoordinator,
        description: RbfaSensorEntityDescription,
        entry,
    ) -> None:
        super().__init__(coordinator)
        self.entity_description = description
        self.TeamData = coordinator.upcoming()

        self.team = entry.data.get('team')
        self._attr_unique_id = f"{DOMAIN}_{description.key}_{self.team}"

        if description.key == 'hometeam':
            self._attr_entity_picture = self.TeamData['homelogo']
        if description.key == 'awayteam':
            self._attr_entity_picture = self.TeamData['awaylogo']

    @property
    def native_value(self):
        return self.TeamData[self.entity_description.key]

    @property
    def extra_state_attributes(self):
        """Return attributes for sensor."""

        basic_attributes = {
            'Team': self.TeamData['teamname'],
            'Date': self.TeamData['date'],
        }

        extra_attributes = {}
        if self.entity_description.key == 'prevposition':
            extra_attributes = {
                'Ranking': self.TeamData['prevranking'],
            }
        return basic_attributes | extra_attributes

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
