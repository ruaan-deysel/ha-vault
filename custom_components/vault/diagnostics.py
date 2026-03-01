"""Diagnostics support for the Vault integration."""

from __future__ import annotations

from typing import Any

from homeassistant.components.diagnostics import async_redact_data
from homeassistant.core import HomeAssistant

from .coordinator import VaultConfigEntry

TO_REDACT = {"host", "api_key"}


async def async_get_config_entry_diagnostics(
    hass: HomeAssistant,
    entry: VaultConfigEntry,
) -> dict[str, Any]:
    """Return diagnostics for a config entry."""
    coordinator = entry.runtime_data.coordinator
    data = coordinator.data

    redacted_data = async_redact_data(dict(entry.data), TO_REDACT)

    return {
        "config_entry": redacted_data,
        "coordinator_data": {
            "health": data.health.model_dump(),
            "settings": data.settings.model_dump(),
            "encryption": data.encryption.model_dump(),
            "storage_count": len(data.storage),
            "jobs_count": len(data.jobs),
            "jobs": [
                {
                    "id": job.id,
                    "name": job.name,
                    "enabled": job.enabled,
                    "schedule": job.schedule,
                    "encryption": job.encryption,
                    "compression": job.compression,
                }
                for job in data.jobs
            ],
            "activity_count": len(data.activity),
        },
    }
