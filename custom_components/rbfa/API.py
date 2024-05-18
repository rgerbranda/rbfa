import logging
from datetime import datetime, timedelta
import json
import requests
from zoneinfo import ZoneInfo

from homeassistant.util import dt as dt_util
from homeassistant.components import persistent_notification

from .const import DOMAIN, VARIABLES, HASHES, REQUIRED, TZ


_LOGGER = logging.getLogger(__name__)


class TeamApp(object):

    def __init__(self, hass, my_api):
#         self.teamdata = None
#         self.matchdata = {'upcoming': None, 'lastmatch': None}
        self.hass = hass
        self.team = my_api.data['team']


    def __get_url(self, operation, value):
        with open(operation + ".txt", 'r') as fson:
            rj = json.load(fson)
        return rj

    def xx__get_url(self, operation, value):
        try:
            main_url = 'https://datalake-prod2018.rbfa.be/graphql'
            url = '{}?operationName={}&variables={{"{}":"{}","language":"nl"}}&extensions={{"persistedQuery":{{"version":1,"sha256Hash":"{}"}}}}'.format(
                main_url,
                operation,
                VARIABLES[operation],
                value,
                HASHES[operation]
            )
#            _LOGGER.debug(url)
            response = requests.get(url)
            if response.status_code != 200:
                _LOGGER.debug('Invalid response from server for collection data')
                return

            rj = response.json()
            if rj.get('data') is None:
                persistent_notification.create(
                    self.hass,
                    "Error for operation {}: {}".format(operation, rj['errors'][0]['message']),
                    DOMAIN,
                    "{}_invalid_config_{}_{}".format(DOMAIN, operation, value)
                )
                _LOGGER.debug(url)

            elif rj['data'][REQUIRED[operation]] == None:
                _LOGGER.debug('no results')

            else:
                return rj

        except requests.exceptions.RequestException as exc:
            _LOGGER.error('Error occurred while fetching data: %r', exc)

    def __get_team(self):
        response = self.__get_url('GetTeam', self.team)
        return response

    def __get_data(self):
        response = self.__get_url('GetTeamCalendar', self.team)
        return response

    def __get_match(self):
        response = self.__get_url('GetMatchDetail', self.match)
        return response

    def __get_ranking(self):
#        _LOGGER.debug(self.series)
        response = self.__get_url('GetSeriesRankings', self.series)
        return response


    async def update(self, my_api):
        _LOGGER.debug('Updating match details using Rest API')

        if 'duration' in my_api.options:
            self.duration = my_api.options['duration']
        else:
            self.duration = my_api.data['duration']

        if 'show_ranking' in my_api.options:
            self.show_ranking = my_api.options['show_ranking']
        elif 'show_ranking' in my_api.data:
            self.show_ranking = my_api.data['show_ranking']
        else:
            self.show_ranking = True

        self.collections = [];
        _LOGGER.debug('duration: %r', self.duration)
        _LOGGER.debug('show ranking: %r', self.show_ranking)

        now = dt_util.utcnow()

        r = await self.hass.async_add_executor_job(self.__get_team)
        if r != None:
            self.teamdata = r['data']['team']

        r = await self.hass.async_add_executor_job(self.__get_data)
        if r != None:
            upcoming = False
            previous = None

            self.collections = []
            ranking = []
            referee = None

            for item in r['data']['teamCalendar']:
                self.match = item['id']
                r = await self.hass.async_add_executor_job(self.__get_match)
                if r != None:
                    match = r['data']['matchDetail']['location']
                    location='{}\n{} {}\nBelgium'.format(
                        match['address'],
                        match['postalCode'],
                        match['city'],
                    )
                    officials = r['data']['matchDetail']['officials']
                    for x in officials:
                        if x['function'] == 'referee':
                            referee = f"{x['firstName']} {x['lastName']}"
                else:
                    location = None

                naive_dt  = datetime.strptime(item['startTime'], '%Y-%m-%dT%H:%M:%S')
                starttime = naive_dt.replace(tzinfo = ZoneInfo(TZ))
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
                        await self.get_ranking('lastmatch')

                summary = '[' + item['state'] + '] ' + item['homeTeam']['name'] + ' - ' + item['awayTeam']['name']
                description = item['series']['name']

                if self.show_ranking:
                    result = 'No match score'
                    if item['outcome']['homeTeamGoals'] != None:
                        result = 'Goals: ' + str(item['outcome']['homeTeamGoals']) + ' - ' + str(item['outcome']['awayTeamGoals'])
                    if item['outcome']['homeTeamPenaltiesScored'] != None:
                        result += '; Penalties: ' + str(item['outcome']['homeTeamPenaltiesScored']) + ' - '
                        result += str(item['outcome']['awayTeamPenaltiesScored'])
                    description += "; " + result

                collection = {
                    'uid': item['id'],
                    'starttime': starttime,
                    'endtime': endtime,
                    'summary': summary,
                    'location': location,
                    'description': description,
                }

                self.collections.append(collection)
                previous = matchdata

            if not upcoming:
                _LOGGER.debug('previous=last')
                self.matchdata = {
                    'upcoming': None,
                    'lastmatch': previous
                }
                if self.show_ranking:
                    await self.get_ranking('lastmatch')

    async def get_ranking (self, tag):
        _LOGGER.debug('show ranking')

        self.series = self.matchdata[tag]['seriesid']
        r = await self.hass.async_add_executor_job(self.__get_ranking)
        if r != None:
            for rank in r['data']['seriesRankings']['rankings'][0]['teams']:
                rankteam = {'position': rank['position'], 'team': rank['name'], 'id': rank['teamId']}
                self.matchdata[tag]['ranking'].append(rankteam)
                if rank['teamId'] == self.matchdata[tag]['hometeamid']:
                    self.matchdata[tag]['hometeamposition'] = rank['position']
                if rank['teamId'] == self.matchdata[tag]['awayteamid']:
                    self.matchdata[tag]['awayteamposition'] = rank['position']