
from __future__ import annotations
from homeassistant.helpers.update_coordinator import CoordinatorEntity
from .coordinator import RbfaCoordinator


class RbfaEntity(CoordinatorEntity[RbfaCoordinator]):
    """Defines an RBFA entity."""

    _attr_has_entity_name = True

    def __init__(self, coordinator: RbfaCoordinator) -> None:
        """Initialize an RBFA entity."""
        super().__init__(coordinator=coordinator)
