from homeassistant.config_entries import ConfigEntry
from homeassistant.const import Platform
from homeassistant.core import HomeAssistant

from .const import DOMAIN
from .coordinator import RbfaCoordinator, RbfaRankingCoordinator

PLATFORMS = [Platform.CALENDAR, Platform.SENSOR]


async def async_setup_entry(
    hass: HomeAssistant,
    entry: ConfigEntry
) -> bool:
    """Set up RBFA from a config entry."""

    coordinator = RbfaCoordinator(hass, entry)
    ranking_coordinator = RbfaRankingCoordinator(hass, entry)

    await coordinator.async_config_entry_first_refresh()
    await ranking_coordinator.async_config_entry_first_refresh()

    hass.data.setdefault(DOMAIN, {})[entry.entry_id] = coordinator
    hass.data.setdefault(
        f"{DOMAIN}_rankings", {}
    )[entry.entry_id] = ranking_coordinator

    entry.async_on_unload(
        entry.add_update_listener(async_update_options)
    )

    await hass.config_entries.async_forward_entry_setups(
        entry, PLATFORMS
    )

    return True


async def async_update_options(
    hass: HomeAssistant,
    entry: ConfigEntry
) -> None:
    """Reload RBFA when options change."""

    await hass.config_entries.async_reload(entry.entry_id)


async def async_unload_entry(
    hass: HomeAssistant,
    entry: ConfigEntry
) -> bool:
    """Unload RBFA integration."""

    unload_ok = await hass.config_entries.async_unload_platforms(
        entry, PLATFORMS
    )

    if unload_ok:
        hass.data.get(DOMAIN, {}).pop(entry.entry_id, None)
        hass.data.get(
            f"{DOMAIN}_rankings", {}
        ).pop(entry.entry_id, None)

    return unload_ok