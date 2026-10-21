"""Platform for sensor integration."""
from __future__ import annotations

from homeassistant.components.sensor import (
    SensorDeviceClass,
    SensorEntity,
    SensorEntityDescription,
)
from homeassistant.core import HomeAssistant
from homeassistant.helpers.entity_platform import AddEntitiesCallback
from homeassistant.config_entries import ConfigEntry

from .const import DOMAIN
from .coordinator import RbfaCoordinator
from .entity import RbfaEntity, get_team_name

import logging

_LOGGER = logging.getLogger(__name__)

SENSORS = (
    SensorEntityDescription(
        key="starttime",
        translation_key="starttime",
        device_class=SensorDeviceClass.TIMESTAMP,
    ),
    SensorEntityDescription(
        key="endtime",
        translation_key="endtime",
        device_class=SensorDeviceClass.TIMESTAMP,
    ),
    SensorEntityDescription(
        key="hometeam",
        translation_key="hometeam",
        icon="mdi:account-group",
    ),
    SensorEntityDescription(
        key="awayteam",
        translation_key="awayteam",
        icon="mdi:account-group",
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
    coordinator: RbfaCoordinator = hass.data[DOMAIN][entry.entry_id]

    all_sensors = []

    for description in SENSORS:
        for collection in ('upcoming', 'lastmatch'):
            all_sensors.append(
                RbfaSensor(
                    coordinator,
                    description,
                    entry,
                    collection=collection,
                )
            )

    async_add_entities(all_sensors)


class RbfaSensor(RbfaEntity, SensorEntity):
    """Representation of a Sensor."""

    def __init__(
        self,
        coordinator: RbfaCoordinator,
        description: SensorEntityDescription,
        entry,
        collection,
    ) -> None:
        super().__init__(coordinator)
        self.entity_description = description
        self.collection = collection
        self._team_name = get_team_name(coordinator)
        self._attr_translation_key = (
            f"{collection}_{description.key}"
        )
        self.team = entry.data.get('team')
        self._attr_unique_id = f"{DOMAIN}_{collection}_{description.key}_{self.team}"

    @property
    def native_value(self):
        data = self.coordinator.data['matchdata'][self.collection]
        if data is not None:
            return data[self.entity_description.key]

    @property
    def entity_picture(self):
        col = self.collection
        data = self.coordinator.data['matchdata'][col]

        if data is not None:
            key = self.entity_description.key

            if key in ['hometeam', 'awayteam']:
                entity_picture = data[key + 'logo']
                return entity_picture

            if key == 'series':
                logo = data['channel'].upper()
                entity_picture = f"https://www.rbfa.be/assets/img/icons/organisers/Logo{logo}.svg"
                return entity_picture

    @property
    def attribution(self):
        """Return attribution for geocoded locations."""
        if self.entity_description.key == 'location':
            data = self.coordinator.data['matchdata'][self.collection]

            if data is not None:
                return data.get('location_attribution')

        return super().attribution

    @property
    def extra_state_attributes(self):
        """Return attributes for sensor."""

        col = self.collection
        data = self.coordinator.data['matchdata'][col]

        attributes = {
            'baseid': self.team,
            'tag': col,
            'team': self._team_name,
        }
        if data is not None:
            key = self.entity_description.key

            if key == 'location':
                latitude = data.get('latitude')
                longitude = data.get('longitude')

                if latitude is not None and longitude is not None:
                    attributes['latitude'] = latitude
                    attributes['longitude'] = longitude

            if key in ['hometeam', 'awayteam']:
                results = ['id', 'goals', 'penalties', 'position']

                for t in results:
                    result = data.get(key + t)
                    if result is not None:
                        attributes[t] = result

            if key == 'series' and data.get('ranking'):
                attributes['ranking'] = data['ranking']

        return attributes
