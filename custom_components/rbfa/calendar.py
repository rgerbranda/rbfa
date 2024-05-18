import logging
from datetime import datetime, timedelta
from typing import Optional, List

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
    """Set up RBFA sensor based on a config entry."""
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

        if 'alt_name' in self.config.options:
            self._attr_name = self.config.options['alt_name']
        elif 'alt_name' in self.config.data:
            self._attr_name = self.config.data['alt_name']
        else:
            self._attr_name = f"{self.TeamData.teamdata['clubName']} | {self.TeamData.teamdata['name']}"

        upcoming = self.TeamData.data['upcoming']
        lastmatch = self.TeamData.data['lastmatch']

        if upcoming != None:
#             _LOGGER.debug('upcoming teamname: %r', upcoming['teamname'])
            return CalendarEvent(
                uid         = upcoming['matchid'],
                summary     = upcoming['hometeam'] + ' - ' + upcoming['awayteam'],
                start       = upcoming['starttime'],
                end         = upcoming['endtime'],
                location    = upcoming['location'],
                description = upcoming['series'],
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

            if start_date.date() <= team_items['starttime'].date() <= end_date.date():

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
