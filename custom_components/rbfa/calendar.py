import logging
from datetime import datetime
from datetime import timedelta
from typing import Optional, List

#from .API import TeamData

from homeassistant.const import CONF_RESOURCES
from homeassistant.components.calendar import CalendarEntity, CalendarEvent
from homeassistant.core import HomeAssistant

from .const import DOMAIN, CONF_TEAM

from homeassistant.helpers.entity_platform import AddEntitiesCallback
from homeassistant.config_entries import ConfigEntry

_LOGGER = logging.getLogger(__name__)


async def async_setup_entry(
    hass: HomeAssistant,
    entry: ConfigEntry,
    async_add_entities: AddEntitiesCallback,
) -> None:
    """Set up Elgato sensor based on a config entry."""
    coordinator: MyCoordinator = hass.data[DOMAIN][entry.entry_id]

    async_add_entities(
        [TeamCalendar(
            coordinator,
            entry,
        )]
    )

class TeamCalendar(CalendarEntity):
    """Defines a RBFA Team Calendar."""

    _attr_icon = "mdi:soccer"

    def __init__(
        self,
        TeamData,
        config,
    ) -> None:
        """Initialize the RBFA Team entity."""
        self.TeamData = TeamData
        self.config = config
        team = config.data['team']
        _LOGGER.debug('team: %r', team)
        self._attr_name      = f"{DOMAIN} {team}"
        self._attr_unique_id = f"{DOMAIN}_calendar_{team}"

        self._event = None

    @property
    def event(self) -> Optional[CalendarEvent]:
        """Return the next upcoming event."""
        _LOGGER.debug('set upcoming event')

        if self.TeamData.upcoming() != None:
            team_items = self.TeamData.upcoming()
            _LOGGER.debug('name: %r', team_items['teamname'])
            self._attr_name = f"{team_items['clubname']} | {team_items['teamname']}"
            return CalendarEvent(
                uid         = team_items['uid'],
                summary     = team_items['hometeam'] + ' - ' + team_items['awayteam'],
                start       = team_items['date'],
                end         = team_items['date'] + timedelta(hours=1),
                location    = team_items['location'],
                description = team_items['series'],
            )

    async def async_get_events(
        self,
        hass: HomeAssistant,
        start_date: datetime,
        end_date: datetime
    ) -> List[CalendarEvent]:
        """Return calendar events"""
        events: List[CalendarEvent] = []

        _LOGGER.debug("count: %r", len(self.TeamData.collections))
        for team_items in self.TeamData.collections:

            if start_date.date() <= team_items['date'].date() <= end_date.date():

                # Summary below will define the name of event in calendar
                events.append(
                    CalendarEvent(
                        uid         = team_items['uid'],
                        summary     = team_items['summary'],
                        start       = team_items['date'],
                        end         = team_items['date'] + timedelta(hours=1),
                        location    = team_items['location'],
                        description = team_items['description'],
                    )
                )

        return events
