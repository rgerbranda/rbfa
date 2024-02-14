from datetime import timedelta
import voluptuous as vol

import homeassistant.helpers.config_validation as cv
from homeassistant.const import CONF_RESOURCES

DOMAIN = "rbfa"

SCHEDULE_UPDATE_INTERVAL = timedelta(minutes=5) # hours=12

CONF_ID = "id"
CONF_TEAM = "team"
CONF_WASTE_COLLECTOR = 'wastecollector'
CONF_CITY_NAME = 'cityname'
CONF_STREET_NAME = 'streetname'
CONF_STREET_NUMBER = 'streetnumber'
CONF_ADDRESS_ID = 'addressid'
CONF_UPCOMING = 'upcomingsensor'
CONF_DATE_ONLY = 'dateonly'
CONF_DATE_OBJECT = 'dateobject'
CONF_NAME = 'name'
CONF_NAME_PREFIX = 'nameprefix'
CONF_BUILT_IN_ICONS = 'builtinicons'
CONF_BUILT_IN_ICONS_NEW = 'builtiniconsnew'
CONF_DISABLE_ICONS = 'disableicons'
CONF_TRANSLATE_DAYS = 'dutch'
CONF_DAY_OF_WEEK = 'dayofweek'
CONF_DAY_OF_WEEK_ONLY = 'dayofweekonly'
CONF_ALWAYS_SHOW_DAY = 'alwaysshowday'
CONF_PRINT_AVAILABLE_WASTE_TYPES = 'printwastetypes'
CONF_UPDATE_INTERVAL = 'updateinterval'
CONF_CUSTOMER_ID = 'customerid'

PLATFORM_SCHEMA = vol.Schema(
    {
        vol.Required(CONF_RESOURCES, default=[]): cv.ensure_list,
        vol.Required(CONF_TEAM, default="300872"): cv.string,
        vol.Required(CONF_STREET_NUMBER, default="1"): cv.string,
        vol.Optional(CONF_CITY_NAME, default=""): cv.string,
        vol.Optional(CONF_STREET_NAME, default=""): cv.string,
        vol.Optional(CONF_ADDRESS_ID, default=""): cv.string,
        vol.Optional(CONF_WASTE_COLLECTOR, default="Cure"): cv.string,
        vol.Optional(CONF_UPCOMING, default=False): cv.boolean,
        vol.Optional(CONF_DATE_ONLY, default=False): cv.boolean,
        vol.Optional(CONF_DATE_OBJECT, default=False): cv.boolean,
        vol.Optional(CONF_NAME, default=""): cv.string,
        vol.Optional(CONF_NAME_PREFIX, default=True): cv.boolean,
        vol.Optional(CONF_BUILT_IN_ICONS, default=False): cv.boolean,
        vol.Optional(CONF_BUILT_IN_ICONS_NEW, default=False): cv.boolean,
        vol.Optional(CONF_DISABLE_ICONS, default=False): cv.boolean,
        vol.Optional(CONF_TRANSLATE_DAYS, default=False): cv.boolean,
        vol.Optional(CONF_DAY_OF_WEEK, default=True): cv.boolean,
        vol.Optional(CONF_DAY_OF_WEEK_ONLY, default=False): cv.boolean,
        vol.Optional(CONF_ALWAYS_SHOW_DAY, default=False): cv.boolean,
        vol.Optional(CONF_PRINT_AVAILABLE_WASTE_TYPES, default=False): cv.boolean,
        vol.Optional(CONF_UPDATE_INTERVAL, default=0): cv.positive_int,
        vol.Optional(CONF_CUSTOMER_ID, default=""): cv.string,
    }, extra=vol.ALLOW_EXTRA  # Allow extra required due when validating config as sensor (platform key is added to config)
)

VARIABLES = {
    'GetTeam':         'teamId',
    'GetTeamCalendar': 'teamId',
    'getClubInfo':     'clubId',
    'GetUpcomingMatch': 'teamId',
}

HASHES = {
    'GetTeam':         '66888f01d376a6484c0c6824e5f266cb3c3513ab83964e50e0a7c30b8fddb4fa',
    'GetTeamCalendar': '63e80713dbe3f057aafb53348ebb61a2c52d3d6cda437d8b7e7bd78191990487',
    'getClubInfo':     'd7160a293f090e50f5ef52b1459530e9a11b36bd75c3ee1bcfbd9057889e009f',
    'GetUpcomingMatch': '82e90ddafc6823e8cc5c5d876073e0e01c261f6844ad8e8bab5b8fd0b17da5e1',
}

ATTR_WASTE_COLLECTOR = 'Wastecollector'
ATTR_UPCOMING_DAY = 'Upcoming_day'
ATTR_UPCOMING_WASTE_TYPES = 'Upcoming_waste_types'
ATTR_HIDDEN = 'Hidden'
ATTR_SORT_DATE = 'Sort_date'
ATTR_DAYS_UNTIL = 'Days_until'

NOTIFICATION_ID = "Afvalbeheer"

DUTCH_TRANSLATION_DAYS = {
    'Monday':       'Maandag',
    'Tuesday':      'Dinsdag',
    'Wednesday':    'Woensdag',
    'Thursday':     'Donderdag',
    'Friday':       'Vrijdag',
    'Saturday':     'Zaterdag',
    'Sunday':       'Zondag',
}

DUTCH_TRANSLATION_DAYS_SHORT = {
    'Mon':  'Maa',
    'Tue':  'Din',
    'Wed':  'Woe',
    'Thu':  'Don',
    'Fri':  'Vri',
    'Sat':  'Zat',
    'Sun':  'Zon',
}

DUTCH_TRANSLATION_MONTHS = {
    'January':      'januari',
    'February':     'februari',
    'March':        'maart',
    'April':        'april',
    'May':          'mei',
    'June':         'juni',
    'July':         'juli',
    'August':       'augustus',
    'September':    'september',
    'October':      'oktober',
    'November':     'november',
    'December':     'december'
}

DUTCH_TRANSLATION_MONTHS_SHORT = {
    'Jan':  'jan',
    'Feb':  'feb',
    'Mar':  'mrt',
    'Apr':  'apr',
    'May':  'mei',
    'Jun':  'jun',
    'Jul':  'jul',
    'Aug':  'aug',
    'Sept': 'sep',
    'Oct':  'okt',
    'Nov':  'nov',
    'Dec':  'dec',
}
