Add the calendar of your soccer team to Home Assistant. The data is gathered from the Royal Belgian Football Association ([RBFA](https://www.rbfa.be/)) website in cooperation with Association Clubs Francophones de Football ([ACFF](https://www.acff.be/)) and [Voetbal Vlaanderen](https://www.voetbalvlaanderen.be/).

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

## Custom dashboard cards

Two custom cards provide three dashboard views: the upcoming match, the previous match and the rankings. They follow your Home Assistant profile language and support Dutch, English, French and Portuguese.

### Install the cards

Copy `www/match-card.js` and `www/ranking-card.js` from this repository into the `www` folder of your Home Assistant configuration directory (`/config/www` for a container installation).

In **Settings → Dashboards → ⋮ → Resources**, add both URLs as **JavaScript module** resources:

```text
/local/match-card.js?v=1
```

```text
/local/ranking-card.js?v=1
```

If Resources is hidden, enable Advanced mode in your user profile. Reload your browser after adding the resources. When updating the files, increase the `v` value and reload again to refresh the browser cache.

Alternatively, use these URLs to load the cards from GitHub through jsDelivr:

```text
https://cdn.jsdelivr.net/gh/rgerbranda/rbfa@main/www/match-card.js
```

```text
https://cdn.jsdelivr.net/gh/rgerbranda/rbfa@main/www/ranking-card.js
```

Register each card only once: choose either its local URL or its CDN URL. The CDN requires internet access and updates to `main` may be delayed by caching. Replace `@main` with a release tag to use a fixed version.

### Upcoming match

<img src="images/upcoming-match.png" alt="Upcoming match card with countdown, teams, venue and referee" width="528">

Add a Manual card with the following YAML. Replace `374444` with the team ID entered when configuring the integration:

```yaml
type: custom:match-card
baseid: "374444"
tag: upcoming
```

The card automatically finds the match sensors using their `baseid`, `tag` and `field` attributes. It shows a countdown or match status, team logos, venue, navigation links and referee. Scores and penalty shoot-out results appear when supplied by the integration. Team positions are retrieved from the matching series in the rankings sensor, when available.

### Previous match

<img src="images/last-match.png" alt="Previous match card with result, teams, venue and referee" width="528">

Use the same team ID with `tag: lastmatch`:

```yaml
type: custom:match-card
baseid: "374444"
tag: lastmatch
```

This view shows the previous match and its available result, without a countdown.

For either match view, you can optionally set `langrbfaurl: nl`, `fr` or `en` to choose the language of the RBFA match-details link. This does not change the language of the card itself.

### Rankings

<img src="images/ranking.png" alt="Ranking card highlighting the configured team" width="528">

Replace `sensor.rangschikkingen` with the actual entity ID of your rankings sensor:

```yaml
type: custom:ranking-card
entity: sensor.rangschikkingen
```

The card displays the first available series and highlights your configured team. To select another series, add its `seriesId` as `series_id`:

```yaml
type: custom:ranking-card
entity: sensor.rangschikkingen
series_id: CHP_131142
```

Find the rankings sensor and its `series` attribute in **Developer tools → States**. Use the exact `seriesId` from your sensor; `CHP_131142` is an example. Each series contains its name and ranking. Match-card positions use the same series ID to avoid mixing rankings from different competitions.

Addresses are converted to coordinates using [Nominatim](https://nominatim.org/).
Location data: © [OpenStreetMap contributors](https://www.openstreetmap.org/copyright),
available under the [ODbL](https://opendatacommons.org/licenses/odbl/1-0/).

<img src="https://github.com/home-assistant/brands/blob/c359584cf6719b89aee0428cdb55da55c5b34593/custom_integrations/rbfa/logo.png" alt="Royal Belgian Football Association" height=128>
