
from __future__ import annotations
from homeassistant.helpers.update_coordinator import CoordinatorEntity
from .coordinator import MyCoordinator


class RbfaEntity(CoordinatorEntity[MyCoordinator]):
    """Defines an Elgato entity."""

    _attr_has_entity_name = True

    def __init__(self, coordinator: MyCoordinator) -> None:
        """Initialize an Elgato entity."""
        super().__init__(coordinator=coordinator)
