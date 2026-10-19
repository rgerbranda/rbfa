import logging
from datetime import timedelta
from homeassistant.util import dt as dt_util
from homeassistant.core import HomeAssistant
from homeassistant.helpers.update_coordinator import DataUpdateCoordinator, UpdateFailed

from .const import DOMAIN
from .api import RbfaApi, RbfaApiError
from .helpers import is_match_ended, is_match_in_progress

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
        """Fetch RBFA data and adjust the update interval."""
        try:
            data = await self.client.update(self.config_entry)

        except RbfaApiError as exc:
            _LOGGER.error("RBFA update failed: %s", exc)
            raise UpdateFailed(
                f"Unable to fetch RBFA data: {exc}"
            ) from exc

        now = dt_util.utcnow()
        events = data['calendar_events']

        match_in_progress = any(
            is_match_in_progress(
                event.get('state'),
                event['starttime'],
                event['endtime'],
                now,
            )
            for event in events
        )

        interval = timedelta(
            minutes=5 if match_in_progress else 15
        )

        # Plan eerder als een speelbare wedstrijd begint.
        for event in events:
            if (
                event['starttime'] > now
                and not is_match_ended(
                    event.get('state'),
                    event['endtime'],
                    now,
                )
            ):
                interval = min(
                    interval,
                    event['starttime'] - now,
                )

        self.update_interval = interval

        _LOGGER.debug(
            "Next RBFA update in %s; match in progress: %s",
            interval,
            match_in_progress,
        )

        return data