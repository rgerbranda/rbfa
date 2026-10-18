import logging
from datetime import datetime
from typing import Optional, List

from homeassistant.core import HomeAssistant
from homeassistant.components.calendar import CalendarEntity, CalendarEvent
from homeassistant.helpers.entity_platform import AddEntitiesCallback
from homeassistant.config_entries import ConfigEntry

from .const       import DOMAIN
from .coordinator import RbfaCoordinator
from .entity import RbfaEntity, get_team_name


_LOGGER = logging.getLogger(__name__)


async def async_setup_entry(
    hass: HomeAssistant,
    entry: ConfigEntry,
    async_add_entities: AddEntitiesCallback,
) -> None:
    """Set up RBFA calendar based on a config entry."""
    coordinator: RbfaCoordinator = hass.data[DOMAIN][entry.entry_id]

    async_add_entities(
        [RbfaCalendar(
            coordinator,
            entry,
        )]
    )

class RbfaCalendar(RbfaEntity, CalendarEntity):
    """Defines a RBFA Team Calendar."""

    _attr_icon = "mdi:soccer"

    def __init__(
        self,
        coordinator,
        config,
    ) -> None:
        super().__init__(coordinator)
        """Initialize the RBFA Team entity."""
        team = config.data['team']
        _LOGGER.debug('team: %r', team)
        self._attr_unique_id = f"{DOMAIN}_calendar_{team}"
        self._attr_name = get_team_name(coordinator)

    @property
    def event(self) -> Optional[CalendarEvent]:
        """Return the next upcoming event."""

        upcoming_match  = self.coordinator.data['matchdata']['upcoming']

        if upcoming_match is not None:
            return CalendarEvent(
                uid         = upcoming_match['matchid'],
                summary     = upcoming_match['hometeam'] + ' - ' + upcoming_match['awayteam'],
                start       = upcoming_match['starttime'],
                end         = upcoming_match['endtime'],
                location    = upcoming_match['location'],
                description = upcoming_match['series'],
            )

    async def async_get_events(
        self,
        hass: HomeAssistant,
        start_date: datetime,
        end_date: datetime
    ) -> List[CalendarEvent]:
        """Return calendar events"""
        events: List[CalendarEvent] = []

        calendar_events = self.coordinator.data['calendar_events']
        _LOGGER.debug("count: %r", len(calendar_events))
        for team_items in calendar_events:

            if team_items['starttime'] < end_date and team_items['endtime'] > start_date:

                # Summary below will define the name of event in calendar
                events.append(
                    CalendarEvent(
                        uid         = team_items['uid'],
                        summary     = team_items['summary'],
                        start       = team_items['starttime'],
                        end         = team_items['endtime'],
                        location    = team_items['location'],
                        description = team_items['description'],
                    )
                )

        return events