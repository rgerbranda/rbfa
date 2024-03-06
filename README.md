Add the calendar of your football team to Home Assistant. The data is gathered from the RBFA

Example configuration.yaml

The team number is the number after 'ploeg': https://www.rbfa.be/nl/club/2438/ploeg/300872/overzicht

```
rbfa:
  - team: 300872
  - team: 281473
```
![Example](https://github.com/rgerbranda/rbfa/blob/ef912db0d17b837fed74d85d1c5b003a15997946/images/example.png)

Ranking card
-

      - type: markdown
        title: Ranking
        content: >-
          {% set sensor = "sensor.result_281449" %}

          {{state_attr(sensor, "Series") }}
          -
          {% if state_attr(sensor, "Ranking") != None %}
          {% for item in state_attr(sensor, "Ranking") %}{{item.position}}. {% if item.id == state_attr(sensor, "TeamID") %}**{{item.team}}**
          {% else %}{{item.team}}
          {% endif %}
          {%- endfor %} 
          {% endif %}


[![github release](https://img.shields.io/github/v/release/rgerbranda/rbfa?logo=github)](https://github.com/rgerbranda/rbfa/releases)
[![github release date](https://img.shields.io/github/release-date/rgerbranda/rbfa)](https://github.com/rgerbranda/rbfa/releases)

<img src="https://github.com/home-assistant/brands/blob/c359584cf6719b89aee0428cdb55da55c5b34593/custom_integrations/rbfa/logo.png" alt="Royal Belgian Football Association" height=128>
