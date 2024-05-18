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
        self.team = entry.data.get('team')
        self._attr_unique_id = f"{DOMAIN}_{collection}_{description.key}_{self.team}"

    @property
    def native_value(self):
        data = self.coordinator.data[self.collection]
        if data != None:
            return data[self.entity_description.key]

    @property
    def entity_picture(self):
        col = self.collection
        data = self.coordinator.data[col]

        if data != None:
            key = self.entity_description.key

            if key in ['hometeam', 'awayteam']:
                entity_picture = data[key + 'logo']
                return entity_picture
    
            if key == 'series':
                logo = data['channel'].upper()
                entity_picture = f"https://www.rbfa.be/assets/img/icons/organisers/Logo{logo}.svg"
                return entity_picture

    @property
    def extra_state_attributes(self):
        """Return attributes for sensor."""

        col = self.collection
        data = self.coordinator.data[col]
        attributes = {
            'baseid': self.team,
            'tag': col,
        }

        if data != None:
            key = self.entity_description.key

            if key in ['hometeam', 'awayteam']:
                results = ['id', 'goals', 'penalties', 'position']

                for t in results:
                    result = data[key + t]
                    if result != None:
                        attributes[t] = result

            if key == 'series' and data['ranking']:
                attributes['ranking'] = data['ranking']

        return attributes
