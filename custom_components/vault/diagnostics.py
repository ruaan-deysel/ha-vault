"""Diagnostics support for the Vault integration."""

from __future__ import annotations

from typing import Any

from homeassistant.components.diagnostics import async_redact_data
from homeassistant.core import HomeAssistant

from .coordinator import VaultConfigEntry

TO_REDACT = {
    "host",
    "api_key",
    "passphrase",
    "encryption_passphrase",
    "password",
    "token",
    "secret",
    "webhook",
    "webhook_url",
    "discord_webhook_url",
}


async def async_get_config_entry_diagnostics(
    hass: HomeAssistant,
    entry: VaultConfigEntry,
) -> dict[str, Any]:
    """Return diagnostics for a config entry."""
    coordinator = entry.runtime_data.coordinator
    data = coordinator.data

    diagnostics = {
        "config_entry": dict(entry.data),
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
    # Redact the whole payload — Settings allows arbitrary extra keys that may
    # contain secrets (webhook URLs, passphrases) depending on plugin version.
    return async_redact_data(diagnostics, TO_REDACT)
