import logging
from datetime import timedelta
from homeassistant.util import dt as dt_util
from homeassistant.core import HomeAssistant
from homeassistant.helpers.update_coordinator import DataUpdateCoordinator, UpdateFailed

from .const import DOMAIN
from .api import RbfaApi, RbfaApiError
from .helpers import is_match_cancelled, is_match_in_progress

_LOGGER = logging.getLogger(__name__)
REFRESH_NORMAL_MINUTES = 15
REFRESH_MATCH_MINUTES = 2
REFRESH_RANKING_MINUTES = 60

class RbfaCoordinator(DataUpdateCoordinator):
    """Class to manage fetching RBFA data."""

    def __init__(self, hass: HomeAssistant, entry) -> None:
        self.client = RbfaApi(hass, entry.data['team'])

        super().__init__(
            hass,
            _LOGGER,
            name=DOMAIN,
            config_entry=entry,
            update_interval=timedelta(minutes=REFRESH_NORMAL_MINUTES),
        )

    async def _async_update_data(self):
        """Fetch RBFA data and adjust the update interval."""
        try:
            data = await self.client.update(self.config_entry)

        except RbfaApiError as exc:
            raise UpdateFailed(
                f"Unable to fetch RBFA data: {exc}"
            ) from exc

        now = dt_util.utcnow()
        events = data['calendar_events']

        match_in_progress = any(
            event.get('show_score') is True
            and is_match_in_progress(
                event.get('state'),
                event['starttime'],
                event['endtime'],
                now,
            )
            for event in events
        )

        interval = timedelta(
            minutes=REFRESH_MATCH_MINUTES if match_in_progress else REFRESH_NORMAL_MINUTES
        )

        # Plan eerder als een speelbare wedstrijd begint.
        for event in events:
            if (
                event.get('show_score') is True
                and event['starttime'] > now
                and not is_match_cancelled(
                    event.get('state'),
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

class RbfaRankingCoordinator(DataUpdateCoordinator):
    """Fetch rankings independently of the match updates."""

    def __init__(self, hass: HomeAssistant, entry) -> None:
        self.client = RbfaApi(hass, entry.data['team'])

        super().__init__(
            hass,
            _LOGGER,
            name=f"{DOMAIN}_rankings",
            config_entry=entry,
            update_interval=timedelta(
                minutes=REFRESH_RANKING_MINUTES
            ),
        )

    async def _async_update_data(self):
        """Fetch all available rankings for the configured team."""
        try:
            return await self.client.async_get_rankings()

        except RbfaApiError as exc:
            raise UpdateFailed(
                f"Unable to fetch RBFA rankings: {exc}"
            ) from exc