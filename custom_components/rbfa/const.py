from datetime import timedelta, time
import voluptuous as vol

import homeassistant.helpers.config_validation as cv
from homeassistant.const import CONF_RESOURCES

import json
from pathlib import Path


manifestfile = Path(__file__).parent / "manifest.json"
with open(manifestfile) as json_file:
    manifest_data = json.load(json_file)

DOMAIN  = manifest_data.get("domain")
NAME    = manifest_data.get("name")
VERSION = manifest_data.get("version")

SCHEDULE_UPDATE_INTERVAL = timedelta(minutes=5) # hours=12

CONF_TEAM = 'team'
CONF_UPDATE_INTERVAL = 'updateinterval'

TZ = 'Europe/Brussels'
START = time( 8, 30)
END   = time(22, 30)

PLATFORM_SCHEMA = vol.Schema(
    {
        vol.Required(CONF_TEAM, default=""): cv.string,
        vol.Optional(CONF_UPDATE_INTERVAL, default=0): cv.positive_int,
    }, extra=vol.ALLOW_EXTRA  # Allow extra required due when validating config as sensor (platform key is added to config)
)
#        vol.Required(CONF_RESOURCES, default=[]): cv.ensure_list,

VARIABLES = {
    'GetTeam':          'teamId',
    'GetTeamCalendar':  'teamId',
    'getClubInfo':      'clubId',
    'GetUpcomingMatch': 'teamId',
    'GetMatchDetail':   'matchId',
    'GetSeriesRankings': 'seriesId',
}

HASHES = {
    'GetTeam':          '66888f01d376a6484c0c6824e5f266cb3c3513ab83964e50e0a7c30b8fddb4fa',
    'GetTeamCalendar':  '63e80713dbe3f057aafb53348ebb61a2c52d3d6cda437d8b7e7bd78191990487',
    'getClubInfo':      'd7160a293f090e50f5ef52b1459530e9a11b36bd75c3ee1bcfbd9057889e009f',
    'GetUpcomingMatch': '82e90ddafc6823e8cc5c5d876073e0e01c261f6844ad8e8bab5b8fd0b17da5e1',
    'GetMatchDetail':   '44adcb765b9b7159616dc339e33fcefa5b3aaadcc32a06cb6eece5855b1830c2',
    'GetSeriesRankings': '7d13cbe2a17d6d5e7a3a0c1039d09c2e0ca326a454ec6fd2a471aa1fa2cf73e5',
}

REQUIRED = {
    'GetTeam':          'team',
    'GetTeamCalendar':  'teamCalendar',
    'getClubInfo':      'clubInfo',
    'GetUpcomingMatch': 'upcomingMatch',
    'GetMatchDetail':   'matchDetail',
    'GetSeriesRankings': 'seriesRankings',
}
