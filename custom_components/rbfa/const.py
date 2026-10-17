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
    'GetTeamCalendar':  '3f0441e6723b9852b4f0cff2c872f4aa674c5de2d23589efc70c7a4ffb7f6383',
    'GetMatchDetail':   'cd8867b845c206fe7aa75c1ebf7b53cbda0ff030253a45e2e2b4bcc13ee46c9a',
    'getSeriesAndRankingsQuery': 'ace90f0250b37a504282e27289c62ea6a3f444ef8821f663bd1faa8e3689e358',
}

REQUIRED = {
    'GetTeam':          'team',
    'GetTeamCalendar':  'teamCalendar',
    'GetMatchDetail':   'matchDetail',
    'getSeriesAndRankingsQuery': 'teamSeriesAndRankings',
}
