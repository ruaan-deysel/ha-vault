"""Base entity for the Vault integration."""

from __future__ import annotations

from homeassistant.helpers.device_registry import DeviceInfo
from homeassistant.helpers.update_coordinator import CoordinatorEntity

from .const import CONF_HOST, CONF_PORT, CONF_TLS, DEFAULT_PORT, DOMAIN
from .coordinator import VaultDataUpdateCoordinator


class VaultEntity(CoordinatorEntity[VaultDataUpdateCoordinator]):
    """Base class for all Vault entities."""

    _attr_has_entity_name = True

    def __init__(
        self,
        coordinator: VaultDataUpdateCoordinator,
        entity_description: object,
    ) -> None:
        """Initialize the base entity.

        Args:
            coordinator: The data update coordinator.
            entity_description: Platform-specific EntityDescription.
        """
        super().__init__(coordinator)
        self.entity_description = entity_description  # type: ignore[assignment]
        self._attr_unique_id = f"{coordinator.config_entry.entry_id}_{entity_description.key}"  # type: ignore[attr-defined]

        entry_data = coordinator.config_entry.data
        host = entry_data.get(CONF_HOST, "")
        port = entry_data.get(CONF_PORT, DEFAULT_PORT)
        tls = entry_data.get(CONF_TLS, False)
        version = coordinator.data.health.version if coordinator.data else ""
        scheme = "https" if tls else "http"

        self._attr_device_info = DeviceInfo(
            identifiers={(DOMAIN, f"{host}:{port}")},
            name="Vault Backup",
            manufacturer="Vault",
            model="Unraid Backup Daemon",
            sw_version=version or None,
            configuration_url=f"{scheme}://{host}:{port}",
        )
