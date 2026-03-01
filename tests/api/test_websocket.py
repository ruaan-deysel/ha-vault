"""Tests for the Vault WebSocket client."""

from __future__ import annotations

import asyncio
from collections.abc import AsyncGenerator
import logging
from unittest.mock import AsyncMock, MagicMock, patch

import aiohttp
import pytest

from custom_components.vault.api.models import WebSocketEvent
from custom_components.vault.api.websocket import VaultWebSocketClient


@pytest.fixture
def ws_client() -> VaultWebSocketClient:
    """Create a VaultWebSocketClient with a mock session."""
    session = MagicMock(spec=aiohttp.ClientSession)
    return VaultWebSocketClient(
        host="192.168.1.100",
        port=24085,
        session=session,
        logger=logging.getLogger("test"),
    )


class TestWebSocketInit:
    """Test WebSocket client initialization."""

    def test_url(self, ws_client: VaultWebSocketClient) -> None:
        """Test URL construction."""
        assert ws_client._url == "ws://192.168.1.100:24085/api/v1/ws"  # noqa: SLF001

    def test_not_connected_initially(self, ws_client: VaultWebSocketClient) -> None:
        """Test not connected initially."""
        assert ws_client.connected is False


class TestListenerRegistration:
    """Test listener registration."""

    def test_register_listener(self, ws_client: VaultWebSocketClient) -> None:
        """Test registering a listener returns a removal function."""
        callback = MagicMock()
        remove = ws_client.register_listener(callback)
        assert callback in ws_client._listeners  # noqa: SLF001
        remove()
        assert callback not in ws_client._listeners  # noqa: SLF001


class TestEventMapping:
    """Test WS-to-HA event type mapping."""

    def test_known_events(self) -> None:
        """Test known event mappings."""
        assert VaultWebSocketClient.get_ha_event_type("job_run_started") == "vault_backup_started"
        assert VaultWebSocketClient.get_ha_event_type("job_run_completed") == "vault_backup_completed"
        assert VaultWebSocketClient.get_ha_event_type("backup_progress") == "vault_backup_progress"

    def test_unknown_event(self) -> None:
        """Test unknown event returns None."""
        assert VaultWebSocketClient.get_ha_event_type("unknown_type") is None


class TestMessageHandling:
    """Test message handling."""

    def test_valid_message(self, ws_client: VaultWebSocketClient) -> None:
        """Test valid JSON message dispatches to listeners."""
        callback = MagicMock()
        ws_client.register_listener(callback)
        ws_client._handle_message('{"type": "job_run_started", "job_id": 1}')  # noqa: SLF001
        callback.assert_called_once()
        event = callback.call_args[0][0]
        assert isinstance(event, WebSocketEvent)
        assert event.type == "job_run_started"
        assert event.job_id == 1

    def test_invalid_message(self, ws_client: VaultWebSocketClient) -> None:
        """Test invalid JSON message is ignored."""
        callback = MagicMock()
        ws_client.register_listener(callback)
        ws_client._handle_message("not valid json")  # noqa: SLF001
        callback.assert_not_called()

    def test_listener_error_does_not_crash(self, ws_client: VaultWebSocketClient) -> None:
        """Test that a listener raising an error does not crash."""
        bad_callback = MagicMock(side_effect=ValueError("test"))
        good_callback = MagicMock()
        ws_client.register_listener(bad_callback)
        ws_client.register_listener(good_callback)
        ws_client._handle_message('{"type": "test"}')  # noqa: SLF001
        bad_callback.assert_called_once()
        good_callback.assert_called_once()


class TestConnectDisconnect:
    """Test connect/disconnect lifecycle."""

    async def test_connect(self, ws_client: VaultWebSocketClient) -> None:
        """Test async_connect starts listening."""
        ws_client._session.ws_connect = AsyncMock(side_effect=aiohttp.ClientError("test"))  # noqa: SLF001
        await ws_client.async_connect()
        assert ws_client._running is True  # noqa: SLF001
        # Clean up
        await ws_client.async_disconnect()

    async def test_disconnect(self, ws_client: VaultWebSocketClient) -> None:
        """Test async_disconnect cleans up."""
        ws_client._running = True  # noqa: SLF001
        ws_client._ws = MagicMock()  # noqa: SLF001
        ws_client._ws.closed = False  # noqa: SLF001
        ws_client._ws.close = AsyncMock()  # noqa: SLF001
        ws_client._task = asyncio.create_task(asyncio.sleep(10))  # noqa: SLF001
        await ws_client.async_disconnect()
        assert ws_client._running is False  # noqa: SLF001
        assert ws_client._ws is None  # noqa: SLF001
        assert ws_client._task is None  # noqa: SLF001

    async def test_double_connect(self, ws_client: VaultWebSocketClient) -> None:
        """Test double connect is a no-op."""
        ws_client._running = True  # noqa: SLF001
        ws_client._session.ws_connect = AsyncMock(side_effect=aiohttp.ClientError("test"))  # noqa: SLF001
        await ws_client.async_connect()
        # Should not create a new task
        assert ws_client._task is None  # noqa: SLF001


class TestListenLoop:
    """Test the _listen_loop method."""

    async def test_text_message_dispatched(self, ws_client: VaultWebSocketClient) -> None:
        """Test that TEXT messages are dispatched to _handle_message."""
        callback = MagicMock()
        ws_client.register_listener(callback)

        text_msg = MagicMock(type=aiohttp.WSMsgType.TEXT, data='{"type": "job_run_started", "job_id": 1}')
        close_msg = MagicMock(type=aiohttp.WSMsgType.CLOSE)

        async def fake_ws_messages() -> AsyncGenerator[MagicMock]:
            yield text_msg
            yield close_msg

        mock_ws = MagicMock()
        mock_ws.__aiter__ = lambda self: fake_ws_messages()
        mock_ws.exception = MagicMock(return_value=None)

        connect_count = 0

        async def ws_connect(*_args: object, **_kwargs: object) -> MagicMock:
            nonlocal connect_count
            connect_count += 1
            if connect_count > 1:
                ws_client._running = False  # noqa: SLF001
                raise aiohttp.ClientError("stop")
            return mock_ws

        ws_client._session.ws_connect = AsyncMock(side_effect=ws_connect)  # noqa: SLF001
        ws_client._running = True  # noqa: SLF001

        with patch("asyncio.sleep", new_callable=AsyncMock):
            task = asyncio.create_task(ws_client._listen_loop())  # noqa: SLF001
            await task

        callback.assert_called_once()
        event = callback.call_args[0][0]
        assert isinstance(event, WebSocketEvent)
        assert event.type == "job_run_started"

    async def test_error_message_breaks_loop(self, ws_client: VaultWebSocketClient) -> None:
        """Test that ERROR messages break the inner loop and trigger reconnect."""
        error_msg = MagicMock(type=aiohttp.WSMsgType.ERROR)

        async def fake_ws_messages() -> AsyncGenerator[MagicMock]:
            yield error_msg

        mock_ws = MagicMock()
        mock_ws.__aiter__ = lambda self: fake_ws_messages()
        mock_ws.exception = MagicMock(return_value=Exception("ws error"))

        connect_count = 0

        async def ws_connect(*_args: object, **_kwargs: object) -> MagicMock:
            nonlocal connect_count
            connect_count += 1
            if connect_count > 1:
                ws_client._running = False  # noqa: SLF001
                raise aiohttp.ClientError("stop")
            return mock_ws

        ws_client._session.ws_connect = AsyncMock(side_effect=ws_connect)  # noqa: SLF001
        ws_client._running = True  # noqa: SLF001

        with patch("asyncio.sleep", new_callable=AsyncMock):
            task = asyncio.create_task(ws_client._listen_loop())  # noqa: SLF001
            await task

        assert connect_count == 2  # First connect + reconnect attempt

    async def test_close_message_breaks_loop(self, ws_client: VaultWebSocketClient) -> None:
        """Test that CLOSE/CLOSING/CLOSED messages break the inner loop."""
        close_msg = MagicMock(type=aiohttp.WSMsgType.CLOSING)

        async def fake_ws_messages() -> AsyncGenerator[MagicMock]:
            yield close_msg

        mock_ws = MagicMock()
        mock_ws.__aiter__ = lambda self: fake_ws_messages()

        connect_count = 0

        async def ws_connect(*_args: object, **_kwargs: object) -> MagicMock:
            nonlocal connect_count
            connect_count += 1
            if connect_count > 1:
                ws_client._running = False  # noqa: SLF001
                raise aiohttp.ClientError("stop")
            return mock_ws

        ws_client._session.ws_connect = AsyncMock(side_effect=ws_connect)  # noqa: SLF001
        ws_client._running = True  # noqa: SLF001

        with patch("asyncio.sleep", new_callable=AsyncMock):
            task = asyncio.create_task(ws_client._listen_loop())  # noqa: SLF001
            await task

        assert connect_count == 2

    async def test_connection_error_reconnects(self, ws_client: VaultWebSocketClient) -> None:
        """Test that connection errors trigger reconnect with backoff."""
        connect_count = 0

        async def ws_connect(*_args: object, **_kwargs: object) -> None:
            nonlocal connect_count
            connect_count += 1
            if connect_count >= 3:
                ws_client._running = False  # noqa: SLF001
            raise aiohttp.ClientError("connection refused")

        ws_client._session.ws_connect = AsyncMock(side_effect=ws_connect)  # noqa: SLF001
        ws_client._running = True  # noqa: SLF001

        with patch("asyncio.sleep", new_callable=AsyncMock) as mock_sleep:
            task = asyncio.create_task(ws_client._listen_loop())  # noqa: SLF001
            await task

        # Should have attempted reconnect with increasing delays
        assert connect_count >= 3
        assert mock_sleep.await_count >= 2

    async def test_running_false_stops_message_loop(self, ws_client: VaultWebSocketClient) -> None:
        """Test that setting _running=False during message iteration stops the loop."""

        async def fake_ws_messages() -> AsyncGenerator[MagicMock]:
            ws_client._running = False  # noqa: SLF001
            yield MagicMock(type=aiohttp.WSMsgType.TEXT, data='{"type": "test"}')

        mock_ws = MagicMock()
        mock_ws.__aiter__ = lambda self: fake_ws_messages()

        ws_client._session.ws_connect = AsyncMock(return_value=mock_ws)  # noqa: SLF001
        ws_client._running = True  # noqa: SLF001

        task = asyncio.create_task(ws_client._listen_loop())  # noqa: SLF001
        await task

        # Should exit without reconnecting
