import logging
from datetime import datetime
from datetime import timedelta
from typing import Optional, List

#from .API import TeamData

from homeassistant.const import CONF_RESOURCES
from homeassistant.components.calendar import CalendarEntity, CalendarEvent
from homeassistant.core import HomeAssistant

from .const import DOMAIN, CONF_TEAM


_LOGGER = logging.getLogger(__name__)


def setup_platform(hass, config, async_add_entities, discovery_info=None):

    if discovery_info and "config" in discovery_info:
        conf = discovery_info["config"]
    else:
        conf = config

    if not conf:
        return

    async_add_entities([TeamCalendar(hass.data[DOMAIN][conf[CONF_TEAM]], conf)])


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

        self._attr_name      = f"{DOMAIN} {config[CONF_TEAM]}"
        self._attr_unique_id = f"{DOMAIN}_calendar_{config[CONF_TEAM]}"

        self._event = None

    @property
    def event(self) -> Optional[CalendarEvent]:
        """Return the next upcoming event."""
#        _LOGGER.debug('set upcoming event')
        if self.TeamData.teamdata() != None:
            teamdata = self.TeamData.teamdata()
            self._attr_name = f"{teamdata['name']} | {teamdata['clubName']}"

        if self.TeamData.upcoming() != None:
            team_items = self.TeamData.upcoming()
            return CalendarEvent(
                uid         = team_items['uid'],
                summary     = team_items['hometeam'] + ' - ' + team_items['awayteam'],
                start       = team_items['date'],
                end         = team_items['date'] + timedelta(hours=1),
                location    = team_items['location'],
                description = 'test',
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
