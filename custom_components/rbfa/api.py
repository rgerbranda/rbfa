import asyncio
import json
import logging
import math
from datetime import datetime, timedelta
from copy import deepcopy
from time import monotonic
from zoneinfo import ZoneInfo
from homeassistant.util import dt as dt_util
from .const import DOMAIN, VARIABLES, HASHES, REQUIRED, TZ
from .helpers import is_match_ended, is_match_cancelled

from aiohttp import ClientError, ClientTimeout
from homeassistant.helpers.aiohttp_client import async_get_clientsession
from homeassistant.helpers.storage import Store
from homeassistant.helpers.translation import async_get_translations

_LOGGER = logging.getLogger(__name__)
MATCH_CACHE_TTL = 24 * 60 * 60
USER_AGENT = (
    "RBFA-HomeAssistant/1.0 "
    "(+https://github.com/rgerbranda/rbfa)"
)
GEOCODING_URL = "https://nominatim.openstreetmap.org/search"
GEOCODING_ATTRIBUTION = (
    "© OpenStreetMap contributors, ODbL — "
    "https://www.openstreetmap.org/copyright"
)
GEOCODING_INTERVAL = 16
GEOCODING_RETRY = 24 * 60 * 60

class RbfaApiError(Exception):
    """Error while fetching RBFA data."""

class RbfaApi(object):

    def __init__(self, hass, team_id):
        self.hass = hass
        self.team = team_id
        self._match_cache = {}
        self._team_data = None
        self.session = async_get_clientsession(hass)
        # Share persistent location results and rate limiting across teams.
        self._geocoding = hass.data.setdefault(
            f"{DOMAIN}_geocoding",
            {
                "store": Store(hass, 1, f"{DOMAIN}_geocoding"),
                "cache": None,
                "lock": asyncio.Lock(),
                "next_request": 0.0,
            },
        )

    async def async_get_config_data(self):
        """Fetch team before creating a config entry."""
        response_team = await self._get_team()

        return {
            'team': response_team['team'],
        }

    async def _request_graphql(self, operation, value):
        main_url = 'https://datalake-prod2018.rbfa.be/graphql'

        payload = {
            "operationName": operation,
            "variables": {
                VARIABLES[operation]: value,
                "language": "nl"
            },
            "extensions": {
                "persistedQuery": {
                    "version": 1,
                    "sha256Hash": HASHES[operation]
                }
            }
        }
        _LOGGER.debug('payload: %r', payload)

        headers = {
            'Content-Type': 'application/json',
            'User-Agent': 'Mozilla/5.0 (Macintosh; Intel Mac OS X 10.15; rv:157.0) Gecko/20100101 Firefox/157.0',
            'Accept-Language': 'nl,en-US;q=0.9,en;q=0.8',
            'Origin': 'https://www.rbfa.be'
        }

        try:
            async with self.session.post(
                main_url,
                json=payload,
                headers=headers,
                timeout=ClientTimeout(total=15),
            ) as response:
                response.raise_for_status()

                content_type = (
                    response.headers.get('Content-Type', '')
                    .split(';')[0]
                    .strip()
                    .lower()
                )

                if content_type != 'application/json':
                    raise RbfaApiError(
                        f'Invalid Content-Type for {operation}: '
                        f'{content_type}'
                    )

                response_json = await response.json()

            if not isinstance(response_json, dict):
                raise RbfaApiError(
                    f'Invalid JSON structure for {operation}'
                )

            if response_json.get('errors'):
                raise RbfaApiError(
                    f'GraphQL error in {operation}: '
                    f'{response_json["errors"]}'
                )

            data = response_json.get('data')

            if not isinstance(data, dict):
                raise RbfaApiError(
                    f'Invalid data structure for {operation}'
                )

            required_key = REQUIRED[operation]

            if required_key not in data:
                raise RbfaApiError(
                    f'Missing required data for {operation}'
                )

            if (
                data[required_key] is None
                and operation != 'getSeriesAndRankingsQuery'
            ):
                raise RbfaApiError(
                    f'Empty required data for {operation}'
                )

            return data

        except (ClientError, TimeoutError) as exc:
            raise RbfaApiError(
                f'Request failed for {operation}: {exc}'
            ) from exc

        except ValueError as exc:
            raise RbfaApiError(
                f'Invalid JSON for {operation}: {exc}'
            ) from exc

    async def _get_team(self):
        return await self._request_graphql('GetTeam', self.team)

    async def _get_team_calendar(self):
        return await self._request_graphql(
            'GetTeamCalendar', self.team
        )

    async def _get_match(self, match_id):
        return await self._request_graphql(
            'GetMatchDetail', match_id
        )

    async def _get_ranking(self):
        return await self._request_graphql(
            'getSeriesAndRankingsQuery', self.team
        )

    async def _get_coordinates(self, location, endpoint):
        """Resolve an address, using a persistent cache shared by all teams."""
        address = (location.get("address") or "").strip()
        postal_code = (location.get("postalCode") or "").strip()
        city = (location.get("city") or "").strip()

        if not address or not city:
            return {}

        query = f"{address}, {postal_code} {city}, Belgium"
        cache_key = json.dumps(
            [
                endpoint,
                str(location.get("id") or ""),
                " ".join(query.casefold().split()),
            ],
            ensure_ascii=False,
        )
        shared = self._geocoding

        async with shared["lock"]:
            if shared["cache"] is None:
                shared["cache"] = (
                    await shared["store"].async_load() or {}
                )

            cache = shared["cache"]
            cached = cache.get(cache_key)
            now = dt_util.utcnow().timestamp()

            if cached is not None:
                if cached["coordinates"]:
                    return dict(cached["coordinates"])
                if now < cached["retry_after"]:
                    return {}

            # Defer another uncached address to a later coordinator update.
            if monotonic() < shared["next_request"]:
                return {}

            shared["next_request"] = monotonic() + GEOCODING_INTERVAL
            coordinates = {}
            retry_after = now + GEOCODING_RETRY

            try:
                async with self.session.get(
                    endpoint,
                    params={
                        "q": query,
                        "format": "jsonv2",
                        "limit": 1,
                        "countrycodes": "be",
                    },
                    headers={
                        "User-Agent": USER_AGENT,
                    },
                    timeout=ClientTimeout(total=10),
                ) as response:
                    response.raise_for_status()
                    results = await response.json()

                if not isinstance(results, list):
                    raise ValueError("Invalid geocoding response")

                if results:
                    latitude = float(results[0]["lat"])
                    longitude = float(results[0]["lon"])
                    if not (
                        math.isfinite(latitude)
                        and math.isfinite(longitude)
                        and -90 <= latitude <= 90
                        and -180 <= longitude <= 180
                    ):
                        raise ValueError("Invalid coordinates")
                    coordinates = {
                        "latitude": latitude,
                        "longitude": longitude,
                    }

            except (
                ClientError,
                TimeoutError,
                ValueError,
                KeyError,
                TypeError,
                IndexError,
            ) as exc:
                _LOGGER.warning(
                    "Could not resolve RBFA location %s: %s",
                    location.get("id"),
                    exc,
                )
                retry_after = now + 60 * 60
                # Back off across all teams after an HTTP/service error.
                shared["next_request"] = monotonic() + 60 * 60

            cache[cache_key] = {
                "coordinates": coordinates,
                "retry_after": retry_after,
            }
            shared["store"].async_delay_save(lambda: cache, 5)
            return dict(coordinates)

    async def async_get_rankings(self):
        """Fetch available series and their general rankings."""
        response = await self._get_ranking()
        team_rankings = response.get('teamSeriesAndRankings') or {}

        series_list = []

        for series in team_rankings.get('rankings') or []:
            if not (series.get('visibility') or {}).get(
                'showRanking', True
            ):
                continue

            general_ranking = next(
                (
                    ranking
                    for ranking in series.get('rankings') or []
                    if ranking.get('type') == 'generalRanking'
                ),
                None,
            )

            if general_ranking is None:
                continue

            teams = general_ranking.get('teams') or []
            if not teams:
                continue

            series_list.append({
                'seriesId': str(series['id']),
                'name': series['name'],
                'ranking': [
                    {
                        key: value
                        for key, value in team.items()
                        if key != '__typename'
                    }
                    for team in teams
                ],
            })

        return series_list

    async def update(self, entry):
        _LOGGER.debug('Updating match details using Rest API')

        translations = await async_get_translations(
            self.hass,
            self.hass.config.language,
            "entity",
            integrations={DOMAIN},
        )

        options = entry.options
        data = entry.data

        duration = options.get('duration', data.get('duration', 105))

        _LOGGER.debug('duration: %r', duration)

        now = dt_util.utcnow()
        timezone = ZoneInfo(TZ)
        match_duration = timedelta(minutes=duration)

        if self._team_data is None:
            response_team = await self._get_team()
            self._team_data = response_team['team']

        response_calendar = await self._get_team_calendar()
        upcoming_found = False
        previous = None

        calendar_events = []
        matchdata = {
            'upcoming': None,
            'lastmatch': None
        }

        for item in sorted(response_calendar['teamCalendar'], key=lambda x: x['startTime']):

            naive_dt  = datetime.strptime(item['startTime'], '%Y-%m-%dT%H:%M:%S')
            starttime = naive_dt.replace(tzinfo=timezone)
            endtime = starttime + match_duration

            match_id = item['id']
            cached = self._match_cache.get(match_id)
            show_score = item.get('showScore') is True

            match_ended = is_match_ended(
                item.get('state'),
                endtime,
                now,
            )

            match_cancelled = is_match_cancelled(
                item.get('state'),
            )

            match_started = (
                starttime <= now
                and not match_cancelled
            )

            refresh_needed = (
                cached is None
                or cached['starttime'] != starttime
                or monotonic() - cached['fetched_at'] >= MATCH_CACHE_TTL
                or (
                    match_started
                    and not cached['fetched_after_start']
                )
            )

            if refresh_needed:
                response_match = await self._get_match(match_id)
                match = response_match['matchDetail']

                self._match_cache[match_id] = {
                    'starttime': starttime,
                    'match_detail': deepcopy(match),
                    'fetched_at': monotonic(),
                    'fetched_after_start': now >= starttime,
                }
            else:
                match = cached['match_detail']
            # End of fetch/cache.

            location_data = match.get('location')

            location = None
            if location_data:
                location = '{}\n{} {}\nBelgium'.format(
                    location_data.get('address') or '',
                    location_data.get('postalCode') or '',
                    location_data.get('city') or ''
                )

            referee = None
            for official in match.get('officials') or []:
                if official.get('function') == 'referee':
                    referee = " ".join(
                        part.strip()
                        for part in (
                            official.get('firstName'),
                            official.get('lastName'),
                        )
                        if part and part.strip()
                    ) or None
                    break

            state = item.get('state')

            translated_state = translations.get(
                f"component.{DOMAIN}.entity.sensor.upcoming_state.state.{state}",
                state,
            )

            description = item['series']['name']

            display_state = translated_state or state

            if display_state:
                description += f" ({display_state})"

            include_outcome = (
                show_score
                and match_started
            )

            if include_outcome:
                outcome = item.get('outcome') or {}
                result = '\nNo match score'

                if outcome.get('homeTeamGoals') is not None:
                    result = (
                        f"\nGoals: {outcome.get('homeTeamGoals')} - "
                        f"{outcome.get('awayTeamGoals')}"
                    )

                if outcome.get('homeTeamPenaltiesScored') is not None:
                    result += (
                        f";\nPenalties: "
                        f"{outcome.get('homeTeamPenaltiesScored')} - "
                        f"{outcome.get('awayTeamPenaltiesScored')}"
                    )

                description += result

            match_data = {
                'matchid': item['id'],
                'team': self.team,
                'channel': item['channel'],
                'starttime': starttime,
                'endtime': endtime,
                'location': location,
                'location_data': location_data,
                'referee': referee,
                'hometeam': item['homeTeam']['name'],
                'hometeamid': item['homeTeam']['id'],
                'hometeamlogo': item['homeTeam']['logo'],
                'awayteam': item['awayTeam']['name'],
                'awayteamid': item['awayTeam']['id'],
                'awayteamlogo': item['awayTeam']['logo'],
                'series': item['series']['name'],
                'seriesid': item['series']['id'],
                'state': item['state'],
                'description': description,
            }

            if include_outcome:

                match_data.update({
                    'hometeamgoals': outcome.get('homeTeamGoals'),
                    'hometeampenalties': outcome.get(
                        'homeTeamPenaltiesScored'
                    ),
                    'awayteamgoals': outcome.get('awayTeamGoals'),
                    'awayteampenalties': outcome.get(
                        'awayTeamPenaltiesScored'
                    ),
                })

            if (
                not match_ended
                and not match_cancelled
                and not upcoming_found
            ):

                upcoming_found = True
                matchdata['upcoming'] = match_data
                matchdata['lastmatch'] = previous

            summary = item['homeTeam']['name'] + ' - ' + item['awayTeam']['name']

            calendar_event = {
                'uid': item['id'],
                'starttime': starttime,
                'endtime': endtime,
                'state': item.get('state'),
                'summary': summary,
                'location': location,
                'description': description,
                'show_score': show_score,
            }

            calendar_events.append(calendar_event)

            if starttime <= now:
                previous = match_data

        if not upcoming_found:
            matchdata['lastmatch'] = previous

        geocoding_url = options.get("geocoding_url", GEOCODING_URL)
        for selected_match in matchdata.values():
            if selected_match is None:
                continue
            coordinates = await self._get_coordinates(
                selected_match.get("location_data") or {},
                geocoding_url,
            )
            selected_match.update(coordinates)
            if coordinates:
                selected_match["location_attribution"] = (
                    GEOCODING_ATTRIBUTION
                )

        active_match_ids = {
            item['id']
            for item in response_calendar['teamCalendar']
        }
        self._match_cache = {
            match_id: cached
            for match_id, cached in self._match_cache.items()
            if match_id in active_match_ids
        }

        return {
            'calendar_events': calendar_events,
            'teamdata': self._team_data,
            'matchdata': matchdata,
        }
