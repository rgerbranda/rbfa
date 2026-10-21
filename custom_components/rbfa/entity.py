
from __future__ import annotations
from homeassistant.helpers.update_coordinator import CoordinatorEntity
from .coordinator import RbfaCoordinator, RbfaRankingCoordinator

def get_team_name(coordinator: RbfaCoordinator) -> str:
    """Return the alternative name or the RBFA team name."""
    entry = coordinator.config_entry
    teamdata = coordinator.data['teamdata']

    alt_name = entry.options.get(
        'alt_name',
        entry.data.get('alt_name', ''),
    )

    return (
        alt_name.strip()
        or f"{teamdata['clubName']} | {teamdata['name']}"
    )

class RbfaEntity(
    CoordinatorEntity[RbfaCoordinator | RbfaRankingCoordinator]
):
    """Defines an RBFA entity."""

    _attr_has_entity_name = True

    def __init__(
        self,
        coordinator: RbfaCoordinator | RbfaRankingCoordinator,
    ) -> None:
        super().__init__(coordinator=coordinator)