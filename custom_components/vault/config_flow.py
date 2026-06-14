"""Config flow for the Vault integration."""

from __future__ import annotations

from typing import Any

import voluptuous as vol

from homeassistant.config_entries import ConfigFlow, ConfigFlowResult
from homeassistant.helpers.aiohttp_client import async_get_clientsession

from .api import VaultApiClient, VaultAuthenticationError, VaultConnectionError
from .const import CONF_API_KEY, CONF_HOST, CONF_PORT, CONF_TLS, DEFAULT_PORT, DOMAIN

STEP_USER_DATA_SCHEMA = vol.Schema(
    {
        vol.Required(CONF_HOST): str,
        vol.Required(CONF_PORT, default=DEFAULT_PORT): vol.Coerce(int),
        vol.Optional(CONF_TLS, default=False): bool,
    }
)

STEP_AUTH_DATA_SCHEMA = vol.Schema(
    {
        vol.Required(CONF_API_KEY): str,
    }
)


class VaultConfigFlow(ConfigFlow, domain=DOMAIN):
    """Handle a config flow for Vault."""

    VERSION = 1

    def __init__(self) -> None:
        """Initialize the config flow."""
        self._user_input: dict[str, Any] = {}
        self._health_version: str | None = None

    # ------------------------------------------------------------------
    # Step 1: User provides host, port, and TLS toggle
    # ------------------------------------------------------------------

    async def async_step_user(
        self,
        user_input: dict[str, Any] | None = None,
    ) -> ConfigFlowResult:
        """Handle the initial step — user provides host, port, and TLS option."""
        errors: dict[str, str] = {}

        if user_input is not None:
            host = user_input[CONF_HOST].strip()
            port: int = user_input[CONF_PORT]
            tls: bool = user_input.get(CONF_TLS, False)
            session = async_get_clientsession(self.hass)
            client = VaultApiClient(host=host, port=port, session=session, tls=tls)

            try:
                health = await client.async_get_health()
            except VaultAuthenticationError:
                self._user_input = {CONF_HOST: host, CONF_PORT: port, CONF_TLS: tls}
                return await self.async_step_auth()
            except VaultConnectionError:
                errors["base"] = "cannot_connect"
            except Exception:  # noqa: BLE001
                errors["base"] = "unknown"
            else:
                self._user_input = {CONF_HOST: host, CONF_PORT: port, CONF_TLS: tls}
                self._health_version = health.version

                # No auth required — create entry directly
                unique_id = f"{host}:{port}"
                await self.async_set_unique_id(unique_id)
                self._abort_if_unique_id_configured()
                return self.async_create_entry(
                    title=f"Vault ({health.version})" if health.version else f"Vault ({host})",
                    data=self._user_input,
                )

        return self.async_show_form(
            step_id="user",
            data_schema=STEP_USER_DATA_SCHEMA,
            errors=errors,
        )

    # ------------------------------------------------------------------
    # Step 2: Zeroconf discovery — auto-discovered instance confirmation
    # ------------------------------------------------------------------

    async def async_step_zeroconf(
        self,
        discovery_info: dict[str, Any],
    ) -> ConfigFlowResult:
        """Handle zeroconf discovery of Vault instances."""
        # Extract host and port from discovery info
        host = discovery_info.get("host", "")
        port = discovery_info.get("port", DEFAULT_PORT)

        # Read TLS flag and API path from TXT records
        properties = discovery_info.get("properties", {})
        tls = properties.get("tls", "false").lower() == "true"

        # Set unique ID and check for duplicates
        unique_id = f"{host}:{port}"
        await self.async_set_unique_id(unique_id)
        self._abort_if_unique_id_configured()

        # Store discovery info for potential reuse
        self._user_input = {CONF_HOST: host, CONF_PORT: port, CONF_TLS: tls}

        # Try to validate connection
        session = async_get_clientsession(self.hass)
        client = VaultApiClient(host=host, port=port, session=session, tls=tls)

        try:
            health = await client.async_get_health()
        except VaultAuthenticationError:
            # Auth required — proceed to auth step
            return await self.async_step_zeroconf_confirm()
        except (VaultConnectionError, Exception):  # noqa: BLE001
            # Connection failed — abort discovery
            return self.async_abort(reason="cannot_connect")

        # Connection successful, no auth needed — create entry
        self._health_version = health.version
        return self.async_create_entry(
            title=f"Vault ({health.version})" if health.version else f"Vault ({host})",
            data=self._user_input,
        )

    async def async_step_zeroconf_confirm(
        self,
        user_input: dict[str, Any] | None = None,
    ) -> ConfigFlowResult:
        """Confirmation step for zeroconf discovery (may require auth)."""
        errors: dict[str, str] = {}

        if user_input is not None:
            # User provided API key if needed
            api_key = user_input.get(CONF_API_KEY, "").strip()
            if api_key:
                self._user_input[CONF_API_KEY] = api_key

            # Validate with API key
            host = self._user_input[CONF_HOST]
            port = self._user_input[CONF_PORT]
            tls = self._user_input.get(CONF_TLS, False)
            session = async_get_clientsession(self.hass)
            client = VaultApiClient(
                host=host,
                port=port,
                session=session,
                tls=tls,
                api_key=self._user_input.get(CONF_API_KEY),
            )

            try:
                health = await client.async_get_health()
            except VaultConnectionError:
                errors["base"] = "cannot_connect"
            except VaultAuthenticationError:
                errors["base"] = "invalid_auth"
            except Exception:  # noqa: BLE001
                errors["base"] = "unknown"
            else:
                self._health_version = health.version
                return self.async_create_entry(
                    title=f"Vault ({health.version})" if health.version else f"Vault ({host})",
                    data=self._user_input,
                )

        # Show confirmation form with optional API key field
        return self.async_show_form(
            step_id="zeroconf_confirm",
            data_schema=vol.Schema(
                {
                    vol.Optional(CONF_API_KEY): str,
                }
            ),
            errors=errors,
            description_placeholders={
                "host": self._user_input[CONF_HOST],
                "port": str(self._user_input[CONF_PORT]),
            },
        )

    # ------------------------------------------------------------------
    # Step 3: Auth — user provides API key (only if auth required)
    # ------------------------------------------------------------------

    async def async_step_auth(
        self,
        user_input: dict[str, Any] | None = None,
    ) -> ConfigFlowResult:
        """Handle the authentication step — user provides API key."""
        errors: dict[str, str] = {}

        if user_input is not None:
            api_key = user_input[CONF_API_KEY].strip()
            host = self._user_input[CONF_HOST]
            port = self._user_input[CONF_PORT]
            tls = self._user_input.get(CONF_TLS, False)
            session = async_get_clientsession(self.hass)
            client = VaultApiClient(host=host, port=port, session=session, api_key=api_key, tls=tls)

            try:
                await client.async_get_health()
            except VaultAuthenticationError:
                errors["base"] = "invalid_auth"
            except VaultConnectionError:
                errors["base"] = "cannot_connect"
            except Exception:  # noqa: BLE001
                errors["base"] = "unknown"
            else:
                unique_id = f"{host}:{port}"
                await self.async_set_unique_id(unique_id)
                self._abort_if_unique_id_configured()
                entry_data = {**self._user_input, CONF_API_KEY: api_key}
                title = f"Vault ({self._health_version})" if self._health_version else f"Vault ({host})"
                return self.async_create_entry(title=title, data=entry_data)

        return self.async_show_form(
            step_id="auth",
            data_schema=STEP_AUTH_DATA_SCHEMA,
            errors=errors,
        )

    # ------------------------------------------------------------------
    # Reauth — triggered when ConfigEntryAuthFailed is raised
    # ------------------------------------------------------------------

    async def async_step_reauth(
        self,
        entry_data: dict[str, Any],
    ) -> ConfigFlowResult:
        """Handle reauth trigger — show the reauth confirm form."""
        return await self.async_step_reauth_confirm()

    async def async_step_reauth_confirm(
        self,
        user_input: dict[str, Any] | None = None,
    ) -> ConfigFlowResult:
        """Handle the reauth confirm step — user provides new API key."""
        errors: dict[str, str] = {}

        if user_input is not None:
            api_key = user_input[CONF_API_KEY].strip()
            entry = self._get_reauth_entry()
            host = entry.data[CONF_HOST]
            port = entry.data.get(CONF_PORT, DEFAULT_PORT)
            tls = entry.data.get(CONF_TLS, False)
            session = async_get_clientsession(self.hass)
            client = VaultApiClient(host=host, port=port, session=session, api_key=api_key, tls=tls)

            try:
                await client.async_get_health()
            except VaultAuthenticationError:
                errors["base"] = "invalid_auth"
            except VaultConnectionError:
                errors["base"] = "cannot_connect"
            except Exception:  # noqa: BLE001
                errors["base"] = "unknown"
            else:
                return self.async_update_reload_and_abort(
                    entry,
                    data_updates={CONF_API_KEY: api_key},
                )

        return self.async_show_form(
            step_id="reauth_confirm",
            data_schema=STEP_AUTH_DATA_SCHEMA,
            errors=errors,
        )

    # ------------------------------------------------------------------
    # Reconfigure — update host, port, TLS, and optionally API key
    # ------------------------------------------------------------------

    async def async_step_reconfigure(
        self,
        user_input: dict[str, Any] | None = None,
    ) -> ConfigFlowResult:
        """Handle reconfiguration of the Vault connection."""
        errors: dict[str, str] = {}

        if user_input is not None:
            host = user_input[CONF_HOST].strip()
            port: int = user_input[CONF_PORT]
            tls: bool = user_input.get(CONF_TLS, False)
            api_key: str | None = user_input.get(CONF_API_KEY, "").strip() or None
            session = async_get_clientsession(self.hass)
            client = VaultApiClient(host=host, port=port, session=session, api_key=api_key, tls=tls)

            try:
                await client.async_get_health()
            except VaultAuthenticationError:
                errors["base"] = "invalid_auth"
            except VaultConnectionError:
                errors["base"] = "cannot_connect"
            except Exception:  # noqa: BLE001
                errors["base"] = "unknown"
            else:
                entry = self._get_reconfigure_entry()
                unique_id = f"{host}:{port}"
                # Keep the unique_id in sync with the (possibly new) host:port,
                # but never collide with another configured entry.
                if any(
                    other.unique_id == unique_id and other.entry_id != entry.entry_id
                    for other in self.hass.config_entries.async_entries(DOMAIN)
                ):
                    return self.async_abort(reason="already_configured")
                data_updates: dict[str, Any] = {CONF_HOST: host, CONF_PORT: port, CONF_TLS: tls}
                if api_key:
                    data_updates[CONF_API_KEY] = api_key
                return self.async_update_reload_and_abort(
                    entry,
                    unique_id=unique_id,
                    data_updates=data_updates,
                )

        existing = self._get_reconfigure_entry().data
        return self.async_show_form(
            step_id="reconfigure",
            data_schema=vol.Schema(
                {
                    vol.Required(CONF_HOST, default=existing.get(CONF_HOST, "")): str,
                    vol.Required(CONF_PORT, default=existing.get(CONF_PORT, DEFAULT_PORT)): vol.Coerce(int),
                    vol.Optional(CONF_TLS, default=existing.get(CONF_TLS, False)): bool,
                    vol.Optional(CONF_API_KEY, default=existing.get(CONF_API_KEY, "")): str,
                }
            ),
            errors=errors,
        )
