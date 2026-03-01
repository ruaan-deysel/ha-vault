"""Tests for Vault repairs."""

from __future__ import annotations

from custom_components.vault.const import DOMAIN
from custom_components.vault.repairs import VaultRepairFlow, async_create_fix_flow
from homeassistant.core import HomeAssistant
from homeassistant.helpers import issue_registry as ir


async def test_create_fix_flow(hass: HomeAssistant) -> None:
    """Test async_create_fix_flow returns a VaultRepairFlow."""
    flow = await async_create_fix_flow(hass, "test_issue", None)
    assert isinstance(flow, VaultRepairFlow)


async def test_repair_flow_init_shows_form(hass: HomeAssistant) -> None:
    """Test repair flow init step shows a form."""
    flow = VaultRepairFlow()
    flow.hass = hass
    flow.issue_id = "test_issue"

    result = await flow.async_step_init(user_input=None)
    assert result["type"] == "form"
    assert result["step_id"] == "init"


async def test_repair_flow_init_with_input_deletes_issue(hass: HomeAssistant) -> None:
    """Test repair flow with user input deletes the issue and creates entry."""
    ir.async_create_issue(
        hass,
        DOMAIN,
        "test_issue",
        is_fixable=True,
        severity=ir.IssueSeverity.WARNING,
        translation_key="test",
    )

    flow = VaultRepairFlow()
    flow.hass = hass
    flow.issue_id = "test_issue"

    result = await flow.async_step_init(user_input={})
    assert result["type"] == "create_entry"

    # Check the issue was deleted
    registry = ir.async_get(hass)
    issue = registry.async_get_issue(DOMAIN, "test_issue")
    assert issue is None
