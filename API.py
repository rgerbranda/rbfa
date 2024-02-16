from abc import ABC, abstractmethod
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
        self.collector = RecycleApp(self.hass, self.team)

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


class WasteCollector(ABC):

    def __init__(self, hass, team):
        _LOGGER.debug('WasteCollector init')
        self.hass = hass
        self.team = team
        self.collections = []; #WasteCollectionRepository()

    @abstractmethod
    async def update(self):
        pass


class RecycleApp(WasteCollector):

    def __init__(self, hass, team):
        super().__init__(hass, team)
        self.teamname = None
        self.upcoming = None


    def __get_url(self, operation, value):
        self.main_url = 'https://datalake-prod2018.rbfa.be/graphql'
        url = '{}?operationName={}&variables={{"{}":"{}","language":"nl"}}&extensions={{"persistedQuery":{{"version":1,"sha256Hash":"{}"}}}}'.format(
            self.main_url,
            operation,
            VARIABLES[operation],
            value,
            HASHES[operation]
        )
        response = requests.get(url)
        if response.json().get('data') is None:
            #_LOGGER.debug(response.json()['errors'][0]['message'])

            persistent_notification.create(
                self.hass,
                "Error for operation {}: {}".format(operation, response.json()['errors'][0]['message']),
                "RBFA",
                DOMAIN + "_invalid_config",
            )

        if response.json()['data'][REQUIRED[operation]] == None:
            _LOGGER.debug('no results')

            persistent_notification.create(
                self.hass,
                "No results for operation {} with value {}".format(operation, value),
                "RBFA",
                DOMAIN + "_invalid_config",
            )

        return response

    def __get_team(self):
        response = self.__get_url('GetTeam', self.team)
        return response

    def __get_data(self):
        response = self.__get_url('GetTeamCalendar', self.team)
        return response

    def __get_match(self):
        response = self.__get_url('GetMatchDetail', self.match)
        return response

    def __get_next(self):
        response = self.__get_url('GetUpcomingMatch', self.team)
        return response

    async def update(self):
        _LOGGER.debug('Updating Waste collection dates using Rest API')

        try:
            tz = pytz.timezone("Europe/Brussels")

            rm = await self.hass.async_add_executor_job(self.__get_next)
            item = rm.json()['data']['upcomingMatch']

            self.match = item['id']
            rc = await self.hass.async_add_executor_job(self.__get_match)
            match = rc.json()['data']['matchDetail']['location']
            location='{}\n{}\n{} {}'.format(
                match['name'],
                match['address'],
                match['postalCode'],
                match['city'],
            )

            naive_dt  = datetime.strptime(item['startTime'], '%Y-%m-%dT%H:%M:%S')
            starttime = tz.localize(naive_dt, is_dst=None)

            self.upcoming = WasteCollection.create(
                uid=item['id'],
                date=starttime,
                summary=item['homeTeam']['name'] + ' - ' + item['awayTeam']['name'],
                location=location,
                description=''
            )


            rt = await self.hass.async_add_executor_job(self.__get_team)
            teamdata = rt.json()
            self.teamname = teamdata['data']['team']['name'] + ' - ' + teamdata['data']['team']['clubName']

            r = await self.hass.async_add_executor_job(self.__get_data)
            if r.status_code != 200:
                _LOGGER.error('Invalid response from server for collection data')
                return
            response = r.json()

            if not response:
                _LOGGER.error('No Waste data found!')
                return

            self.collections = []
            for item in response['data']['teamCalendar']:
                self.match = item['id']
                rc = await self.hass.async_add_executor_job(self.__get_match)
                match = rc.json()['data']['matchDetail']['location']
                location='{}\n{}\n{} {}'.format(
                    match['name'],
                    match['address'],
                    match['postalCode'],
                    match['city'],
                )

                if not item['startTime']:
                    continue

                naive_dt  = datetime.strptime(item['startTime'], '%Y-%m-%dT%H:%M:%S')
                starttime = tz.localize(naive_dt, is_dst=None)
                description = None

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

        except requests.exceptions.RequestException as exc:
            _LOGGER.error('Error occurred while fetching data: %r', exc)
            return False


def get_wastedata_from_config(hass, config):
    _LOGGER.debug("Get Rest API retriever")
    team = config.get(CONF_TEAM)
    update_interval = config.get(CONF_UPDATE_INTERVAL)

    if not team:
        persistent_notification.create(
            hass,
            "Config invalid! Team id is required",
            "RBFA",
            NOTIFICATION_ID + "_invalid_config",
        )
        return


    td = TeamData(
        hass,
        team,
        update_interval,
    )
  #  _LOGGER.debug('teamname: %r', td.collections)
    return td
