import logging
from datetime import datetime, timedelta
from typing import Optional, List

#from homeassistant.const import CONF_RESOURCES
from homeassistant.core import HomeAssistant
from homeassistant.components.calendar import CalendarEntity, CalendarEvent
from homeassistant.helpers.entity_platform import AddEntitiesCallback
from homeassistant.config_entries import ConfigEntry

from .const       import DOMAIN
from .coordinator import MyCoordinator
from .entity      import RbfaEntity


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

class TeamCalendar(RbfaEntity, CalendarEntity):
    """Defines a RBFA Team Calendar."""

    _attr_icon = "mdi:soccer"

    def __init__(
        self,
        coordinator,
        config,
    ) -> None:
        super().__init__(coordinator)
        """Initialize the RBFA Team entity."""
        self.TeamData = coordinator
        self.config = config
        team = config.data['team']
        _LOGGER.debug('team: %r', team)
        self._attr_name      = f"{DOMAIN} {team}"
        self._attr_unique_id = f"{DOMAIN}_calendar_{team}"

        self._event = None

    @property
    def event(self) -> Optional[CalendarEvent]:
        """Return the next upcoming event."""
        upcoming = self.TeamData.matchdata().get('upcoming')
        lastmatch = self.TeamData.matchdata().get('lastmatch')

        if upcoming != None:
            _LOGGER.debug('upcoming teamname: %r', upcoming['teamname'])
            self._attr_name = f"{upcoming['clubname']} | {upcoming['teamname']}"
            return CalendarEvent(
                uid         = upcoming['matchid'],
                summary     = upcoming['hometeam'] + ' - ' + upcoming['awayteam'],
                start       = upcoming['date'],
                end         = upcoming['date'] + timedelta(hours=1),
                location    = upcoming['location'],
                description = upcoming['series'],
            )
        elif lastmatch != None:
            self._attr_name = f"{lastmatch['clubname']} | {lastmatch['teamname']}"
            return CalendarEvent(
                uid         = lastmatch['matchid'],
                summary     = lastmatch['hometeam'] + ' - ' + lastmatch['awayteam'],
                start       = lastmatch['date'],
                end         = lastmatch['date'] + timedelta(hours=1),
                location    = lastmatch['location'],
                description = lastmatch['series'],
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
                        uid         = team_items['matchid'],
                        summary     = team_items['summary'],
                        start       = team_items['date'],
                        end         = team_items['date'] + timedelta(hours=1),
                        location    = team_items['location'],
                        description = team_items['description'],
                    )
                )

        return events
