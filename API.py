from abc import ABC, abstractmethod
import logging
from datetime import datetime
from datetime import timedelta
import json
import requests
import re
import uuid
import pytz

from homeassistant.helpers.event import async_track_point_in_utc_time
from homeassistant.util import dt as dt_util
from homeassistant.components import persistent_notification

from .const import *


_LOGGER = logging.getLogger(__name__)


class WasteCollectionRepository(object):

    def __init__(self):
        self.collections = []

    def __iter__(self):
        for collection in self.collections:
            yield collection

    def __len__(self):
        return len(self.collections)

    def add(self, collection):
        self.collections.append(collection)

    def remove_all(self):
        self.collections = []

    def get_sorted(self):
        return sorted(self.collections, key=lambda x: x.date)

    def get_by_date(self, date, waste_types=None):
        if waste_types:
            return list(filter(lambda x: x.date.date() == date.date() and x.waste_type in waste_types, self.get_sorted()))
        else:
            return list(filter(lambda x: x.date.date() == date.date(), self.get_sorted()))
    
    def get_available_waste_types(self):
        possible_waste_types = []
        for collection in self.collections:
            if collection.waste_type not in possible_waste_types:
                possible_waste_types.append(collection.waste_type)
        return sorted(possible_waste_types, key=str.lower)


class WasteCollection(object):

    def __init__(self):
        self.uid = None
        self.date = None
        self.waste_type = None
        self.location = None
        self.icon_data = None

    @classmethod
    def create(cls, uid, date, waste_type, location, icon_data=None):
        collection = cls()
        collection.uid = uid
        collection.date = date
        collection.waste_type = waste_type
        collection.location = location
        collection.icon_data = icon_data
        _LOGGER.debug('type: %r', waste_type)
        return collection


class WasteData(object):

    def __init__(self, hass, waste_collector, city_name, postcode, street_name, street_number, suffix, address_id, print_waste_type, update_interval, customer_id):
        self.hass = hass
        self.waste_collector = waste_collector
        self.city_name = city_name
        self.postcode = postcode
        self.street_name = street_name
        self.street_number = street_number
        self.suffix = suffix
        self.address_id = address_id
        self.print_waste_type = print_waste_type
        self.collector = None
        self.update_interval = update_interval
        self.customer_id = customer_id
        self.__select_collector()

    def __select_collector(self):
        if self.waste_collector == "recycleapp":
            self.collector = RecycleApp(self.hass, self.waste_collector, self.postcode, self.street_name, self.street_number, self.suffix)
        else:
            persistent_notification.create(
                self.hass,
                'Waste collector "{}" not found!'.format(self.waste_collector),
                'Afvalwijzer' + " " + self.waste_collector, 
                NOTIFICATION_ID + "_collectornotfound_" + self.waste_collector)

    async def schedule_update(self, interval):
        nxt = dt_util.utcnow() + interval
        async_track_point_in_utc_time(self.hass, self.async_update, nxt)

    async def async_update(self, *_):
        await self.collector.update()
        if self.update_interval != 0:
            await self.schedule_update(timedelta(hours=self.update_interval))
        else:
            await self.schedule_update(SCHEDULE_UPDATE_INTERVAL)
        if self.print_waste_type:
            persistent_notification.create(
                self.hass,
                'Available waste types: ' + ', '.join(self.collector.collections.get_available_waste_types()),
                'Afvalwijzer' + " " + self.waste_collector, 
                NOTIFICATION_ID + "_availablewastetypes_" + self.waste_collector)
            self.print_waste_type = False

    @property
    def collections(self):
        return self.collector.collections


class WasteCollector(ABC):

    def __init__(self, hass, waste_collector, postcode, street_number, suffix):
        self.hass = hass
        self.waste_collector = waste_collector
        self.postcode = postcode
        self.street_number = street_number
        self.suffix = suffix
        self.collections = WasteCollectionRepository()

    @abstractmethod
    async def update(self):
        pass

    def map_waste_type(self, name):
        for from_type, to_type in self.WASTE_TYPE_MAPPING.items():
            if from_type.lower() in name.lower():
                return to_type
        return name.lower()




class RecycleApp(WasteCollector):

    _LOGGER.debug("app found")
    
    def __init__(self, hass, waste_collector, postcode, street_name, street_number, suffix):
        super().__init__(hass, waste_collector, postcode, street_number, suffix)
        self.main_url = 'https://datalake-prod2018.rbfa.be/graphql'

        ##
        self.operationName = "GetTeamCalendar" #"GetUpcomingMatch"
        self.variables = '{"teamId":"300872","language":"nl"}'
        self.extensions = '{"persistedQuery":{"version":1,"sha256Hash":"63e80713dbe3f057aafb53348ebb61a2c52d3d6cda437d8b7e7bd78191990487"}}'
        self.club = ''
               

    def __get_data(self):
        response = requests.get("{}?operationName={}&variables={}&extensions={}".format(self.main_url, self.operationName, self.variables, self.extensions) )
    #    _LOGGER.debug('status code: %r', response.status_code)
        return response

    def __get_club(self):
        variables = '{"clubId":"' + self.club + '","language":"nl"}'
        extensions = '{"persistedQuery":{"version":1,"sha256Hash":"d7160a293f090e50f5ef52b1459530e9a11b36bd75c3ee1bcfbd9057889e009f"}}'
        url = "{}?operationName={}&variables={}&extensions={}".format(self.main_url, 'getClubInfo', variables, extensions)
        _LOGGER.debug('url: %r', url)
        response = requests.get(url )
        return response

    async def update(self):
        _LOGGER.debug('Updating Waste collection dates using Rest API')

        try:
            r = await self.hass.async_add_executor_job(self.__get_data)
            if r.status_code != 200:
                _LOGGER.error('Invalid response from server for collection data')
                return
            response = r.json()

            if not response:
                _LOGGER.error('No Waste data found!')
                return

            self.collections.remove_all()

            for item in response['data']['teamCalendar']:
                self.club = item['homeTeam']['clubId']

                rc = await self.hass.async_add_executor_job(self.__get_club)
                club = rc.json()
                _LOGGER.debug(club['data']['clubInfo']['venue']['streetName'])
                if not item['startTime']:
                    continue

                naive_dt  = datetime.strptime(item['startTime'], '%Y-%m-%dT%H:%M:%S')
                tz = pytz.timezone("Europe/Brussels")
                starttime = tz.localize(naive_dt, is_dst=None)

                _LOGGER.debug(starttime)

                collection = WasteCollection.create(
                    uid=item['id'],
                    date=starttime,
                    waste_type=item['homeTeam']['name'] + ' - ' + item['awayTeam']['name'],
                    location=club['data']['clubInfo']['venue']['streetName']
                )
                self.collections.add(collection)

        except requests.exceptions.RequestException as exc:
            _LOGGER.error('Error occurred while fetching data: %r', exc)
            return False


def get_wastedata_from_config(hass, config):
    _LOGGER.debug("Get Rest API retriever")
    city_name = config.get(CONF_CITY_NAME)
    postcode = config.get(CONF_POSTCODE)
    street_name = config.get(CONF_STREET_NAME)
    street_number = config.get(CONF_STREET_NUMBER)
    suffix = config.get(CONF_SUFFIX)
    address_id = config.get(CONF_ADDRESS_ID)
    waste_collector = config.get(CONF_WASTE_COLLECTOR).lower()
    print_waste_type = config.get(CONF_PRINT_AVAILABLE_WASTE_TYPES)
    update_interval = config.get(CONF_UPDATE_INTERVAL)
    customer_id = config.get(CONF_CUSTOMER_ID)
    config["id"] = _format_id(waste_collector, postcode, street_number)

    if waste_collector in DEPRECATED_AND_NEW_WASTECOLLECTORS:
        persistent_notification.create(
            hass,
            "Update your config to use {}! You are still using {} as a waste collector, which is deprecated. Check your automations and lovelace config, as the sensor names may also be changed!".format(
                DEPRECATED_AND_NEW_WASTECOLLECTORS[waste_collector], waste_collector
            ),
            "Afvalbeheer" + " " + waste_collector,
            NOTIFICATION_ID + "_update_config_" + waste_collector,
        )
        waste_collector = DEPRECATED_AND_NEW_WASTECOLLECTORS[waste_collector]

    if waste_collector in ["limburg.net", "recycleapp"] and not street_name:
        persistent_notification.create(
            hass,
            "Config invalid! Streetname is required for {}".format(waste_collector),
            "Afvalbeheer" + " " + waste_collector,
            NOTIFICATION_ID + "_invalid_config_" + waste_collector,
        )
        return

    return WasteData(
        hass,
        waste_collector,
        city_name,
        postcode,
        street_name,
        street_number,
        suffix,
        address_id,
        print_waste_type,
        update_interval,
        customer_id,
    )


def _format_id(waste_collector, postcode, house_number):
    return waste_collector + "-" + postcode + "-" + str(house_number)
