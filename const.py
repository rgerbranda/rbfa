from datetime import timedelta
import voluptuous as vol

import homeassistant.helpers.config_validation as cv
from homeassistant.const import CONF_RESOURCES

DOMAIN = "rbfa"

SCHEDULE_UPDATE_INTERVAL = timedelta(minutes=5) # hours=12

CONF_TEAM = 'team'
CONF_UPDATE_INTERVAL = 'updateinterval'

PLATFORM_SCHEMA = vol.Schema(
    {
        vol.Required(CONF_RESOURCES, default=[]): cv.ensure_list,
        vol.Required(CONF_TEAM, default=""): cv.string,
        vol.Optional(CONF_UPDATE_INTERVAL, default=0): cv.positive_int,
    }, extra=vol.ALLOW_EXTRA  # Allow extra required due when validating config as sensor (platform key is added to config)
)

VARIABLES = {
    'GetTeam':          'teamId',
    'GetTeamCalendar':  'teamId',
    'getClubInfo':      'clubId',
    'GetUpcomingMatch': 'teamId',
    'GetMatchDetail':   'matchId',
}

HASHES = {
    'GetTeam':          '66888f01d376a6484c0c6824e5f266cb3c3513ab83964e50e0a7c30b8fddb4fa',
    'GetTeamCalendar':  '63e80713dbe3f057aafb53348ebb61a2c52d3d6cda437d8b7e7bd78191990487',
    'getClubInfo':      'd7160a293f090e50f5ef52b1459530e9a11b36bd75c3ee1bcfbd9057889e009f',
    'GetUpcomingMatch': '82e90ddafc6823e8cc5c5d876073e0e01c261f6844ad8e8bab5b8fd0b17da5e1',
    'GetMatchDetail':   '44adcb765b9b7159616dc339e33fcefa5b3aaadcc32a06cb6eece5855b1830c2',
}

REQUIRED = {
    'GetTeam':          'team',
    'GetTeamCalendar':  'teamCalendar',
    'getClubInfo':      'clubInfo',
    'GetUpcomingMatch': 'upcomingMatch',
    'GetMatchDetail':   'matchDetail',
}
