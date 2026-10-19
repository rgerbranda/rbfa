import logging
from datetime import datetime, timedelta
from copy import deepcopy
from time import monotonic
from zoneinfo import ZoneInfo
from homeassistant.util import dt as dt_util
from .const import VARIABLES, HASHES, REQUIRED, TZ

from aiohttp import ClientError, ClientTimeout
from homeassistant.helpers.aiohttp_client import async_get_clientsession

_LOGGER = logging.getLogger(__name__)

class RbfaApiError(Exception):
    """Error while fetching RBFA data."""

class RbfaApi(object):

    def __init__(self, hass, team_id):
        self.hass = hass
        self.team = team_id
        self._match_cache = {}
        self._team_data = None
        self.session = async_get_clientsession(hass)

    async def async_get_config_data(self):
        """Fetch team and rankings before creating a config entry."""
        response_team = await self._get_team()
        response_ranking = await self._get_ranking()

        return {
            'team': response_team['team'],
            'rankings': response_ranking['teamSeriesAndRankings'],
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

    async def update(self, entry):
        _LOGGER.debug('Updating match details using Rest API')

        options = entry.options
        data = entry.data

        duration = options.get('duration', data.get('duration', 105))
        show_ranking = options.get('show_ranking', data.get('show_ranking', True))
        show_referee = options.get('show_referee', data.get('show_referee', True))

        _LOGGER.debug('duration: %r', duration)
        _LOGGER.debug('show ranking: %r', show_ranking)

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
            match_in_progress = (
                starttime <= now
                and item.get('state') != 'finished'
            )
            match_id = item['id']
            cached = self._match_cache.get(match_id)

            cache_valid = (
                cached is not None
                and cached['calendar_item'] == item
                and monotonic() - cached['fetched_at'] < 3600 * 24
                and not match_in_progress
            )

            if cache_valid:
                match = cached['match_detail']
            else:
                response_match = await self._get_match(match_id)
                match = response_match['matchDetail']

                self._match_cache[match_id] = {
                    'calendar_item': deepcopy(item),
                    'match_detail': deepcopy(match),
                    'fetched_at': monotonic(),
                }
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
            if show_referee:
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

            match_data = {
                'matchid': item['id'],
                'team': self.team,
                'channel': item['channel'],
                'starttime': starttime,
                'endtime': endtime,
                'location': location,
                'referee': referee,
                'hometeam': item['homeTeam']['name'],
                'hometeamid': item['homeTeam']['id'],
                'hometeamlogo': item['homeTeam']['logo'],
                'hometeamgoals': item['outcome']['homeTeamGoals'],
                'hometeampenalties': item['outcome']['homeTeamPenaltiesScored'],
                'hometeamposition': None,
                'awayteam': item['awayTeam']['name'],
                'awayteamid': item['awayTeam']['id'],
                'awayteamlogo': item['awayTeam']['logo'],
                'awayteamgoals': item['outcome']['awayTeamGoals'],
                'awayteampenalties': item['outcome']['awayTeamPenaltiesScored'],
                'awayteamposition': None,
                'series': item['series']['name'],
                'seriesid': item['series']['id'],
                'ranking': [],
            }

            if item.get('state') != 'finished' and not upcoming_found:
                upcoming_found = True
                matchdata['upcoming'] = match_data
                matchdata['lastmatch'] = previous

            summary = item['homeTeam']['name'] + ' - ' + item['awayTeam']['name']
            description = item['series']['name'] + ' (state: ' + item['state'] + ')'

            if show_ranking:
                result = 'No match score'
                if item['outcome']['homeTeamGoals'] is not None:
                    result = 'Goals: ' + str(item['outcome']['homeTeamGoals']) + ' - ' + str(item['outcome']['awayTeamGoals'])
                if item['outcome']['homeTeamPenaltiesScored'] is not None:
                    result += '; Penalties: ' + str(item['outcome']['homeTeamPenaltiesScored']) + ' - '
                    result += str(item['outcome']['awayTeamPenaltiesScored'])
                description += "; " + result

            calendar_event = {
                'uid': item['id'],
                'starttime': starttime,
                'endtime': endtime,
                'state': item.get('state'),
                'summary': summary,
                'location': location,
                'description': description,
            }

            calendar_events.append(calendar_event)
            previous = match_data

        if not upcoming_found:
            matchdata['lastmatch'] = previous

        active_match_ids = {
            item['id']
            for item in response_calendar['teamCalendar']
        }
        self._match_cache = {
            match_id: cached
            for match_id, cached in self._match_cache.items()
            if match_id in active_match_ids
        }

        if show_ranking and any(
            match is not None for match in matchdata.values()
        ):
            response_ranking = await self._get_ranking()
            team_rankings = (
                response_ranking.get('teamSeriesAndRankings') or {}
            )

            for match in matchdata.values():
                if match is not None:
                    self._apply_ranking(match, team_rankings)

        return {
            'calendar_events': calendar_events,
            'teamdata': self._team_data,
            'matchdata': matchdata,
        }

    def _apply_ranking(self, matchdata, team_rankings):
        """Apply previously fetched rankings to a match."""

        matchdata['ranking'] = []
        matchdata['hometeamposition'] = None
        matchdata['awayteamposition'] = None

        series_data = next(
            (
                series
                for series in team_rankings.get('rankings') or []
                if str(series['id']) == str(matchdata['seriesid'])
            ),
            None,
        )

        if series_data is None:
            return

        if not (series_data.get('visibility') or {}).get(
            'showRanking', True
        ):
            return

        general_ranking = next(
            (
                ranking
                for ranking in series_data.get('rankings') or []
                if ranking.get('type') == 'generalRanking'
            ),
            None,
        )

        if general_ranking is None:
            return

        for rank in general_ranking.get('teams') or []:
            team_id = rank['teamId']
            position = rank['position']

            matchdata['ranking'].append({
                'position': position,
                'team': rank['name'],
                'id': team_id,
            })

            if str(team_id) == str(matchdata['hometeamid']):
                matchdata['hometeamposition'] = position

            if str(team_id) == str(matchdata['awayteamid']):
                matchdata['awayteamposition'] = position