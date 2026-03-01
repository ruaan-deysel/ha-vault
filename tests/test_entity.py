"""Tests for the Vault base entity."""

from __future__ import annotations

from pytest_homeassistant_custom_component.common import MockConfigEntry

from custom_components.vault.const import DOMAIN
from homeassistant.core import HomeAssistant
from homeassistant.helpers import device_registry as dr, entity_registry as er


async def test_device_info(
    hass: HomeAssistant,
    mock_setup_entry: MockConfigEntry,
) -> None:
    """Test that entities create a device with correct info."""
    device_registry = dr.async_get(hass)
    device = device_registry.async_get_device(identifiers={(DOMAIN, "192.168.1.100:24085")})
    assert device is not None
    assert device.name == "Vault Backup"
    assert device.manufacturer == "Vault"
    assert device.model == "Unraid Backup Daemon"
    assert device.sw_version == "1.0.0"
    assert device.configuration_url == "http://192.168.1.100:24085"


async def test_unique_id_format(
    hass: HomeAssistant,
    mock_setup_entry: MockConfigEntry,
) -> None:
    """Test that entities have correct unique_id format."""
    registry = er.async_get(hass)
    entries = er.async_entries_for_config_entry(registry, mock_setup_entry.entry_id)
    assert len(entries) > 0

    # All unique_ids should start with the entry_id
    for entity_entry in entries:
        assert entity_entry.unique_id.startswith(mock_setup_entry.entry_id)
