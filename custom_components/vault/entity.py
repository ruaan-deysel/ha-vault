"""Base entity for the Vault integration."""

from __future__ import annotations

from typing import TYPE_CHECKING

from homeassistant.core import HomeAssistant, callback
from homeassistant.helpers import entity_registry as er
from homeassistant.helpers.device_registry import DeviceInfo
from homeassistant.helpers.update_coordinator import CoordinatorEntity

from .const import CONF_HOST, CONF_PORT, CONF_TLS, DEFAULT_PORT, DOMAIN
from .coordinator import VaultDataUpdateCoordinator

if TYPE_CHECKING:
    from .api.models import BackupJob


@callback
def async_remove_stale_entities(
    hass: HomeAssistant,
    platform_domain: str,
    unique_ids: set[str],
) -> None:
    """Remove registry entries for entities whose source object no longer exists."""
    registry = er.async_get(hass)
    for unique_id in unique_ids:
        if entity_id := registry.async_get_entity_id(platform_domain, DOMAIN, unique_id):
            registry.async_remove(entity_id)


@callback
def async_prune_orphan_entities(
    hass: HomeAssistant,
    entry_id: str,
    platform_domain: str,
    valid_unique_ids: set[str],
) -> None:
    """Remove registry entries of this platform that no longer map to a known object.

    Cleans up leftovers from jobs/storage deleted or renamed while Home
    Assistant was not running, and from older integration versions.
    """
    registry = er.async_get(hass)
    for reg_entry in er.async_entries_for_config_entry(registry, entry_id):
        if reg_entry.domain == platform_domain and reg_entry.unique_id not in valid_unique_ids:
            registry.async_remove(reg_entry.entity_id)


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
            # Vault is an Unraid plugin — its UI lives in the Unraid web UI,
            # not on the API port, so link to the Unraid host itself.
            configuration_url=f"{scheme}://{host}",
        )


class VaultJobEntity(VaultEntity):
    """Base class for per-job entities.

    Unique IDs are derived from the immutable job id (via the entity
    description key), while the displayed name follows job renames.
    """

    def __init__(
        self,
        coordinator: VaultDataUpdateCoordinator,
        entity_description: object,
        job: BackupJob,
        name_label: str,
    ) -> None:
        """Initialize the per-job entity.

        Args:
            coordinator: The data update coordinator.
            entity_description: Platform-specific EntityDescription whose key
                must contain the job id (e.g. ``job_12_status``).
            job: The backup job this entity belongs to.
            name_label: Suffix appended to the job name (e.g. "Status").
        """
        super().__init__(coordinator, entity_description)
        self._job_id = job.id
        self._job_name = job.name
        self._name_label = name_label

    @property
    def name(self) -> str:
        """Return the entity name, tracking job renames."""
        if self.coordinator.data is None:
            return f"{self._job_name} {self._name_label}"
        job = next((j for j in self.coordinator.data.jobs if j.id == self._job_id), None)
        if job is not None:
            self._job_name = job.name
        return f"{self._job_name} {self._name_label}"
