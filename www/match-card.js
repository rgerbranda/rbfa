class MatchCard extends HTMLElement {
  constructor() {
    super();
    this.attachShadow({ mode: "open" });
  }

  setConfig(config) {
    const baseId = config?.baseid;
    if (!['string', 'number'].includes(typeof baseId) || !String(baseId).trim()) {
      throw new Error('Configure baseid for match-card');
    }
    const tag = config?.tag ?? 'upcoming';
    if (!['upcoming', 'lastmatch'].includes(tag)) {
      throw new Error('tag must be upcoming or lastmatch');
    }
    const langrbfaurl = config?.langrbfaurl;
    if (langrbfaurl != null && !['nl', 'fr', 'en'].includes(langrbfaurl)) {
      throw new Error('langrbfaurl must be nl, fr or en');
    }
    this._config = { baseid: String(baseId).trim(), tag, langrbfaurl };
    this._discoveredEntities = null;
    this.syncCountdownTimer();
    this.render();
  }

  set hass(hass) {
    const previous = this._hass;
    this._hass = hass;
    const nextEntities = this.resolveEntities(hass);
    const mappingUnchanged = JSON.stringify(nextEntities) === JSON.stringify(this._resolvedEntities);
    const ids = Object.values(nextEntities);
    if (previous && this._config && previous.language === hass.language &&
        mappingUnchanged && ids.every(id => previous.states[id] === hass.states[id])) return;
    this.render();
  }

  resolveEntities(hass) {
    if (this._discoveredEntities && this._discoveryStates === hass?.states && this._discoveryBaseId === this._config?.baseid && this._discoveryTag === this._config?.tag) {
      return this._discoveredEntities;
    }
    const resolved = {};
    const fields = ['starttime', 'hometeam', 'awayteam', 'series', 'state', 'location', 'referee', 'matchid'];
    const baseId = this._config?.baseid;
    if (baseId != null && hass?.states) {
      for (const id in hass.states) {
        if (!id.startsWith('sensor.')) continue;
        const entity = hass.states[id];
        const attributes = entity.attributes || {};
        if (attributes.baseid == null || String(attributes.baseid) !== String(baseId)) continue;
        if (attributes.tag === this._config?.tag && fields.includes(attributes.field)) {
          if (!resolved[attributes.field]) resolved[attributes.field] = id;
        }
        if (Array.isArray(attributes.series) && !resolved.rankings) resolved.rankings = id;
      }
    }
    this._discoveryStates = hass?.states;
    this._discoveryBaseId = this._config?.baseid;
    this._discoveryTag = this._config?.tag;
    this._discoveredEntities = resolved;
    return resolved;
  }

  connectedCallback() {
    this.syncCountdownTimer();
  }

  syncCountdownTimer() {
    clearInterval(this._interval);
    this._interval = null;
    if (this.isConnected && this._config?.tag === 'upcoming') {
      this._interval = setInterval(() => this.updateCountdown(), 1000);
      this.updateCountdown();
    }
  }

  disconnectedCallback() {
    clearInterval(this._interval);
  }

  escapeHtml(value) {
    const characters = { '&': '&amp;', '<': '&lt;', '>': '&gt;', '"': '&quot;', "'": '&#39;' };
    return String(value ?? '').replace(/[&<>"']/g, character => characters[character]);
  }

  imageUrl(value) {
    if (typeof value !== 'string' || !value.trim()) return '';
    try {
      const url = new URL(value, window.location.href);
      return ['http:', 'https:'].includes(url.protocol) ? this.escapeHtml(url.href) : '';
    } catch {
      return '';
    }
  }

  getTranslation(lang) {
    const translations = {
      fr: {
        live: "🔴 EN COURS",
        ended: "🏁 TERMINÉ",
        postponed: "REPORTÉ",
        forfeitbyoneteam: "FORFAIT D’UNE ÉQUIPE",
        generalforfeit: "FORFAIT GÉNÉRAL",
        planned: "PRÉVU",
        no_data: "Aucun match disponible",
        home: "Équipe à domicile",
        away: "Équipe à l’extérieur",
        day: "j",
        penalties: "Tirs au but",
        pos: "Pos.",
        vs: "VS",
        place: "Lieu",
        referee: "Arbitre",
        match_info: "Fiche Match ↗",
        to_confirm: "À confirmer",
        nav_maps: "Google Maps",
        nav_waze: "Waze"
      },
      nl: {
        live: "🔴 BEZIG",
        ended: "🏁 AFGELOPEN",
        postponed: "UITGESTELD",
        forfeitbyoneteam: "FORFAIT DOOR ÉÉN PLOEG",
        generalforfeit: "ALGEMEEN FORFAIT",
        planned: "GEPLAND",
        no_data: "Geen wedstrijd beschikbaar",
        home: "Thuisploeg",
        away: "Uitploeg",
        day: "d",
        penalties: "Strafschoppen",
        pos: "Pos.",
        vs: "TEGEN",
        place: "Locatie",
        referee: "Scheidsrechter",
        match_info: "Wedstrijd Info ↗",
        to_confirm: "Nog te bevestigen",
        nav_maps: "Google Maps",
        nav_waze: "Waze"
      },
      en: {
        live: "🔴 LIVE",
        ended: "🏁 FINISHED",
        postponed: "POSTPONED",
        forfeitbyoneteam: "ONE-TEAM FORFEIT",
        generalforfeit: "GENERAL FORFEIT",
        planned: "SCHEDULED",
        no_data: "No match available",
        home: "Home team",
        away: "Away team",
        day: "d",
        penalties: "Penalties",
        pos: "Pos.",
        vs: "VS",
        place: "Venue",
        referee: "Referee",
        match_info: "Match Details ↗",
        to_confirm: "To be confirmed",
        nav_maps: "Google Maps",
        nav_waze: "Waze"
      },
      pt: {
        live: "🔴 EM DIRETO", ended: "🏁 TERMINADO",
        postponed: "ADIADO", forfeitbyoneteam: "FALTA DE COMPARÊNCIA DE UMA EQUIPA",
        generalforfeit: "FALTA DE COMPARÊNCIA GERAL", planned: "AGENDADO",
        no_data: "Nenhum jogo disponível",
        home: "Equipa da casa", away: "Equipa visitante", day: "d",
        penalties: "Penáltis",
        pos: "Pos.", vs: "VS", place: "Local", referee: "Árbitro",
        match_info: "Detalhes do jogo ↗", to_confirm: "Por confirmar",
        nav_maps: "Google Maps", nav_waze: "Waze"
      }
    };

    const cleanLang = (lang || 'en').toLowerCase().split('-')[0];
    return translations[cleanLang] || translations.en;
  }

  updateCountdown() {
    if (this._config?.tag !== 'upcoming' || !this._hass || !this._t) return;
    const now = new Date().getTime();
    const diff = this._startTime - now;
    const badge = this.shadowRoot.querySelector('.countdown-badge');
    if (!badge) return;

    const t = this._t;

    badge.style.background = '';
    if (this._matchState === 'finished') {
      badge.textContent = t.ended;
      badge.style.background = '#7f8c8d';
      return;
    }
    if (['postponed', 'forfeitbyoneteam', 'generalforfeit'].includes(this._matchState)) {
      badge.textContent = t[this._matchState];
      badge.style.background = '#7f8c8d';
      return;
    }
    if (!Number.isFinite(this._startTime) || !this._matchState) {
      badge.textContent = t.to_confirm;
      return;
    }

    if (diff > 0) {
      const days = Math.floor(diff / (1000 * 60 * 60 * 24));
      const hours = Math.floor((diff % (1000 * 60 * 60 * 24)) / (1000 * 60 * 60));
      const minutes = Math.floor((diff % (1000 * 60 * 60)) / (1000 * 60));
      const seconds = Math.floor((diff % (1000 * 60)) / 1000);

      let text = '⏱️ ';
      if (days > 0) text += `${days}${t.day} `;
      text += `${hours}h ${minutes}m ${seconds}s`;
      badge.textContent = text;
    } else if (this._matchState === 'planned') {
      badge.textContent = t.planned;
    } else {
      badge.textContent = t.live;
      badge.style.background = '#e74c3c';
    }
  }

  render() {
    if (!this._hass || !this._config) return;

    const systemLanguage = this._hass.language || navigator.language || 'en';
    const requestedLang = systemLanguage.toLowerCase().split('-')[0];
    const cardLanguage = ['nl', 'fr', 'en', 'pt'].includes(requestedLang) ? requestedLang : 'en';
    this._t = this.getTranslation(cardLanguage);
    const t = this._t;

    const userLang = systemLanguage.toLowerCase().split('-')[0];
    const rbfaLang = this._config.langrbfaurl ?? (['nl', 'fr', 'en'].includes(userLang) ? userLang : 'en');
    const rbfaMatchPath = ({ nl: 'wedstrijd', fr: 'match', en: 'game' })[rbfaLang];
    
    this._resolvedEntities = this.resolveEntities(this._hass);
    const getEntity = key => this._hass.states[this._resolvedEntities[key]];
    const value = entity => entity?.state && !['unknown', 'unavailable'].includes(entity.state) ? entity.state : null;
    const sensorSeries = getEntity('series');
    const sensorStartTime = getEntity('starttime');
    const sensorHome = getEntity('hometeam');
    const sensorAway = getEntity('awayteam');
    const sensorLocation = getEntity('location');
    const sensorReferee = getEntity('referee');
    const sensorMatchId = getEntity('matchid');
    this._matchState = value(getEntity('state'));
    const startTime = Date.parse(value(sensorStartTime) || '');
    this._startTime = Number.isFinite(startTime) ? startTime : null;
    if (!this._startTime && !value(sensorHome) && !value(sensorAway)) {
      this.shadowRoot.innerHTML = `<ha-card style="padding: 16px; text-align: center;">${t.no_data}</ha-card>`;
      return;
    }
    const rankingEntity = getEntity('rankings');
    const seriesList = value(rankingEntity) && Array.isArray(rankingEntity?.attributes?.series) ? rankingEntity.attributes.series : [];
    const seriesId = sensorSeries?.attributes?.id;
    const ranking = seriesId != null ? seriesList.find(series => String(series?.seriesId) === String(seriesId))?.ranking : [];
    const position = team => {
      const id = team?.attributes?.id;
      if (id == null || !Array.isArray(ranking)) return '—';
      return this.escapeHtml(ranking.find(row => String(row?.teamId) === String(id))?.position ?? '—');
    };
    const seriesName = this.escapeHtml(value(sensorSeries) || 'RBFA');
    const homeName = this.escapeHtml(value(sensorHome) || t.home);
    const homeImg = this.imageUrl(sensorHome?.attributes?.entity_picture);
    const homePos = position(sensorHome);
    const awayName = this.escapeHtml(value(sensorAway) || t.away);
    const awayImg = this.imageUrl(sensorAway?.attributes?.entity_picture);
    const awayPos = position(sensorAway);

    const scoreValue = (sensor, key) => {
      if (!value(sensor)) return null;
      const raw = sensor.attributes?.[key];
      if (raw == null || raw === '' || !['number', 'string'].includes(typeof raw)) return null;
      const number = Number(raw);
      return Number.isInteger(number) && number >= 0 ? number : null;
    };
    const homeGoals = scoreValue(sensorHome, 'goals');
    const awayGoals = scoreValue(sensorAway, 'goals');
    const homePenalties = scoreValue(sensorHome, 'penalties');
    const awayPenalties = scoreValue(sensorAway, 'penalties');
    const cancelled = ['postponed', 'forfeitbyoneteam', 'generalforfeit'].includes(this._matchState);
    const hasScore = !cancelled && homeGoals != null && awayGoals != null;
    const hasPenalties = hasScore && homePenalties != null && awayPenalties != null;

    const rawLocation = sensorLocation?.state;
    const locationText = (rawLocation && !['unknown', 'unavailable'].includes(rawLocation)) 
      ? rawLocation.replace(/\n/g, ', ') 
      : t.to_confirm;

    const encodedLocation = encodeURIComponent(locationText);
    const mapsUrl = `https://www.google.com/maps/search/?api=1&query=${encodedLocation}`;
    const wazeUrl = `https://waze.com/ul?q=${encodedLocation}&navigate=yes`;

    const refereeName = this.escapeHtml(value(sensorReferee) || t.to_confirm);
    const matchId = value(sensorMatchId);

    const dateFormatted = this._startTime
      ? new Date(this._startTime).toLocaleDateString(cardLanguage, {
          weekday: 'short',
          day: 'numeric',
          month: 'short',
          hour: '2-digit',
          minute: '2-digit'
        })
      : t.to_confirm;

    this.shadowRoot.innerHTML = `
      <style>
        :host {
          display: block;
        }
        .match-card {
          background: var(--ha-card-background, var(--card-background-color, #1c1c1e));
          border-radius: 16px;
          padding: 18px;
          box-shadow: 0 6px 18px rgba(0,0,0,0.12);
          font-family: system-ui, -apple-system, sans-serif;
          color: var(--primary-text-color);
        }
        .header {
          display: flex;
          justify-content: space-between;
          align-items: center;
          margin-bottom: 12px;
        }
        .league {
          font-size: 0.9rem;
          font-weight: 800;
          letter-spacing: 1.2px;
          text-transform: uppercase;
          color: var(--secondary-text-color);
        }
        .match-link {
          font-size: 0.85rem;
          color: var(--primary-color, #03a9f4);
          text-decoration: none;
          font-weight: 700;
        }
        .banner {
          background: rgba(var(--rgb-primary-color, 3, 169, 244), 0.12);
          border-radius: 12px;
          padding: 10px 14px;
          display: flex;
          justify-content: space-between;
          align-items: center;
          margin-bottom: 16px;
        }
        .date-info {
          font-size: 0.95rem;
          font-weight: 700;
        }
        .countdown-badge {
          background: var(--primary-color, #03a9f4);
          color: #fff;
          font-size: 0.85rem;
          font-weight: 700;
          padding: 5px 12px;
          border-radius: 20px;
        }
        .teams-container {
          display: flex;
          justify-content: space-around;
          align-items: center;
          margin: 16px 0;
        }
        .team {
          flex: 1;
          display: flex;
          flex-direction: column;
          align-items: center;
          text-align: center;
        }
        .logo {
          width: 72px;
          height: 72px;
          object-fit: contain;
          margin-bottom: 8px;
          filter: drop-shadow(0px 3px 3px rgba(0,0,0,0.2));
        }
        .team-name {
          font-size: 1.05rem;
          font-weight: 800;
          line-height: 1.3;
        }
        .team-pos {
          font-size: 0.85rem;
          opacity: 0.7;
          margin-top: 2px;
        }
        .vs-badge {
          font-weight: 900;
          font-size: 1.1rem;
          opacity: 0.3;
          padding: 0 10px;
        }
        .score-container {
          display: flex;
          flex-direction: column;
          align-items: center;
          gap: 4px;
          padding: 0 10px;
          text-align: center;
        }
        .score {
          font-size: 1.8rem;
          font-weight: 900;
          white-space: nowrap;
          font-variant-numeric: tabular-nums;
        }
        .penalties {
          font-size: 0.75rem;
          color: var(--secondary-text-color);
        }
        .footer-info {
          font-size: 0.85rem;
          padding-top: 12px;
          border-top: 1px solid var(--divider-color, rgba(255,255,255,0.08));
          color: var(--secondary-text-color);
          display: flex;
          flex-direction: column;
          gap: 8px;
        }
        .location-line {
          display: flex;
          justify-content: space-between;
          align-items: center;
          flex-wrap: wrap;
          gap: 8px;
        }
        .nav-buttons {
          display: flex;
          gap: 8px;
        }
        .nav-btn {
          padding: 4px 10px;
          border-radius: 6px;
          background: rgba(255,255,255,0.1);
          color: var(--primary-text-color);
          text-decoration: none;
          font-size: 0.8rem;
          font-weight: 700;
          transition: background 0.2s;
        }
        .nav-btn:hover {
          background: var(--primary-color);
          color: #fff;
        }
      </style>

      <div class="match-card">
        <div class="header">
          <span class="league">⚽ ${seriesName}</span>
          ${matchId ? `<a class="match-link" href="https://www.rbfa.be/${rbfaLang}/${rbfaMatchPath}/${encodeURIComponent(matchId)}" target="_blank" rel="noopener noreferrer">${t.match_info}</a>` : ''}
        </div>

        <div class="banner">
          <span class="date-info">📅 ${dateFormatted}</span>
          ${this._config.tag === 'upcoming' ? '<span class="countdown-badge">⏱️ --h --m</span>' : ''}
        </div>

        <div class="teams-container">
          <div class="team">
            ${homeImg ? `<img class="logo" src="${homeImg}" alt="" />` : ''}
            <span class="team-name">${homeName}</span>
            <span class="team-pos">${t.pos} n°${homePos}</span>
          </div>

          ${hasScore ? `
            <div class="score-container">
              <span class="score">${homeGoals} - ${awayGoals}</span>
              ${hasPenalties ? `<span class="penalties">${t.penalties}: ${homePenalties} - ${awayPenalties}</span>` : ''}
            </div>
          ` : `<div class="vs-badge">${t.vs}</div>`}

          <div class="team">
            ${awayImg ? `<img class="logo" src="${awayImg}" alt="" />` : ''}
            <span class="team-name">${awayName}</span>
            <span class="team-pos">${t.pos} n°${awayPos}</span>
          </div>
        </div>

        <div class="footer-info">
          <div class="location-line">
            <span>📍 <b>${t.place} :</b> ${this.escapeHtml(locationText)}</span>
            ${locationText !== t.to_confirm ? `
              <div class="nav-buttons">
                <a class="nav-btn" href="${this.escapeHtml(mapsUrl)}" target="_blank" rel="noopener noreferrer">🗺️ ${t.nav_maps}</a>
                <a class="nav-btn" href="${this.escapeHtml(wazeUrl)}" target="_blank" rel="noopener noreferrer">🚗 ${t.nav_waze}</a>
              </div>
            ` : ''}
          </div>
          <div>⚖️ <b>${t.referee} :</b> ${refereeName}</div>
        </div>
      </div>
    `;

    if (this._config.tag === 'upcoming') this.updateCountdown();
  }
}

if (!customElements.get('match-card')) {
    customElements.define('match-card', MatchCard);
}
