import logging
from datetime import timedelta

from homeassistant.core import HomeAssistant
from homeassistant.helpers.update_coordinator import DataUpdateCoordinator, UpdateFailed

from .const import DOMAIN
from .api import RbfaApi, RbfaApiError

_LOGGER = logging.getLogger(__name__)

class RbfaCoordinator(DataUpdateCoordinator):
    """Class to manage fetching RBFA data."""

    def __init__(self, hass: HomeAssistant, entry) -> None:
        self.client = RbfaApi(hass, entry.data['team'])

        super().__init__(
            hass,
            _LOGGER,
            name=DOMAIN,
            config_entry=entry,
            update_interval=timedelta(minutes=15),
        )

    async def _async_update_data(self):
        """Fetch data from RBFA."""

        try:
            return await self.client.update(self.config_entry)

        except RbfaApiError as exc:
            _LOGGER.error("RBFA update failed: %s", exc, exc_info=False)
            raise UpdateFailed(
                f"Unable to fetch RBFA data: {exc}"
            ) from exc