import json
from pathlib import Path


manifestfile = Path(__file__).parent / "manifest.json"
with open(manifestfile) as json_file:
    manifest_data = json.load(json_file)

DOMAIN  = manifest_data.get("domain")
NAME    = manifest_data.get("name")
VERSION = manifest_data.get("version")

TZ = 'Europe/Brussels'

VARIABLES = {
    'GetTeam':          'teamId',
    'GetTeamCalendar':  'teamId',
    'getClubInfo':      'clubId',
    'GetUpcomingMatch': 'teamId',
    'GetMatchDetail':   'matchId',
    'GetSeriesRankings': 'seriesId',
}

HASHES = {
    'GetTeam':          'e16f98f7985e6b7d6553c8ca60aea3a2b65b6b84dfcabbb02b4ee55261413858',
    'GetTeamCalendar':  '3f0441e6723b9852b4f0cff2c872f4aa674c5de2d23589efc70c7a4ffb7f6383',
    'getClubInfo':      '7c1bd99f0001a20d60208c60d4fb7c99aefdb810b9ee1c4de21a6d6ba4804b58',
    'GetUpcomingMatch': '7e0aa25b6dbe45cede5f1a16320b091be9078a7b9d8cb9cb1402fc35292696fb',
    'GetMatchDetail':   'cd8867b845c206fe7aa75c1ebf7b53cbda0ff030253a45e2e2b4bcc13ee46c9a',
    'GetSeriesRankings': '0a53124a9bc8872b686f22d80fd545622dbaf4b27a7596e1207b097b92c87953',
}

REQUIRED = {
    'GetTeam':          'team',
    'GetTeamCalendar':  'teamCalendar',
    'getClubInfo':      'clubInfo',
    'GetUpcomingMatch': 'upcomingMatch',
    'GetMatchDetail':   'matchDetail',
    'GetSeriesRankings': 'seriesRankings',
}
