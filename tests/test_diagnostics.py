"""Tests for Vault diagnostics."""

from __future__ import annotations

from pytest_homeassistant_custom_component.common import MockConfigEntry

from custom_components.vault.diagnostics import async_get_config_entry_diagnostics
from homeassistant.core import HomeAssistant


async def test_diagnostics_output(
    hass: HomeAssistant,
    mock_setup_entry: MockConfigEntry,
) -> None:
    """Test diagnostics returns expected structure."""
    result = await async_get_config_entry_diagnostics(hass, mock_setup_entry)

    assert "config_entry" in result
    assert "coordinator_data" in result


async def test_diagnostics_redacts_host(
    hass: HomeAssistant,
    mock_setup_entry: MockConfigEntry,
) -> None:
    """Test diagnostics redacts sensitive host data."""
    result = await async_get_config_entry_diagnostics(hass, mock_setup_entry)

    # Host should be redacted
    assert result["config_entry"]["host"] == "**REDACTED**"
    # Port should not be redacted
    assert result["config_entry"]["port"] == 24085


async def test_diagnostics_coordinator_data(
    hass: HomeAssistant,
    mock_setup_entry: MockConfigEntry,
) -> None:
    """Test diagnostics includes coordinator data."""
    result = await async_get_config_entry_diagnostics(hass, mock_setup_entry)
    coord_data = result["coordinator_data"]

    assert "health" in coord_data
    assert "settings" in coord_data
    assert "encryption" in coord_data
    assert "jobs_count" in coord_data
    assert "jobs" in coord_data
    assert coord_data["jobs_count"] == 3
