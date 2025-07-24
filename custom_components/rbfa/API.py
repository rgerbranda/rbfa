import logging
from datetime import datetime, timedelta
import json
import requests
from zoneinfo import ZoneInfo
from homeassistant.util import dt as dt_util
from .const import DOMAIN, VARIABLES, HASHES, REQUIRED, TZ

_LOGGER = logging.getLogger(__name__)


class TeamApp(object):

    def __init__(self, hass, my_api):
        self.hass = hass
        self.team = my_api.data['team']

    def __get_url(self, operation, value):
        try:
            main_url = 'https://datalake-prod2018.rbfa.be/graphql'
            url = '{}?operationName={}&variables={{"{}":"{}","language":"nl"}}&extensions={{"persistedQuery":{{"version":1,"sha256Hash":"{}"}}}}'.format(
                main_url,
                operation,
                VARIABLES[operation],
                value,
                HASHES[operation]
            )
            response = self.s.get(url)
            if response.status_code != 200:
                _LOGGER.debug('Invalid response from server for collection data')
                return

            rj = response.json()
            if rj.get('data') is None:
                _LOGGER.debug("Error for operation {}: {}".format(operation, rj['errors'][0]['message']))
            elif rj['data'][REQUIRED[operation]] is None:
                _LOGGER.debug('No results for operation %s', operation)
            else:
                return rj

        except requests.exceptions.RequestException as exc:
            _LOGGER.error('Error occurred while fetching data: %r', exc)

    def __get_team(self):
        return self.__get_url('GetTeam', self.team)

    def __get_data(self):
        return self.__get_url('GetTeamCalendar', self.team)

    def __get_match(self):
        return self.__get_url('GetMatchDetail', self.match)

    def __get_ranking(self):
        return self.__get_url('GetSeriesRankings', self.series)

    async def update(self, my_api):
        with requests.Session() as self.s:
            _LOGGER.debug('Updating match details using Rest API')

            if logging.getLogger(__name__).getEffectiveLevel() == 10:
                logging.getLogger("urllib3").setLevel(logging.DEBUG)

            self.duration = my_api.options.get('duration', my_api.data.get('duration'))
            self.show_ranking = my_api.options.get('show_ranking', my_api.data.get('show_ranking', True))
            self.show_referee = my_api.options.get('show_referee', my_api.data.get('show_referee', True))

            self.collections = []
            _LOGGER.debug('Duration: %r', self.duration)
            _LOGGER.debug('Show ranking: %r', self.show_ranking)

            now = dt_util.utcnow()
            r = await self.hass.async_add_executor_job(self.__get_team)
            if r:
                self.teamdata = r['data']['team']

            r = await self.hass.async_add_executor_job(self.__get_data)
            if r:
                upcoming = False
                previous = None
                referee = None

                for item in r['data']['teamCalendar']:
                    self.match = item['id']
                    r = await self.hass.async_add_executor_job(self.__get_match)
                    if r:
                        match = r['data']['matchDetail']['location']
                        location = '{}\n{} {}\nBelgium'.format(
                            match['address'],
                            match['postalCode'],
                            match['city'],
                        )
                        if self.show_referee:
                            officials = r['data']['matchDetail'].get('officials', [])
                            for x in officials:
                                if x['function'] == 'referee':
                                    referee = f"{x['firstName']} {x['lastName']}"
                    else:
                        location = None

                    naive_dt = datetime.strptime(item['startTime'], '%Y-%m-%dT%H:%M:%S')
                    starttime = naive_dt.replace(tzinfo=ZoneInfo(TZ))
                    endtime = starttime + timedelta(minutes=self.duration)

                    matchdata = {
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

                    if endtime >= now and not upcoming:
                        upcoming = True
                        self.matchdata = {
                            'upcoming': matchdata,
                            'lastmatch': previous
                        }
                        if self.show_ranking:
                            await self.get_ranking('upcoming')
                            if previous:
                                await self.get_ranking('lastmatch')

                    summary = f"{item['homeTeam']['name']} - {item['awayTeam']['name']}"
                    description = f"{item['series']['name']} (state: {item['state']})"

                    if self.show_ranking:
                        result = 'No match score'
                        if item['outcome']['homeTeamGoals'] is not None:
                            result = f"Goals: {item['outcome']['homeTeamGoals']} - {item['outcome']['awayTeamGoals']}"
                        if item['outcome']['homeTeamPenaltiesScored'] is not None:
                            result += f"; Penalties: {item['outcome']['homeTeamPenaltiesScored']} - {item['outcome']['awayTeamPenaltiesScored']}"
                        description += "; " + result

                    self.collections.append({
                        'uid': item['id'],
                        'starttime': starttime,
                        'endtime': endtime,
                        'summary': summary,
                        'location': location,
                        'description': description,
                    })

                    previous = matchdata

                if not upcoming:
                    _LOGGER.debug('No upcoming match found; using last match only')
                    self.matchdata = {
                        'upcoming': None,
                        'lastmatch': previous
                    }
                    if self.show_ranking:
                        await self.get_ranking('lastma_
