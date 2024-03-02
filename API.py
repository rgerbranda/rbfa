import logging
from datetime import datetime
from datetime import timedelta
import json
import requests
import pytz

from homeassistant.helpers.event import async_track_point_in_utc_time
from homeassistant.util import dt as dt_util
from homeassistant.components import persistent_notification

from .const import *


_LOGGER = logging.getLogger(__name__)

class WasteCollection(object):

    def __init__(self):
        self.uid = None
        self.date = None
        self.summary = None
        self.location = None
        self.description = None



    @classmethod
    def create(cls, uid, date, summary, location, description):
        collection = cls()
        collection.uid = uid
        collection.date = date
        collection.summary = summary
        collection.location = location
        collection.description = description
        return collection


class TeamData(object):

    def __init__(self, hass, team, update_interval):
        self.hass = hass
        self.team = team
        self.update_interval = update_interval
        self.collector = RecycleApp(self.hass, team)

    async def schedule_update(self, interval):
        nxt = dt_util.utcnow() + interval
  #      _LOGGER.debug('schedule_update %r', nxt)
        async_track_point_in_utc_time(self.hass, self.async_update, nxt)

    async def async_update(self, *_):
        _LOGGER.debug('async_update')
        await self.collector.update()
        if self.update_interval != 0:
            await self.schedule_update(timedelta(hours=self.update_interval))
        else:
            await self.schedule_update(SCHEDULE_UPDATE_INTERVAL)

    @property
    def collections(self):
        return self.collector.collections

    def teamname(self):
        return self.collector.teamname

    def upcoming(self):
        return self.collector.upcoming


class RecycleApp(object):

    def __init__(self, hass, team):
        self.teamname = None
        self.upcoming = None
        self.hass = hass
        self.team = team
        self.collections = [];

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
#            _LOGGER.debug(url)
            response = requests.get(url)
            if response.status_code != 200:
                _LOGGER.debug('Invalid response from server for collection data')
                return

            rj = response.json()
            if rj.get('data') is None:
                #_LOGGER.debug(response.json()['errors'][0]['message'])
                persistent_notification.create(
                    self.hass,
                    "Error for operation {}: {}".format(operation, rj['errors'][0]['message']),
                    DOMAIN,
                    "{}_invalid_config_{}_{}".format(DOMAIN, operation, value)
                )

            elif rj['data'][REQUIRED[operation]] == None:
                _LOGGER.debug('no results')
                persistent_notification.create(
                    self.hass,
                    "No results for operation {} with value {}".format(operation, value),
                    DOMAIN,
                    "{}_invalid_config_{}_{}".format(DOMAIN, operation, value)
                )

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

    async def update(self):
        _LOGGER.debug('Updating Waste collection dates using Rest API')

   #     try:
        tz = pytz.timezone("Europe/Brussels")
        today = datetime.now(pytz.utc)

        r = await self.hass.async_add_executor_job(self.__get_team)
        if r != None:
            teamdata = r['data']['team']
            self.teamname = teamdata['name'] + ' - ' + teamdata['clubName']

        r = await self.hass.async_add_executor_job(self.__get_data)
        if r != None:
    #        if r.status_code != 200:
    #            _LOGGER.error('Invalid response from server for collection data')
    #            return

    #        if not response:
    #            _LOGGER.error('No Waste data found!')
    #            return

            upcoming = None

            self.collections = []
            for item in r['data']['teamCalendar']:
                self.match = item['id']
                r = await self.hass.async_add_executor_job(self.__get_match)
                if r != None:
                    match = r['data']['matchDetail']['location']
                    location='{}\n{}\n{} {}'.format(
                        match['name'],
                        match['address'],
                        match['postalCode'],
                        match['city'],
                    )
                else:
                    location = None

       #         if not item['startTime']:
       #             continue

                naive_dt  = datetime.strptime(item['startTime'], '%Y-%m-%dT%H:%M:%S')
                starttime = tz.localize(naive_dt, is_dst=None)
                description = None

                if starttime >= today and self.upcoming == None:
                    self.upcoming = {
                        'uid': item['id'],
                        'date': starttime,
                        'location': location,
                        'hometeam': item['homeTeam']['name'],
                        'homelogo': item['homeTeam']['logo'],
                        'awayteam': item['awayTeam']['name'],
                        'awaylogo': item['awayTeam']['logo'],
                    }

                if item['outcome']['homeTeamGoals'] != None:
                    description='Result: ' + str(item['outcome']['homeTeamGoals']) + ' - ' + str(item['outcome']['awayTeamGoals'])

                collection = WasteCollection.create(
                    uid=item['id'],
                    date=starttime,
                    summary=item['homeTeam']['name'] + ' - ' + item['awayTeam']['name'],
                    location=location,
                    description=description
                )
                self.collections.append(collection)


def get_wastedata_from_config(hass, config):
    _LOGGER.debug("Get Rest API retriever")
    team = config.get(CONF_TEAM)
    update_interval = config.get(CONF_UPDATE_INTERVAL)

    td = TeamData(
        hass,
        team,
        update_interval,
    )
  #  _LOGGER.debug('teamname: %r', td.collections)
    return td
