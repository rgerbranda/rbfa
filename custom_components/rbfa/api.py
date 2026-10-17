import logging
from datetime import datetime, timedelta
import requests
from zoneinfo import ZoneInfo
from homeassistant.util import dt as dt_util
from .const import VARIABLES, HASHES, REQUIRED, TZ

_LOGGER = logging.getLogger(__name__)

class RbfaApiError(Exception):
    """Error while fetching RBFA data."""

class RbfaApi(object):

    def __init__(self, hass, entry):
        self.hass = hass
        self.team = entry.data['team']

    def _request_graphql(self, operation, value):
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
    
        headers = {
            'Content-Type': 'application/json',
            'User-Agent': 'Mozilla/5.0 (Macintosh; Intel Mac OS X 10.15; rv:157.0) Gecko/20100101 Firefox/157.0',
            'Accept-Language': 'nl,en-US;q=0.9,en;q=0.8',
            'Origin': 'https://www.rbfa.be'
        }

        try:
            response = self.s.post(
                main_url,
                json=payload,
                headers=headers,
                timeout=15
            )
            response.raise_for_status()

            content_type = response.headers.get(
                'Content-Type', ''
            ).split(';')[0].strip().lower()

            if content_type != 'application/json':
                raise RbfaApiError(
                    f'Invalid Content-Type for {operation}: {content_type}'
                )
    
            rj = response.json()
    
            if not isinstance(rj, dict):
                raise RbfaApiError(
                    f'Invalid JSON structure for {operation}'
                )

            if rj.get('errors'):
                raise RbfaApiError(
                    f'GraphQL error in {operation}: {rj["errors"]}'
                )
    
            data = rj.get('data')

            if not isinstance(data, dict):
                raise RbfaApiError(f'Invalid data structure for {operation}')
            
            if data.get(REQUIRED[operation]) is None:
                raise RbfaApiError(f'Missing required data for {operation}')

            return data

        except requests.exceptions.RequestException as exc:
            raise RbfaApiError(
                f'Request failed for {operation}: {exc}'
            ) from exc
    
        except ValueError as exc:
            raise RbfaApiError(
                f'Invalid JSON for {operation}: {exc}'
            ) from exc

    def _get_team(self):
        response = self._request_graphql('GetTeam', self.team)
        return response

    def _get_team_calendar(self):
        response = self._request_graphql('GetTeamCalendar', self.team)
        return response

    def _get_match(self, match_id):
        response = self._request_graphql('GetMatchDetail', match_id)
        return response

    def _get_ranking(self):
        response = self._request_graphql('getSeriesAndRankingsQuery', self.team)
#         _LOGGER.debug('series: %r', response)
        return response


    async def update(self, entry):
        with requests.Session() as self.s:
            _LOGGER.debug('Updating match details using Rest API')

            options = entry.options
            data = entry.data
            
            duration = options.get('duration', data.get('duration', 105))
            show_ranking = options.get('show_ranking', data.get('show_ranking', True))
            show_referee = options.get('show_referee', data.get('show_referee', True))
            
            _LOGGER.debug('duration: %r', duration)
            _LOGGER.debug('show ranking: %r', show_ranking)

            now = dt_util.utcnow()

            r = await self.hass.async_add_executor_job(self._get_team)
            teamdata = r['team']

            r = await self.hass.async_add_executor_job(self._get_team_calendar)
            upcoming_found = False
            previous = None

            calendar_events = []
            matchdata = {
                'upcoming': None,
                'lastmatch': None
            }

            for item in sorted(r['teamCalendar'], key=lambda x: x['startTime']):
                match_id = item['id']
                r = await self.hass.async_add_executor_job(
                    self._get_match,
                    match_id
                )

                match = (r or {}).get('matchDetail') or {}
                loc = match.get('location')
                
                location = None
                if loc:
                    location = '{}\n{} {}\nBelgium'.format(
                        loc.get('address') or '',
                        loc.get('postalCode') or '',
                        loc.get('city') or ''
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

                naive_dt  = datetime.strptime(item['startTime'], '%Y-%m-%dT%H:%M:%S')
                starttime = naive_dt.replace(tzinfo = ZoneInfo(TZ))
                endtime = starttime + timedelta(minutes=duration)

                up_match = {
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

                if endtime >= now and not upcoming_found:

                    upcoming_found = True
                    matchdata['upcoming'] = up_match
                    matchdata['lastmatch'] = previous
                    if show_ranking:
                        await self.get_ranking(up_match)
                        if previous is not None:
                            await self.get_ranking(previous)

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
                    'summary': summary,
                    'location': location,
                    'description': description,
                }

                calendar_events.append(calendar_event)
                previous = up_match

            if not upcoming_found:
                _LOGGER.debug('previous=last')
                matchdata['lastmatch'] = previous
                if show_ranking and previous is not None:
                    await self.get_ranking(previous)

            return {
                    'calendar_events': calendar_events,
                    'teamdata': teamdata,
                    'matchdata': matchdata
                }

    async def get_ranking(self, matchdata):
        response = await self.hass.async_add_executor_job(
            self._get_ranking
        )

        # _request_graphql retourneert de inhoud van "data".
        team_rankings = (
            response.get('teamSeriesAndRankings') or {}
        )

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