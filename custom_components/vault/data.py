"""
Custom types for vault.

This module defines the runtime data structure attached to each config entry.
Access pattern: entry.runtime_data.client / entry.runtime_data.coordinator

The VaultConfigEntry type alias is used throughout the integration
for type-safe access to the config entry's runtime data.
"""

from __future__ import annotations

from dataclasses import dataclass
from typing import TYPE_CHECKING

if TYPE_CHECKING:
    from homeassistant.config_entries import ConfigEntry
    from homeassistant.loader import Integration

    from .api import VaultApiClient
    from .coordinator import VaultDataUpdateCoordinator


type VaultConfigEntry = ConfigEntry[VaultData]


@dataclass
class VaultData:
    """Runtime data for vault config entries.

    Stored as entry.runtime_data after successful setup.
    Provides typed access to the API client and coordinator instances.
    """

    client: VaultApiClient
    coordinator: VaultDataUpdateCoordinator
    integration: Integration
