import logging
from datetime import datetime
from datetime import timedelta
from typing import Optional, List

from .API import TeamData

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

    async_add_entities([AfvalbeheerCalendar(hass.data[DOMAIN][conf[CONF_TEAM]], conf)])


class AfvalbeheerCalendar(CalendarEntity):
    """Defines a Afvalbeheer calendar."""

    _attr_icon = "mdi:soccer"

    def __init__(
        self,
        TeamData: TeamData,
        config,
    ) -> None:
        """Initialize the Afvalbeheer entity."""
        self.TeamData = TeamData
        self.config = config
        
        self._attr_name      = f"{DOMAIN.capitalize()}={config[CONF_TEAM]}"
        self._attr_unique_id = f"{DOMAIN}_{config[CONF_TEAM]}"

        self._event = None

    @property
    def event(self) -> Optional[CalendarEvent]:
        """Return the next upcoming event."""
        _LOGGER.debug("type: %r", self.TeamData.xteamname())
       
        if self.TeamData.xteamname() != None:
            self._attr_name = self.TeamData.xteamname()

        if self.TeamData.upcoming() != None:
            waste_item = self.TeamData.upcoming()
            return CalendarEvent(
                uid=waste_item.uid,
                summary=waste_item.summary,
                start=waste_item.date,
                end=waste_item.date + timedelta(hours=1),
                location=waste_item.location,
                description='test',
            )

    async def async_get_events(
        self, hass: HomeAssistant, start_date: datetime, end_date: datetime
    ) -> List[CalendarEvent]:
        """Return calendar events within a datetime range."""
        events: List[CalendarEvent] = []

        _LOGGER.debug("aantal: %r", len(self.TeamData.collections))
        for team_items in self.TeamData.collections:
            
            if start_date.date() <= team_items.date.date() <= end_date.date():
            #    _LOGGER.debug(start_date.date())
                end = team_items.date + timedelta(hours=1)
            #    _LOGGER.debug(type(end))
                # Summary below will define the name of event in calendar
                events.append(
                    CalendarEvent(
                        uid=team_items.uid,
                        summary=team_items.summary,
                        start=team_items.date,
                        location=team_items.location,
                        end=end,
                    )
                )

        return events
