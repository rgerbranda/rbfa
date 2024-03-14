#from __future__ import annotations

import logging
from datetime import timedelta
from homeassistant.config_entries import ConfigEntry
from homeassistant.const import Platform

from homeassistant.core import HomeAssistant

from .const import DOMAIN
from .API import TeamApp
from .coordinator import MyCoordinator

_LOGGER = logging.getLogger(__name__)

PLATFORMS = [Platform.CALENDAR, Platform.SENSOR]

async def async_setup_entry(hass, entry) -> bool:
    """Set up RBFA from a config entry."""
    coordinator = MyCoordinator(hass, entry)
    _LOGGER.debug('first refresh')
    await coordinator.async_config_entry_first_refresh()

    hass.data.setdefault(DOMAIN, {})[entry.entry_id] = coordinator
    await hass.config_entries.async_forward_entry_setups(entry, PLATFORMS)

    return True
