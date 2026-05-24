"""Persistence helpers for Pool Manager.

This module wraps :class:`homeassistant.helpers.storage.Store` to persist
state that lives outside the config-entry data (currently the user's
:class:`~.domain.inventory.Inventory`).

One store file is created per config entry, keyed
``poolman.inventory.<entry_id>`` so that multi-pool installations remain
isolated. Loading is fault-tolerant: corrupted or partial payloads cause
the integration to fall back to an empty inventory and log a warning,
never crash setup.
"""

from __future__ import annotations

import logging

from typing import Any

from homeassistant.core import HomeAssistant
from homeassistant.helpers.storage import Store

from .const import DOMAIN
from .domain.inventory import Inventory

_LOGGER = logging.getLogger(__name__)

INVENTORY_STORAGE_VERSION = 1


class InventoryStore:
    """Persistence wrapper for an :class:`Inventory` per config entry."""

    def __init__(self, hass: HomeAssistant, entry_id: str) -> None:
        """Initialize the store.

        Args:
            hass: The Home Assistant instance.
            entry_id: Config entry identifier; used to namespace the
                storage key so multiple pools persist independently.
        """
        self._store: Store[dict[str, Any]] = Store(
            hass,
            INVENTORY_STORAGE_VERSION,
            f"{DOMAIN}.inventory.{entry_id}",
        )

    async def async_load(self) -> Inventory:
        """Load the inventory from disk.

        Returns:
            The persisted :class:`Inventory`, or an empty inventory when
            no data exists or the stored payload cannot be parsed.
        """
        try:
            data = await self._store.async_load()
        except Exception:
            _LOGGER.warning("Failed to load inventory store; starting empty", exc_info=True)
            return Inventory()

        if not data:
            return Inventory()

        try:
            return Inventory.from_dict(data)
        except (KeyError, TypeError, ValueError):
            _LOGGER.warning("Malformed inventory payload; starting empty", exc_info=True)
            return Inventory()

    async def async_save(self, inventory: Inventory) -> None:
        """Persist the inventory to disk."""
        await self._store.async_save(inventory.to_dict())
