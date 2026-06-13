"""WebSocket client for Vault real-time events."""

from __future__ import annotations

import asyncio
from collections.abc import Callable
import contextlib
from logging import Logger
from typing import Any

import aiohttp

from .models import WebSocketEvent

# Map Vault WS message types → HA event types
_WS_TO_HA_EVENT: dict[str, str] = {
    "job_run_started": "vault_backup_started",
    "item_backup_start": "vault_backup_item_start",
    "backup_progress": "vault_backup_progress",
    "item_backup_done": "vault_backup_item_done",
    "item_backup_failed": "vault_backup_item_failed",
    "job_run_completed": "vault_backup_completed",
    "item_restore_start": "vault_restore_item_start",
    "item_restore_done": "vault_restore_item_done",
    "item_restore_failed": "vault_restore_item_failed",
    "restore_progress": "vault_restore_progress",
    "verify_started": "vault_verify_started",
    "verify_progress": "vault_verify_progress",
    "verify_complete": "vault_verify_complete",
    "queue_update": "vault_queue_update",
    "job_cancelling": "vault_job_cancelling",
    "storage_health": "vault_storage_health",
    "storage_capacity_updated": "vault_storage_capacity",
    "dedup_gc_complete": "vault_dedup_gc_complete",
    "import_completed": "vault_import_completed",
    "config_changed": "vault_config_changed",
    "activity": "vault_activity",
    "stale_items_detected": "vault_stale_items_detected",
    "anomaly.raised": "vault_anomaly_raised",
    "anomaly.updated": "vault_anomaly_updated",
    "anomaly.resolved": "vault_anomaly_resolved",
    "anomaly.acknowledged": "vault_anomaly_acknowledged",
    "baseline.updated": "vault_baseline_updated",
}


class VaultWebSocketClient:
    """Manages a persistent WebSocket connection to the Vault instance.

    Receives real-time events (job started/completed, errors, etc.)
    and dispatches them to registered listeners.
    """

    def __init__(
        self,
        host: str,
        port: int,
        session: aiohttp.ClientSession,
        logger: Logger,
        *,
        api_key: str | None = None,
        tls: bool = False,
    ) -> None:
        """Initialize the WebSocket client.

        Args:
            host: Hostname or IP of the Vault instance.
            port: Port number of the Vault API.
            session: aiohttp session provided by Home Assistant.
            logger: Logger instance.
            api_key: Optional API key for authentication.
            tls: Whether to use WSS instead of WS.
        """
        scheme = "wss" if tls else "ws"
        url = f"{scheme}://{host}:{port}/api/v1/ws"
        self._url = url
        self._log_url = url
        self._headers: dict[str, str] | None = None
        if api_key:
            self._headers = {
                "X-API-Key": api_key,
                "Authorization": f"Bearer {api_key}",
            }
        self._session = session
        self._logger = logger
        self._ws: aiohttp.ClientWebSocketResponse | None = None
        self._listeners: list[Callable[[WebSocketEvent], None]] = []
        self._task: asyncio.Task[None] | None = None
        self._running = False

    def register_listener(self, callback: Callable[[WebSocketEvent], None]) -> Callable[[], None]:
        """Register a callback for incoming WebSocket events.

        Args:
            callback: Function called with each WebSocketEvent.

        Returns:
            A callable that removes the listener when called.
        """
        self._listeners.append(callback)

        def remove() -> None:
            self._listeners.remove(callback)

        return remove

    async def async_connect(self) -> None:
        """Start the WebSocket connection and begin listening."""
        if self._running:
            return
        self._running = True
        self._task = asyncio.create_task(self._listen_loop())

    async def async_disconnect(self) -> None:
        """Close the WebSocket connection and stop listening."""
        self._running = False
        if self._ws and not self._ws.closed:
            await self._ws.close()
        if self._task and not self._task.done():
            self._task.cancel()
            with contextlib.suppress(asyncio.CancelledError):
                await self._task
        self._ws = None
        self._task = None

    @property
    def connected(self) -> bool:
        """Return True if the WebSocket is connected."""
        return self._ws is not None and not self._ws.closed

    async def _listen_loop(self) -> None:
        """Main loop: connect, read messages, reconnect on failure."""
        retry_delay = 5

        while self._running:
            try:
                self._logger.debug("Connecting to Vault WebSocket at %s", self._log_url)
                self._ws = await self._session.ws_connect(self._url, heartbeat=30, headers=self._headers)
                retry_delay = 5  # Reset on successful connect

                async for msg in self._ws:
                    if not self._running:
                        break
                    if msg.type == aiohttp.WSMsgType.TEXT:
                        self._handle_message(msg.data)
                    elif msg.type == aiohttp.WSMsgType.ERROR:
                        self._logger.warning("WebSocket error: %s", self._ws.exception())
                        break
                    elif msg.type in (aiohttp.WSMsgType.CLOSE, aiohttp.WSMsgType.CLOSING, aiohttp.WSMsgType.CLOSED):
                        break

            except (aiohttp.ClientError, TimeoutError) as err:
                self._logger.debug("WebSocket connection failed: %s", err)

            if self._running:
                self._logger.debug("Reconnecting in %s seconds", retry_delay)
                await asyncio.sleep(retry_delay)
                retry_delay = min(retry_delay * 2, 60)

    def _handle_message(self, raw: Any) -> None:
        """Parse a raw WebSocket text message and dispatch to listeners."""
        try:
            event = WebSocketEvent.model_validate_json(raw)
        except (ValueError, TypeError):
            self._logger.debug("Ignoring unparsable WebSocket message: %s", raw)
            return

        for listener in self._listeners:
            try:
                listener(event)
            except (ValueError, TypeError, AttributeError):
                self._logger.exception("Error in WebSocket event listener")

    @staticmethod
    def get_ha_event_type(ws_type: str) -> str | None:
        """Map a Vault WS message type to an HA event type, or None if unmapped."""
        return _WS_TO_HA_EVENT.get(ws_type)
