Add the calendar of your soccer team to Home Assistant. The data is gathered from the Royal Belgian Football Association ([RBFA](https://www.rbfa.be/)) website in cooporation with Association Clubs Francophones de Football ([ACFF](https://www.acff.be/)) and [Voetbal Vlaanderen](https://www.voetbalvlaanderen.be/).

[![Hacs validation](https://github.com/rgerbranda/rbfa/actions/workflows/validate.yaml/badge.svg)](https://github.com/rgerbranda/rbfa/actions/workflows/validate.yaml)
[![Hassfest validation](https://github.com/rgerbranda/rbfa/actions/workflows/hassfest.yaml/badge.svg)](https://github.com/rgerbranda/rbfa/actions/workflows/hassfest.yaml)

[![Open your Home Assistant instance and open the repository inside the Home Assistant Community Store.](https://my.home-assistant.io/badges/hacs_repository.svg?style=flat-square)](https://my.home-assistant.io/redirect/hacs_repository/?owner=rgerbranda&repository=rbfa&category=integration)

Configuration
-
![Example](https://github.com/rgerbranda/rbfa/blob/main/images/configuration.png)

The team number is the number after 'ploeg': https://www.rbfa.be/nl/club/2438/ploeg/300872/overzicht

Example card
-
![Example](https://github.com/rgerbranda/rbfa/blob/main/images/example.png)

Match card
-
<img src="https://github.com/rgerbranda/rbfa/blob/main/images/match_sheet.png" alt="Match card" width=528>

The match card is based on the [Markdown card](https://www.home-assistant.io/dashboards/markdown/).

Add a Markdown card with the following content. Note: replace the names of the sensors by the ones in your configuration.

```
<table width="100%">
<tr>
<th colspan=2>{{states('sensor.reeks')}}</th>
</tr>
<tr>
<th colspan=2>
<a href="https://www.rbfa.be/nl/wedstrijd/{{ states('sensor.wedstrijd_id') }}">{{as_timestamp(states('sensor.start'))|timestamp_custom('%d-%m-%y om %H:%M uur')}}</a></th>
</tr>
<tr>
<td align="center"><img src="{{state_attr('sensor.thuis','entity_picture')}}" width="64"></td>
<td align="center"><img src="{{state_attr('sensor.uit','entity_picture')}}" width="64"></td>
</tr>
<tr>
<td align="center">{{states('sensor.thuis')}}</td>
<td align="center">{{states('sensor.uit')}}</td>
</tr>
<tr>
<td align="center">Positie: {{state_attr('sensor.thuis','position')}}</td>
<td align="center">Positie: {{state_attr('sensor.uit', 'position')}}</td>
</tr>
<tr>
<td align="center" colspan="2">{{states('sensor.locatie') | replace("\n",", ")}}</td>
</tr>
<tr>
<td align="center" colspan="2">Scheidsrechter: {{states('sensor.scheidsrechter') }}</td>
</table>
```


Ranking card
-

```
type: markdown
title: Ranking
content: >-
  {% set sensor = "sensor.result_279669" %}

  {{state_attr(sensor, "Series") }}

  -

  {% if state_attr(sensor, "Ranking") != None %}
  {% for item in state_attr(sensor, "Ranking") %}

  {{ item.position }}. {% if item.id == state_attr(sensor, "TeamID") %}**{{item.team}}**
  {% else %}{{item.team}}
  {% endif %}
  {% endfor %} 
  {% endif %}
```

<img src="https://github.com/rgerbranda/rbfa/blob/main/images/ranking.png" alt="Ranking" width=528>

<img src="https://github.com/home-assistant/brands/blob/c359584cf6719b89aee0428cdb55da55c5b34593/custom_integrations/rbfa/logo.png" alt="Royal Belgian Football Association" height=128>
