"""Constants for the Vault integration."""

from logging import Logger, getLogger

LOGGER: Logger = getLogger(__package__)

DOMAIN = "vault"

# Config entry keys
CONF_HOST = "host"
CONF_PORT = "port"
CONF_API_KEY = "api_key"
CONF_TLS = "tls"

# Defaults
DEFAULT_PORT = 24085
DEFAULT_UPDATE_INTERVAL_SECONDS = 60
ACTIVE_UPDATE_INTERVAL_SECONDS = 10
