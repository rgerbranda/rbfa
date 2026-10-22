class RankingCard extends HTMLElement {
  constructor() {
    super();
    this.attachShadow({ mode: "open" });
  }

  setConfig(config) {
    if (!config?.entity) throw new Error('Configure entity for ranking-card');
    this._config = { entity: config.entity, series_id: config.series_id };
    this.render();
  }

  set hass(hass) {
    const previous = this._hass;
    this._hass = hass;
    if (previous && this._config &&
        previous.states[this._config.entity] === hass.states[this._config.entity] &&
        previous.language === hass.language) return;
    this.render();
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
        title: "CLASSEMENT",
        pos: "P",
        team: "Équipe",
        played: "J",
        won: "G",
        drawn: "N",
        lost: "P",
        diff: "+/-",
        pts: "Pts",
        unknown_team: "Équipe inconnue",
        no_data: "Classement indisponible"
      },
      nl: {
        title: "RANGSCHIKKING",
        pos: "P",
        team: "Ploeg",
        played: "G",
        won: "W",
        drawn: "G",
        lost: "V",
        diff: "+/-",
        pts: "Ptn",
        unknown_team: "Onbekende ploeg",
        no_data: "Rangschikking niet beschikbaar"
      },
      en: {
        title: "RANKING",
        pos: "P",
        team: "Team",
        played: "P",
        won: "W",
        drawn: "D",
        lost: "L",
        diff: "GD",
        pts: "Pts",
        unknown_team: "Unknown team",
        no_data: "Ranking unavailable"
      },
      pt: {
        title: "CLASSIFICAÇÃO",
        pos: "P",
        team: "Equipa",
        played: "J",
        won: "V",
        drawn: "E",
        lost: "D",
        diff: "DG",
        pts: "Pts",
        unknown_team: "Equipa desconhecida",
        no_data: "Classificação indisponível"
      }
    };

    const cleanLang = (lang || 'fr').toLowerCase().split('-')[0];
    return translations[cleanLang] || translations.fr;
  }

  render() {
    if (!this._hass || !this._config) return;

    const systemLanguage = this._hass.language || navigator.language || 'fr';
    const t = this.getTranslation(systemLanguage);

    const entity = this._hass.states[this._config.entity];

    if (!entity || ['unknown', 'unavailable'].includes(entity.state)) {
      this.shadowRoot.innerHTML = `<ha-card style="padding: 16px; text-align: center;">${t.no_data}</ha-card>`;
      return;
    }

    const seriesList = Array.isArray(entity.attributes?.series) ? entity.attributes.series : [];
    const selectedSeries = this._config.series_id != null
      ? seriesList.find(series => String(series?.seriesId) === String(this._config.series_id))
      : seriesList[0];
    const seriesName = this.escapeHtml(selectedSeries?.name || 'RBFA');
    const baseId = entity.attributes?.baseid;
    const teamsList = Array.isArray(selectedSeries?.ranking)
      ? selectedSeries.ranking.filter(item => item && typeof item === 'object')
      : [];

    let rowsHtml = '';
    if (teamsList.length > 0) {
      rowsHtml = teamsList.map(item => {
        const teamId = String(item.teamId ?? '');
        const isMyTeam = baseId != null && (teamId === String(baseId));
        const teamName = this.escapeHtml(item.name || t.unknown_team);
        const position = this.escapeHtml(item.position ?? '—');
        const teamLogo = this.imageUrl(item.logo);
        
        const played = this.escapeHtml(item.matchesPlayed ?? '—');
        const won = this.escapeHtml(item.matchesWon ?? '—');
        const drawn = this.escapeHtml(item.matchesDrawn ?? '—');
        const lost = this.escapeHtml(item.matchesLost ?? '—');
        const diffVal = item.goalDifference;
        const diff = this.escapeHtml(diffVal != null ? (diffVal > 0 ? `+${diffVal}` : diffVal) : '—');
        const points = this.escapeHtml(item.points ?? '—');

        return `
          <tr class="ranking-row ${isMyTeam ? 'highlight' : ''}">
            <td class="pos-col">
              <span class="pos-badge ${isMyTeam ? 'pos-badge-highlight' : ''}">${position}</span>
            </td>
            <td class="team-col">
              <div class="team-info-wrapper">
                ${teamLogo ? `<img class="team-logo" src="${teamLogo}" alt="" loading="lazy" />` : ''}
                <span class="team-name-ranking">${teamName}</span>
              </div>
            </td>
            <td class="stat-col">${played}</td>
            <td class="stat-col hide-mobile">${won}</td>
            <td class="stat-col hide-mobile">${drawn}</td>
            <td class="stat-col hide-mobile">${lost}</td>
            <td class="stat-col">${diff}</td>
            <td class="pts-col"><b>${points}</b></td>
          </tr>
        `;
      }).join('');
    } else {
      rowsHtml = `<tr><td colspan="8" style="text-align: center; padding: 16px; opacity: 0.7;">${t.no_data}</td></tr>`;
    }

    this.shadowRoot.innerHTML = `
      <style>
        :host {
          display: block;
          container-type: inline-size;
          container-name: ranking-card;
        }
        .ranking-card {
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
          margin-bottom: 14px;
        }
        .header-title-container {
          display: flex;
          align-items: center;
          gap: 10px;
        }
        .league-name {
          font-size: 0.95rem;
          font-weight: 800;
          letter-spacing: 0.8px;
          text-transform: uppercase;
          color: var(--primary-text-color);
        }
        .card-subtitle {
          font-size: 0.75rem;
          font-weight: 700;
          letter-spacing: 1.2px;
          text-transform: uppercase;
          color: var(--secondary-text-color);
        }
        .ranking-table {
          width: 100%;
          border-collapse: separate;
          border-spacing: 0 5px;
          margin-top: 4px;
        }
        .ranking-header th {
          font-size: 0.65rem;
          text-transform: uppercase;
          color: var(--secondary-text-color);
          padding: 4px 4px;
          font-weight: 700;
          text-align: center;
        }
        .ranking-header th:nth-child(2) {
          text-align: left;
        }
        .ranking-row {
          background: rgba(255, 255, 255, 0.03);
          transition: background 0.2s;
        }
        .ranking-row td:first-child {
          border-top-left-radius: 10px;
          border-bottom-left-radius: 10px;
        }
        .ranking-row td:last-child {
          border-top-right-radius: 10px;
          border-bottom-right-radius: 10px;
        }
        .ranking-row.highlight {
          background: rgba(var(--rgb-primary-color, 3, 169, 244), 0.18);
          border: 1px solid var(--primary-color, #03a9f4);
        }
        .pos-col {
          width: 32px;
          text-align: center;
          padding: 6px 2px;
        }
        .pos-badge {
          display: inline-flex;
          align-items: center;
          justify-content: center;
          width: 22px;
          height: 22px;
          border-radius: 50%;
          font-size: 0.7rem;
          font-weight: 700;
          background: rgba(255, 255, 255, 0.08);
          color: var(--secondary-text-color);
        }
        .pos-badge-highlight {
          background: var(--primary-color, #03a9f4);
          color: #fff;
          box-shadow: 0 2px 5px rgba(0,0,0,0.25);
        }
        .team-col {
          padding: 6px 8px;
          font-size: 0.7rem;
          display: flex;
          align-items: center;
          justify-content: space-between;
        }
        .team-info-wrapper {
          display: flex;
          align-items: center;
          gap: 8px;
          overflow: hidden;
        }
        .team-logo {
          width: 20px;
          height: 20px;
          object-fit: contain;
          flex-shrink: 0;
        }
        .team-name-ranking {
          font-size: 0.85rem;
          white-space: nowrap;
          overflow: hidden;
          text-overflow: ellipsis;
        }
        .ranking-row.highlight .team-name-ranking {
          font-weight: 800;
          color: var(--primary-text-color);
        }
        .stat-col {
          width: 28px;
          text-align: center;
          font-size: 0.75rem;
          opacity: 0.75;
          padding: 6px 2px;
        }
        .pts-col {
          width: 34px;
          text-align: center;
          font-size: 0.85rem;
          padding: 6px 4px;
          color: var(--primary-color, #03a9f4);
        }
        @container ranking-card (max-width: 450px) {
          .hide-mobile { display: none; }
        }
      </style>

      <div class="ranking-card">
        <div class="header">
          <div class="header-title-container">
            <div>
              <div class="card-subtitle">🏆 ${t.title}</div>
              <div class="league-name">${seriesName}</div>
            </div>
          </div>
        </div>

        <table class="ranking-table">
          <thead>
            <tr class="ranking-header">
              <th>${t.pos}</th>
              <th>${t.team}</th>
              <th>${t.played}</th>
              <th class="hide-mobile">${t.won}</th>
              <th class="hide-mobile">${t.drawn}</th>
              <th class="hide-mobile">${t.lost}</th>
              <th>${t.diff}</th>
              <th>${t.pts}</th>
            </tr>
          </thead>
          <tbody>
            ${rowsHtml}
          </tbody>
        </table>
      </div>
    `;
  }
}

customElements.define('ranking-card', RankingCard);
