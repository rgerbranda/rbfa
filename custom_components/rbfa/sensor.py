"""Platform for sensor integration."""
from __future__ import annotations

from homeassistant.components.sensor import (
    SensorDeviceClass,
    SensorEntity,
    SensorEntityDescription,
)
from homeassistant.core import HomeAssistant
from homeassistant.helpers.entity_platform import AddEntitiesCallback

from .const import DOMAIN
from .coordinator import MyCoordinator
from .entity import RbfaEntity

import logging

_LOGGER = logging.getLogger(__name__)

SENSORS = (
    SensorEntityDescription(
        key="starttime",
        translation_key="starttime",
        device_class = SensorDeviceClass.TIMESTAMP,
    ),
    SensorEntityDescription(
        key="endtime",
        translation_key="endtime",
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
        icon="mdi:soccer-field",
    ),
    SensorEntityDescription(
        key="series",
        translation_key="series",
        icon="mdi:table-row",
    ),
    SensorEntityDescription(
        key="referee",
        translation_key="referee",
        icon="mdi:whistle",
    ),
    SensorEntityDescription(
        key="matchid",
        translation_key="matchid",
        icon="mdi:soccer",
    ),
)

async def async_setup_entry(
    hass: HomeAssistant,
    entry: ConfigEntry,
    async_add_entities: AddEntitiesCallback,
) -> None:
    """Set up RBFA sensor based on a config entry."""
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

            if description.key == 'series':
                self._attr_entity_picture = f"https://www.rbfa.be/assets/img/icons/organisers/Logo{self.TeamData['channel'].upper()}.svg"

    @property
    def native_value(self):
        if self.TeamData != None:
            return self.TeamData[self.entity_description.key]

    @property
    def extra_state_attributes(self):
        """Return attributes for sensor."""

        if self.TeamData != None:
            basic_attributes = {
                'baseid': self.team,
                'tag': self.collection,
            }

            if self.entity_description.key == 'position':
                self.extra_attributes = {
                    'ranking': self.TeamData['ranking'],
                }
            return basic_attributes | self.extra_attributes
