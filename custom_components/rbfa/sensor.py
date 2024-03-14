"""Platform for sensor integration."""
from __future__ import annotations
#from collections.abc import Callable
#from dataclasses import dataclass

from homeassistant.components.sensor import (
    SensorDeviceClass,
    SensorEntity,
    SensorEntityDescription,
)
from homeassistant.core import HomeAssistant
from homeassistant.helpers.entity_platform import AddEntitiesCallback
#from homeassistant.helpers.typing import ConfigType, DiscoveryInfoType

#from homeassistant.const import Platform
from .const import DOMAIN, CONF_TEAM

#from .API import TeamData

from .coordinator import MyCoordinator
from .entity import RbfaEntity

import logging

_LOGGER = logging.getLogger(__name__)

# @dataclass(frozen=True, kw_only=True)
# class RbfaSensorEntityDescription(SensorEntityDescription):
#     """A class that describes AEMET OpenData sensor entities."""
#
#     keys: list[str] | None = None
#     value_fn: Callable[[str], datetime | float | int | str | None] = lambda value: value

SENSORS = (
    SensorEntityDescription(
        key="date",
        translation_key="date",
        device_class = SensorDeviceClass.TIMESTAMP,
    ),
    SensorEntityDescription(
        key="hometeam",
        translation_key="hometeam",
    ),
    SensorEntityDescription(
        key="awayteam",
        translation_key="awayteam",
    ),
    SensorEntityDescription(
        key="location",
        translation_key="location",
        icon="mdi:map-marker",
    ),
    SensorEntityDescription(
        key="series",
        translation_key="series",
    ),
    SensorEntityDescription(
        key="referee",
        translation_key="referee",
        icon="mdi:whistle",
    ),
    SensorEntityDescription(
        key="matchid",
        translation_key="matchid",
    ),
#     SensorEntityDescription(
#         key="position",
#         translation_key="position",
#     ),
#     RbfaSensorEntityDescription(
#         key="hometeamgoals",
#         translation_key="hometeamgoals",
#         icon = "mdi:scoreboard"
#     ),
#     RbfaSensorEntityDescription(
#         key="awayteamgoals",
#         translation_key="awayteamgoals",
#         icon = "mdi:scoreboard"
#     ),
)

async def async_setup_entry(
    hass: HomeAssistant,
    entry: ConfigEntry,
    async_add_entities: AddEntitiesCallback,
) -> None:
    """Set up Elgato sensor based on a config entry."""
    coordinator: MyCoordinator = hass.data[DOMAIN][entry.entry_id]

    all_sensors = []
    for description in SENSORS:
        all_sensors.append(
            RbfaSensor(
                coordinator,
                description,
                entry,
                collection='upcoming',
            )
        )
        all_sensors.append(
            RbfaSensor(
                coordinator,
                description,
                entry,
                collection='lastmatch',
            )
        )
    async_add_entities(
        all_sensors
    )

class RbfaSensor(RbfaEntity, SensorEntity):
    """Representation of a Sensor."""

    def __init__(
        self,
        coordinator: MyCoordinator,
        description: RbfaSensorEntityDescription,
        entry,
        collection,
    ) -> None:
        super().__init__(coordinator)
        self.entity_description = description
        self.collection = collection
        self.extra_attributes = {}

        self.TeamData = coordinator.matchdata().get(collection)

        self.team = entry.data.get('team')
        self._attr_unique_id = f"{DOMAIN}_{collection}_{description.key}_{self.team}"

        if self.TeamData != None:
            self.extra_attributes = {}

            if description.key == 'hometeam' or description.key == 'awayteam':
                self._attr_entity_picture = self.TeamData[description.key + 'logo']
                results = ['id', 'goals', 'penalties', 'position']

                for t in results:
                    if self.TeamData[description.key + t] != None:
                        self.extra_attributes[t] = self.TeamData[description.key + t]

            if description.key == 'series' and len(self.TeamData['ranking']) > 0:
                self.extra_attributes ['ranking'] = self.TeamData['ranking']

    @property
    def native_value(self):
        if self.TeamData != None:
            return self.TeamData[self.entity_description.key]

    @property
    def extra_state_attributes(self):
        """Return attributes for sensor."""

        if self.TeamData != None:
            basic_attributes = {
                'team': self.TeamData['teamname'],
                'baseid': self.team,
                'date': self.TeamData['date'],
                'tag': self.collection,
            }

            if self.entity_description.key == 'position':
                self.extra_attributes = {
                    'ranking': self.TeamData['ranking'],
                }
            return basic_attributes | self.extra_attributes
