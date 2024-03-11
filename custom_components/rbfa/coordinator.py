

from homeassistant.config_entries import ConfigEntry
from homeassistant.core import HomeAssistant
from homeassistant.helpers.update_coordinator import DataUpdateCoordinator, UpdateFailed
from datetime import timedelta

from .const import DOMAIN
import logging
from .API import TeamApp

_LOGGER = logging.getLogger(__name__)



class MyCoordinator(DataUpdateCoordinator):
    """Class to manage fetching Elgato data."""
    
    def __init__(self, hass: HomeAssistant, my_api) -> None:
        """Initialize the coordinator."""
        team = '283884'
        team = '300872'

        self.collector = TeamApp(hass, my_api.data['team'])
        super().__init__(
            hass,
            _LOGGER,
            name=f"{DOMAIN}",
            update_interval=timedelta(seconds=30),
        )

    async def _async_update_data(self):
        """Fetch data from the Elgato device."""
        _LOGGER.debug('fetch data coordinator')
        await self.collector.update()
        
    @property
    def collections(self):
        return self.collector.collections

#    def teamdata(self):
#        return self.collector.teamdata

    def upcoming(self):
        return self.collector.upcoming

#    def lastmatch(self):
#        return self.collector.lastmatch
