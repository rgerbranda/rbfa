import json
from pathlib import Path


manifestfile = Path(__file__).parent / "manifest.json"
with open(manifestfile) as json_file:
    manifest_data = json.load(json_file)

DOMAIN  = manifest_data.get("domain")
# NAME    = manifest_data.get("name")
# VERSION = manifest_data.get("version")

TZ = 'Europe/Brussels'

VARIABLES = {
    'GetTeam':          'teamId',
    'GetTeamCalendar':  'teamId',
    'GetMatchDetail':   'matchId',
    'getSeriesAndRankingsQuery': 'teamId',
}

HASHES = {
    'GetTeam':          'e16f98f7985e6b7d6553c8ca60aea3a2b65b6b84dfcabbb02b4ee55261413858',
    'GetTeamCalendar':  '5cc5fac5f4819eb5aba7e1961e46bb61105a99f234141f0f862a344bdc17b164',
    'GetMatchDetail':   'e4194e20528d04a046bd71ea20a044dbd445144b1104f5e6f5992cfdcf43a793',
    'getSeriesAndRankingsQuery': '18a00fb0be3d9ac68294cba3c1542b0f48e52a1de5e792a158557f4ce78b9cf1',
}

REQUIRED = {
    'GetTeam':          'team',
    'GetTeamCalendar':  'teamCalendar',
    'GetMatchDetail':   'matchDetail',
    'getSeriesAndRankingsQuery': 'teamSeriesAndRankings',
}
