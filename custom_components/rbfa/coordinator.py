import logging
from datetime import timedelta

from homeassistant.config_entries import ConfigEntry
from homeassistant.core import HomeAssistant
from homeassistant.helpers.update_coordinator import DataUpdateCoordinator, UpdateFailed

from .const import DOMAIN
from .API import TeamApp

_LOGGER = logging.getLogger(__name__)



class MyCoordinator(DataUpdateCoordinator):
    """Class to manage fetching RBFA data."""

    def __init__(self, hass: HomeAssistant, my_api) -> None:
        """Initialize the coordinator."""

        self.collector = TeamApp(hass, my_api)
        super().__init__(
            hass,
            _LOGGER,
            name=f"{DOMAIN}",
            update_interval=timedelta(seconds=15),
        )

    async def _async_update_data(self):
        """Fetch data from the RBFA service."""
        _LOGGER.debug('fetch data coordinator')
        await self.collector.update()
        return self.collector.matchdata

    @property
    def collections(self):
        return self.collector.collections
