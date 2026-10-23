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
from .coordinator import RbfaCoordinator, RbfaRankingCoordinator
from .entity import RbfaEntity, get_team_name

MATCH_STATES = (
    "planned",
    "finished",
    "postponed",
    "forfeitbyoneteam",
    "generalforfeit",
)

SENSORS = (
    SensorEntityDescription(
        key="starttime",
        device_class=SensorDeviceClass.TIMESTAMP,
    ),
    SensorEntityDescription(
        key="hometeam",
        icon="mdi:account-group",
    ),
    SensorEntityDescription(
        key="awayteam",
        icon="mdi:account-group",
    ),
    SensorEntityDescription(
        key="location",
        icon="mdi:soccer-field",
    ),
    SensorEntityDescription(
        key="series",
        icon="mdi:table-row",
    ),
    SensorEntityDescription(
        key="state",
        device_class=SensorDeviceClass.ENUM,
        options=list(MATCH_STATES),
    ),
    SensorEntityDescription(
        key="referee",
        icon="mdi:whistle",
    ),
    SensorEntityDescription(
        key="matchid",
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

    ranking_coordinator = hass.data[
        f"{DOMAIN}_rankings"
    ][entry.entry_id]

    all_sensors.append(
        RbfaRankingSensor(ranking_coordinator, entry)
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
            'field': self.entity_description.key,
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
                results = ['id', 'goals', 'penalties']

                for t in results:
                    result = data.get(key + t)
                    if result is not None:
                        attributes[t] = result

            if key == 'series':
                attributes['id'] = data['seriesid']
        return attributes

class RbfaRankingSensor(RbfaEntity, SensorEntity):
    """Represent all rankings for the configured team."""

    _attr_translation_key = "rankings"
    _attr_icon = "mdi:format-list-numbered"

    def __init__(
        self,
        coordinator: RbfaRankingCoordinator,
        entry: ConfigEntry,
    ) -> None:
        super().__init__(coordinator)
        self.team = entry.data['team']
        self._attr_unique_id = f"{DOMAIN}_rankings_{self.team}"

    @property
    def native_value(self) -> int:
        """Return the number of available series."""
        return len(self.coordinator.data or [])

    @property
    def extra_state_attributes(self):
        """Return the rankings grouped by series."""
        return {
            'baseid': self.team,
            'series': self.coordinator.data or [],
        }
