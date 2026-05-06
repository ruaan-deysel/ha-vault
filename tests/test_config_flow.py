"""Tests for the Vault config flow."""

from __future__ import annotations

from unittest.mock import AsyncMock, MagicMock, patch

from pytest_homeassistant_custom_component.common import MockConfigEntry

from custom_components.vault.api.exceptions import VaultAuthenticationError, VaultConnectionError
from custom_components.vault.api.models import HealthStatus
from custom_components.vault.const import DOMAIN
from homeassistant.config_entries import SOURCE_USER
from homeassistant.core import HomeAssistant
from homeassistant.data_entry_flow import FlowResultType


def _make_mock_client(
    *,
    health: HealthStatus | None = None,
    health_side_effect: Exception | None = None,
) -> MagicMock:
    """Create a mock VaultApiClient with common defaults."""
    mock_client = MagicMock()
    if health_side_effect:
        mock_client.async_get_health = AsyncMock(side_effect=health_side_effect)
    else:
        mock_client.async_get_health = AsyncMock(return_value=health or HealthStatus(status="ok", version="1.0.0"))
    return mock_client


async def test_user_step_success(hass: HomeAssistant) -> None:
    """Test successful user step creates config entry (no auth required)."""
    with patch(
        "custom_components.vault.config_flow.VaultApiClient",
    ) as mock_client_class:
        mock_client_class.return_value = _make_mock_client()

        result = await hass.config_entries.flow.async_init(DOMAIN, context={"source": SOURCE_USER})
        assert result["type"] is FlowResultType.FORM
        assert result["step_id"] == "user"

        result = await hass.config_entries.flow.async_configure(
            result["flow_id"],
            user_input={"host": "192.168.1.100", "port": 24085, "tls": False},
        )
        assert result["type"] is FlowResultType.CREATE_ENTRY
        assert result["title"] == "Vault (1.0.0)"
        assert result["data"] == {"host": "192.168.1.100", "port": 24085, "tls": False}


async def test_user_step_auth_required(hass: HomeAssistant) -> None:
    """Test user step redirects to auth step when auth is required."""
    with patch(
        "custom_components.vault.config_flow.VaultApiClient",
    ) as mock_client_class:
        # Step 1: health requires authentication
        mock_client_class.return_value = _make_mock_client(
            health_side_effect=VaultAuthenticationError("auth required"),
        )

        result = await hass.config_entries.flow.async_init(DOMAIN, context={"source": SOURCE_USER})
        result = await hass.config_entries.flow.async_configure(
            result["flow_id"],
            user_input={"host": "192.168.1.100", "port": 24085, "tls": False},
        )
        assert result["type"] is FlowResultType.FORM
        assert result["step_id"] == "auth"

        # Step 2: provide valid API key
        mock_client_class.return_value = _make_mock_client()

        result = await hass.config_entries.flow.async_configure(
            result["flow_id"],
            user_input={"api_key": "test-secret-key"},
        )
        assert result["type"] is FlowResultType.CREATE_ENTRY
        assert result["data"]["api_key"] == "test-secret-key"
        assert result["data"]["tls"] is False


async def test_auth_step_invalid_key(hass: HomeAssistant) -> None:
    """Test auth step shows error on invalid API key."""
    with patch(
        "custom_components.vault.config_flow.VaultApiClient",
    ) as mock_client_class:
        # Step 1: health requires authentication
        mock_client_class.return_value = _make_mock_client(
            health_side_effect=VaultAuthenticationError("auth required"),
        )

        result = await hass.config_entries.flow.async_init(DOMAIN, context={"source": SOURCE_USER})
        result = await hass.config_entries.flow.async_configure(
            result["flow_id"],
            user_input={"host": "192.168.1.100", "port": 24085, "tls": False},
        )
        assert result["step_id"] == "auth"

        # Step 2: bad API key
        mock_client_class.return_value = _make_mock_client(
            health_side_effect=VaultAuthenticationError("bad key"),
        )

        result = await hass.config_entries.flow.async_configure(
            result["flow_id"],
            user_input={"api_key": "wrong-key"},
        )
        assert result["type"] is FlowResultType.FORM
        assert result["errors"] == {"base": "invalid_auth"}


async def test_auth_step_connection_error(hass: HomeAssistant) -> None:
    """Test auth step shows error on connection failure."""
    with patch(
        "custom_components.vault.config_flow.VaultApiClient",
    ) as mock_client_class:
        mock_client_class.return_value = _make_mock_client(
            health_side_effect=VaultAuthenticationError("auth required"),
        )

        result = await hass.config_entries.flow.async_init(DOMAIN, context={"source": SOURCE_USER})
        result = await hass.config_entries.flow.async_configure(
            result["flow_id"],
            user_input={"host": "192.168.1.100", "port": 24085, "tls": False},
        )
        assert result["step_id"] == "auth"

        mock_client_class.return_value = _make_mock_client(
            health_side_effect=VaultConnectionError("timeout"),
        )

        result = await hass.config_entries.flow.async_configure(
            result["flow_id"],
            user_input={"api_key": "some-key"},
        )
        assert result["type"] is FlowResultType.FORM
        assert result["errors"] == {"base": "cannot_connect"}


async def test_auth_step_unknown_error(hass: HomeAssistant) -> None:
    """Test auth step shows error on unknown exception."""
    with patch(
        "custom_components.vault.config_flow.VaultApiClient",
    ) as mock_client_class:
        mock_client_class.return_value = _make_mock_client(
            health_side_effect=VaultAuthenticationError("auth required"),
        )

        result = await hass.config_entries.flow.async_init(DOMAIN, context={"source": SOURCE_USER})
        result = await hass.config_entries.flow.async_configure(
            result["flow_id"],
            user_input={"host": "192.168.1.100", "port": 24085, "tls": False},
        )
        assert result["step_id"] == "auth"

        mock_client_class.return_value = _make_mock_client(
            health_side_effect=RuntimeError("boom"),
        )

        result = await hass.config_entries.flow.async_configure(
            result["flow_id"],
            user_input={"api_key": "some-key"},
        )
        assert result["type"] is FlowResultType.FORM
        assert result["errors"] == {"base": "unknown"}


async def test_user_step_cannot_connect(hass: HomeAssistant) -> None:
    """Test user step shows error on connection failure."""
    with patch(
        "custom_components.vault.config_flow.VaultApiClient",
    ) as mock_client_class:
        mock_client_class.return_value = _make_mock_client(
            health_side_effect=VaultConnectionError("timeout"),
        )

        result = await hass.config_entries.flow.async_init(DOMAIN, context={"source": SOURCE_USER})
        result = await hass.config_entries.flow.async_configure(
            result["flow_id"],
            user_input={"host": "192.168.1.100", "port": 24085, "tls": False},
        )
        assert result["type"] is FlowResultType.FORM
        assert result["errors"] == {"base": "cannot_connect"}


async def test_user_step_unknown_error(hass: HomeAssistant) -> None:
    """Test user step shows error on unknown exception."""
    with patch(
        "custom_components.vault.config_flow.VaultApiClient",
    ) as mock_client_class:
        mock_client_class.return_value = _make_mock_client(
            health_side_effect=RuntimeError("unexpected"),
        )

        result = await hass.config_entries.flow.async_init(DOMAIN, context={"source": SOURCE_USER})
        result = await hass.config_entries.flow.async_configure(
            result["flow_id"],
            user_input={"host": "192.168.1.100", "port": 24085, "tls": False},
        )
        assert result["type"] is FlowResultType.FORM
        assert result["errors"] == {"base": "unknown"}


async def test_user_step_already_configured(hass: HomeAssistant) -> None:
    """Test user step aborts if already configured."""
    entry = MockConfigEntry(
        domain=DOMAIN,
        data={"host": "192.168.1.100", "port": 24085},
        unique_id="192.168.1.100:24085",
    )
    entry.add_to_hass(hass)

    with patch(
        "custom_components.vault.config_flow.VaultApiClient",
    ) as mock_client_class:
        mock_client_class.return_value = _make_mock_client()

        result = await hass.config_entries.flow.async_init(DOMAIN, context={"source": SOURCE_USER})
        result = await hass.config_entries.flow.async_configure(
            result["flow_id"],
            user_input={"host": "192.168.1.100", "port": 24085, "tls": False},
        )
        assert result["type"] is FlowResultType.ABORT
        assert result["reason"] == "already_configured"


async def test_user_step_tls_enabled(hass: HomeAssistant) -> None:
    """Test user step with TLS enabled."""
    with patch(
        "custom_components.vault.config_flow.VaultApiClient",
    ) as mock_client_class:
        mock_client_class.return_value = _make_mock_client()

        result = await hass.config_entries.flow.async_init(DOMAIN, context={"source": SOURCE_USER})
        result = await hass.config_entries.flow.async_configure(
            result["flow_id"],
            user_input={"host": "192.168.1.100", "port": 24085, "tls": True},
        )
        assert result["type"] is FlowResultType.CREATE_ENTRY
        assert result["data"]["tls"] is True
        # Verify client was created with tls=True
        mock_client_class.assert_called_with(
            host="192.168.1.100", port=24085, session=mock_client_class.call_args.kwargs["session"], tls=True
        )


async def test_reauth_step_success(
    hass: HomeAssistant,
    mock_config_entry: MockConfigEntry,
) -> None:
    """Test successful reauth flow."""
    mock_config_entry.add_to_hass(hass)

    with patch(
        "custom_components.vault.config_flow.VaultApiClient",
    ) as mock_client_class:
        mock_client_class.return_value = _make_mock_client()

        result = await mock_config_entry.start_reauth_flow(hass)
        assert result["type"] is FlowResultType.FORM
        assert result["step_id"] == "reauth_confirm"

        result = await hass.config_entries.flow.async_configure(
            result["flow_id"],
            user_input={"api_key": "new-api-key"},
        )
        assert result["type"] is FlowResultType.ABORT
        assert result["reason"] == "reauth_successful"


async def test_reauth_step_invalid_auth(
    hass: HomeAssistant,
    mock_config_entry: MockConfigEntry,
) -> None:
    """Test reauth step shows error on invalid key."""
    mock_config_entry.add_to_hass(hass)

    with patch(
        "custom_components.vault.config_flow.VaultApiClient",
    ) as mock_client_class:
        mock_client_class.return_value = _make_mock_client(
            health_side_effect=VaultAuthenticationError("bad key"),
        )

        result = await mock_config_entry.start_reauth_flow(hass)
        result = await hass.config_entries.flow.async_configure(
            result["flow_id"],
            user_input={"api_key": "wrong-key"},
        )
        assert result["type"] is FlowResultType.FORM
        assert result["errors"] == {"base": "invalid_auth"}


async def test_reauth_step_cannot_connect(
    hass: HomeAssistant,
    mock_config_entry: MockConfigEntry,
) -> None:
    """Test reauth step shows error on connection failure."""
    mock_config_entry.add_to_hass(hass)

    with patch(
        "custom_components.vault.config_flow.VaultApiClient",
    ) as mock_client_class:
        mock_client_class.return_value = _make_mock_client(
            health_side_effect=VaultConnectionError("timeout"),
        )

        result = await mock_config_entry.start_reauth_flow(hass)
        result = await hass.config_entries.flow.async_configure(
            result["flow_id"],
            user_input={"api_key": "some-key"},
        )
        assert result["type"] is FlowResultType.FORM
        assert result["errors"] == {"base": "cannot_connect"}


async def test_reauth_step_unknown_error(
    hass: HomeAssistant,
    mock_config_entry: MockConfigEntry,
) -> None:
    """Test reauth step shows error on unknown exception."""
    mock_config_entry.add_to_hass(hass)

    with patch(
        "custom_components.vault.config_flow.VaultApiClient",
    ) as mock_client_class:
        mock_client_class.return_value = _make_mock_client(
            health_side_effect=RuntimeError("unknown"),
        )

        result = await mock_config_entry.start_reauth_flow(hass)
        result = await hass.config_entries.flow.async_configure(
            result["flow_id"],
            user_input={"api_key": "some-key"},
        )
        assert result["type"] is FlowResultType.FORM
        assert result["errors"] == {"base": "unknown"}


async def test_reconfigure_step_success(
    hass: HomeAssistant,
    mock_config_entry: MockConfigEntry,
) -> None:
    """Test successful reconfigure step."""
    mock_config_entry.add_to_hass(hass)

    with patch(
        "custom_components.vault.config_flow.VaultApiClient",
    ) as mock_client_class:
        mock_client_class.return_value = _make_mock_client()

        result = await mock_config_entry.start_reconfigure_flow(hass)
        assert result["type"] is FlowResultType.FORM
        assert result["step_id"] == "reconfigure"

        result = await hass.config_entries.flow.async_configure(
            result["flow_id"],
            user_input={"host": "10.0.0.1", "port": 9999, "tls": True, "api_key": "my-key"},
        )
        assert result["type"] is FlowResultType.ABORT
        assert result["reason"] == "reconfigure_successful"


async def test_reconfigure_step_invalid_auth(
    hass: HomeAssistant,
    mock_config_entry: MockConfigEntry,
) -> None:
    """Test reconfigure step shows error on invalid auth."""
    mock_config_entry.add_to_hass(hass)

    with patch(
        "custom_components.vault.config_flow.VaultApiClient",
    ) as mock_client_class:
        mock_client_class.return_value = _make_mock_client(
            health_side_effect=VaultAuthenticationError("bad"),
        )

        result = await mock_config_entry.start_reconfigure_flow(hass)
        result = await hass.config_entries.flow.async_configure(
            result["flow_id"],
            user_input={"host": "10.0.0.1", "port": 9999, "tls": False, "api_key": "bad-key"},
        )
        assert result["type"] is FlowResultType.FORM
        assert result["errors"] == {"base": "invalid_auth"}


async def test_reconfigure_step_cannot_connect(
    hass: HomeAssistant,
    mock_config_entry: MockConfigEntry,
) -> None:
    """Test reconfigure step shows error on connection failure."""
    mock_config_entry.add_to_hass(hass)

    with patch(
        "custom_components.vault.config_flow.VaultApiClient",
    ) as mock_client_class:
        mock_client_class.return_value = _make_mock_client(
            health_side_effect=VaultConnectionError("timeout"),
        )

        result = await mock_config_entry.start_reconfigure_flow(hass)
        result = await hass.config_entries.flow.async_configure(
            result["flow_id"],
            user_input={"host": "10.0.0.1", "port": 9999},
        )
        assert result["type"] is FlowResultType.FORM
        assert result["errors"] == {"base": "cannot_connect"}


async def test_reconfigure_step_unknown_error(
    hass: HomeAssistant,
    mock_config_entry: MockConfigEntry,
) -> None:
    """Test reconfigure step shows error on unknown exception."""
    mock_config_entry.add_to_hass(hass)

    with patch(
        "custom_components.vault.config_flow.VaultApiClient",
    ) as mock_client_class:
        mock_client_class.return_value = _make_mock_client(
            health_side_effect=RuntimeError("unexpected"),
        )

        result = await mock_config_entry.start_reconfigure_flow(hass)
        result = await hass.config_entries.flow.async_configure(
            result["flow_id"],
            user_input={"host": "10.0.0.1", "port": 9999},
        )
        assert result["type"] is FlowResultType.FORM
        assert result["errors"] == {"base": "unknown"}


async def test_user_step_auth_status_check_fails(hass: HomeAssistant) -> None:
    """Test user step proceeds without auth when auth_status check fails."""
    with patch(
        "custom_components.vault.config_flow.VaultApiClient",
    ) as mock_client_class:
        mock_client = _make_mock_client()
        mock_client.async_get_auth_status = AsyncMock(side_effect=VaultConnectionError("auth check failed"))
        mock_client_class.return_value = mock_client

        result = await hass.config_entries.flow.async_init(DOMAIN, context={"source": SOURCE_USER})
        result = await hass.config_entries.flow.async_configure(
            result["flow_id"],
            user_input={"host": "192.168.1.100", "port": 24085, "tls": False},
        )
        # Should still create entry since auth check failure is non-fatal
        assert result["type"] is FlowResultType.CREATE_ENTRY
