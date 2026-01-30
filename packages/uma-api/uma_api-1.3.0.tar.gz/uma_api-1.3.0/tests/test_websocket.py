"""Tests for the Uma API WebSocket client."""

import asyncio
import contextlib
import json
from unittest.mock import AsyncMock, MagicMock, patch

import pytest
import websockets.exceptions

from uma_api.websocket import UnraidWebSocketClient


class TestUnraidWebSocketClient:
    """Test the UnraidWebSocketClient class."""

    def test_client_initialization(self):
        """Test client initialization."""
        client = UnraidWebSocketClient(host="192.168.1.100", port=8043)

        assert client.host == "192.168.1.100"
        assert client.port == 8043
        assert client.ws_url == "ws://192.168.1.100:8043/api/v1/ws"
        assert client.on_message is None
        assert client.on_error is None
        assert client.on_close is None

    def test_client_initialization_with_reconnect_options(self):
        """Test client initialization with reconnection options."""
        client = UnraidWebSocketClient(
            host="192.168.1.100",
            auto_reconnect=True,
            reconnect_delays=[1, 2, 4],
            max_retries=5,
        )

        assert client.auto_reconnect is True
        assert client.reconnect_delays == [1, 2, 4]
        assert client.max_retries == 5

    def test_client_default_reconnect_values(self):
        """Test default reconnection values."""
        client = UnraidWebSocketClient(host="192.168.1.100")

        assert client.auto_reconnect is True
        assert client.reconnect_delays == [1, 2, 4, 8, 16, 32, 60]
        assert client.max_retries == 10

    def test_client_with_wss(self):
        """Test client initialization with WSS."""
        client = UnraidWebSocketClient(host="192.168.1.100", port=8043, use_wss=True)

        assert client.ws_url == "wss://192.168.1.100:8043/api/v1/ws"

    def test_client_with_custom_port(self):
        """Test client initialization with custom port."""
        client = UnraidWebSocketClient(host="192.168.1.100", port=9999)

        assert client.port == 9999
        assert client.ws_url == "ws://192.168.1.100:9999/api/v1/ws"

    def test_client_with_callbacks(self):
        """Test client initialization with callbacks."""

        def on_message(data):
            pass

        def on_error(error):
            pass

        def on_close():
            pass

        client = UnraidWebSocketClient(
            host="192.168.1.100",
            on_message=on_message,
            on_error=on_error,
            on_close=on_close,
        )

        assert client.on_message is on_message
        assert client.on_error is on_error
        assert client.on_close is on_close

    @pytest.mark.asyncio
    async def test_is_connected_property(self):
        """Test the is_connected property."""
        client = UnraidWebSocketClient(host="192.168.1.100")

        # Initially not connected
        assert client.is_connected is False

    @pytest.mark.asyncio
    async def test_is_connected_with_websocket(self):
        """Test is_connected when websocket exists."""
        client = UnraidWebSocketClient(host="192.168.1.100")

        # Mock websocket that is open
        mock_ws = MagicMock()
        mock_ws.closed = False
        client._websocket = mock_ws

        assert client.is_connected is True

        # Mock websocket that is closed
        mock_ws.closed = True
        assert client.is_connected is False

    @pytest.mark.asyncio
    async def test_disconnect(self):
        """Test disconnect method."""
        client = UnraidWebSocketClient(host="192.168.1.100")

        # Create a mock websocket
        mock_ws = AsyncMock()
        client._websocket = mock_ws

        await client.disconnect()

        mock_ws.close.assert_called_once()
        assert client._running is False

    @pytest.mark.asyncio
    async def test_disconnect_without_websocket(self):
        """Test disconnect when no websocket connected."""
        client = UnraidWebSocketClient(host="192.168.1.100")

        # Should not raise error
        await client.disconnect()
        assert client._running is False

    @pytest.mark.asyncio
    async def test_connect_with_sync_message_callback(self):
        """Test connect with synchronous message callback."""
        received_messages = []

        def on_message(data):
            received_messages.append(data)

        client = UnraidWebSocketClient(
            host="192.168.1.100",
            on_message=on_message,
        )

        # Create a mock websocket context manager
        mock_ws = AsyncMock()
        mock_ws.recv = AsyncMock(
            side_effect=[
                json.dumps({"type": "test", "value": 1}),
                websockets.exceptions.ConnectionClosed(None, None),
            ]
        )

        with patch("websockets.connect") as mock_connect:
            mock_connect.return_value.__aenter__.return_value = mock_ws
            mock_connect.return_value.__aexit__.return_value = None

            await client.connect()

        assert len(received_messages) == 1
        assert received_messages[0] == {"type": "test", "value": 1}

    @pytest.mark.asyncio
    async def test_connect_with_async_message_callback(self):
        """Test connect with asynchronous message callback."""
        received_messages = []

        async def on_message(data):
            received_messages.append(data)

        client = UnraidWebSocketClient(
            host="192.168.1.100",
            on_message=on_message,
        )

        # Create a mock websocket context manager
        mock_ws = AsyncMock()
        mock_ws.recv = AsyncMock(
            side_effect=[
                json.dumps({"type": "async_test", "value": 2}),
                websockets.exceptions.ConnectionClosed(None, None),
            ]
        )

        with patch("websockets.connect") as mock_connect:
            mock_connect.return_value.__aenter__.return_value = mock_ws
            mock_connect.return_value.__aexit__.return_value = None

            await client.connect()

        assert len(received_messages) == 1
        assert received_messages[0] == {"type": "async_test", "value": 2}

    @pytest.mark.asyncio
    async def test_connect_with_bytes_message(self):
        """Test connect handles bytes messages."""
        received_messages = []

        def on_message(data):
            received_messages.append(data)

        client = UnraidWebSocketClient(
            host="192.168.1.100",
            on_message=on_message,
        )

        mock_ws = AsyncMock()
        mock_ws.recv = AsyncMock(
            side_effect=[
                b'{"type": "bytes_test"}',
                websockets.exceptions.ConnectionClosed(None, None),
            ]
        )

        with patch("websockets.connect") as mock_connect:
            mock_connect.return_value.__aenter__.return_value = mock_ws
            mock_connect.return_value.__aexit__.return_value = None

            await client.connect()

        assert len(received_messages) == 1
        assert received_messages[0] == {"type": "bytes_test"}

    @pytest.mark.asyncio
    async def test_connect_with_json_decode_error(self):
        """Test connect handles JSON decode errors."""
        errors_received = []

        def on_error(error):
            errors_received.append(error)

        client = UnraidWebSocketClient(
            host="192.168.1.100",
            on_error=on_error,
        )

        mock_ws = AsyncMock()
        mock_ws.recv = AsyncMock(
            side_effect=[
                "not valid json {{{",
                websockets.exceptions.ConnectionClosed(None, None),
            ]
        )

        with patch("websockets.connect") as mock_connect:
            mock_connect.return_value.__aenter__.return_value = mock_ws
            mock_connect.return_value.__aexit__.return_value = None

            await client.connect()

        assert len(errors_received) == 1
        assert isinstance(errors_received[0], ValueError)

    @pytest.mark.asyncio
    async def test_connect_with_async_error_callback(self):
        """Test connect with async error callback."""
        errors_received = []

        async def on_error(error):
            errors_received.append(error)

        client = UnraidWebSocketClient(
            host="192.168.1.100",
            on_error=on_error,
        )

        mock_ws = AsyncMock()
        mock_ws.recv = AsyncMock(
            side_effect=[
                "invalid json",
                websockets.exceptions.ConnectionClosed(None, None),
            ]
        )

        with patch("websockets.connect") as mock_connect:
            mock_connect.return_value.__aenter__.return_value = mock_ws
            mock_connect.return_value.__aexit__.return_value = None

            await client.connect()

        assert len(errors_received) == 1

    @pytest.mark.asyncio
    async def test_connect_with_close_callback(self):
        """Test connect calls close callback on disconnect."""
        close_called = []

        def on_close():
            close_called.append(True)

        client = UnraidWebSocketClient(
            host="192.168.1.100",
            on_close=on_close,
        )

        mock_ws = AsyncMock()
        mock_ws.recv = AsyncMock(side_effect=[websockets.exceptions.ConnectionClosed(None, None)])

        with patch("websockets.connect") as mock_connect:
            mock_connect.return_value.__aenter__.return_value = mock_ws
            mock_connect.return_value.__aexit__.return_value = None

            await client.connect()

        assert len(close_called) == 1

    @pytest.mark.asyncio
    async def test_connect_with_async_close_callback(self):
        """Test connect with async close callback."""
        close_called = []

        async def on_close():
            close_called.append(True)

        client = UnraidWebSocketClient(
            host="192.168.1.100",
            on_close=on_close,
        )

        mock_ws = AsyncMock()
        mock_ws.recv = AsyncMock(side_effect=[websockets.exceptions.ConnectionClosed(None, None)])

        with patch("websockets.connect") as mock_connect:
            mock_connect.return_value.__aenter__.return_value = mock_ws
            mock_connect.return_value.__aexit__.return_value = None

            await client.connect()

        assert len(close_called) == 1

    @pytest.mark.asyncio
    async def test_connect_connection_error(self):
        """Test connect raises ConnectionError on failure."""
        errors_received = []

        def on_error(error):
            errors_received.append(error)

        client = UnraidWebSocketClient(
            host="192.168.1.100",
            on_error=on_error,
            auto_reconnect=False,  # Disable reconnect for this test
        )

        with patch("websockets.connect") as mock_connect:
            mock_connect.side_effect = Exception("Connection refused")

            with pytest.raises(ConnectionError) as exc_info:
                await client.connect()

            assert "Failed to connect to WebSocket" in str(exc_info.value)


class TestWebSocketReconnection:
    """Tests for WebSocket auto-reconnection functionality."""

    def test_lifecycle_callbacks_initialization(self):
        """Test lifecycle callbacks can be set."""
        on_connect_called = []
        on_disconnect_called = []
        on_reconnect_failed_called = []

        def on_connect():
            on_connect_called.append(True)

        def on_disconnect():
            on_disconnect_called.append(True)

        def on_reconnect_failed():
            on_reconnect_failed_called.append(True)

        client = UnraidWebSocketClient(
            host="192.168.1.100",
            on_connect=on_connect,
            on_disconnect=on_disconnect,
            on_reconnect_failed=on_reconnect_failed,
        )

        assert client.on_connect is on_connect
        assert client.on_disconnect is on_disconnect
        assert client.on_reconnect_failed is on_reconnect_failed

    @pytest.mark.asyncio
    async def test_on_connect_callback(self):
        """Test on_connect callback is called when connected."""
        connect_called = []

        def on_connect():
            connect_called.append(True)

        client = UnraidWebSocketClient(
            host="192.168.1.100",
            on_connect=on_connect,
            auto_reconnect=False,
        )

        mock_ws = AsyncMock()
        mock_ws.recv = AsyncMock(side_effect=[websockets.exceptions.ConnectionClosed(None, None)])

        with patch("websockets.connect") as mock_connect:
            mock_connect.return_value.__aenter__.return_value = mock_ws
            mock_connect.return_value.__aexit__.return_value = None

            await client.connect()

        assert len(connect_called) == 1

    @pytest.mark.asyncio
    async def test_on_connect_async_callback(self):
        """Test async on_connect callback."""
        connect_called = []

        async def on_connect():
            connect_called.append(True)

        client = UnraidWebSocketClient(
            host="192.168.1.100",
            on_connect=on_connect,
            auto_reconnect=False,
        )

        mock_ws = AsyncMock()
        mock_ws.recv = AsyncMock(side_effect=[websockets.exceptions.ConnectionClosed(None, None)])

        with patch("websockets.connect") as mock_connect:
            mock_connect.return_value.__aenter__.return_value = mock_ws
            mock_connect.return_value.__aexit__.return_value = None

            await client.connect()

        assert len(connect_called) == 1

    @pytest.mark.asyncio
    async def test_on_disconnect_callback(self):
        """Test on_disconnect callback is called when disconnected."""
        disconnect_called = []

        def on_disconnect():
            disconnect_called.append(True)

        client = UnraidWebSocketClient(
            host="192.168.1.100",
            on_disconnect=on_disconnect,
            auto_reconnect=False,
        )

        mock_ws = AsyncMock()
        mock_ws.recv = AsyncMock(side_effect=[websockets.exceptions.ConnectionClosed(None, None)])

        with patch("websockets.connect") as mock_connect:
            mock_connect.return_value.__aenter__.return_value = mock_ws
            mock_connect.return_value.__aexit__.return_value = None

            # Use start() instead of connect() for disconnect callback
            await client.start()

        assert len(disconnect_called) == 1

    @pytest.mark.asyncio
    async def test_start_and_stop(self):
        """Test start and stop methods."""
        client = UnraidWebSocketClient(
            host="192.168.1.100",
            auto_reconnect=False,
        )

        mock_ws = AsyncMock()
        mock_ws.recv = AsyncMock(side_effect=[websockets.exceptions.ConnectionClosed(None, None)])

        with patch("websockets.connect") as mock_connect:
            mock_connect.return_value.__aenter__.return_value = mock_ws
            mock_connect.return_value.__aexit__.return_value = None

            # Start should connect
            await client.start()

        # After connection closes, should not be connected
        assert client.is_connected is False

    @pytest.mark.asyncio
    async def test_stop_graceful_shutdown(self):
        """Test stop method for graceful shutdown."""
        client = UnraidWebSocketClient(host="192.168.1.100")

        mock_ws = AsyncMock()
        client._websocket = mock_ws

        await client.stop()

        mock_ws.close.assert_called_once()
        assert client._running is False

    @pytest.mark.asyncio
    async def test_reconnection_on_disconnect(self):
        """Test that reconnection is attempted on disconnect."""
        client = UnraidWebSocketClient(
            host="192.168.1.100",
            auto_reconnect=True,
            reconnect_delays=[0.01, 0.02],
            max_retries=2,
        )

        call_count = [0]

        def make_mock():
            """Create a new mock WebSocket for each connection attempt."""
            call_count[0] += 1
            mock_ws = AsyncMock()
            mock_ws.recv = AsyncMock(side_effect=websockets.exceptions.ConnectionClosed(None, None))
            return mock_ws

        with patch("websockets.connect") as mock_connect:
            # Each call to connect returns a new context manager with a fresh mock
            mock_connect.return_value.__aenter__.side_effect = make_mock
            mock_connect.return_value.__aexit__.return_value = None

            with patch("uma_api.websocket.asyncio.sleep", new_callable=AsyncMock):
                await client.start()

        # Should have tried to connect multiple times (initial + retries up to max_retries)
        # max_retries=2 means: initial + 2 retries = 3 total attempts
        assert call_count[0] == 3

    @pytest.mark.asyncio
    async def test_max_retries_exceeded(self):
        """Test on_reconnect_failed is called when max retries exceeded."""
        reconnect_failed_called = []

        def on_reconnect_failed():
            reconnect_failed_called.append(True)

        client = UnraidWebSocketClient(
            host="192.168.1.100",
            on_reconnect_failed=on_reconnect_failed,
            auto_reconnect=True,
            reconnect_delays=[0.01],
            max_retries=2,
        )

        with patch("websockets.connect") as mock_connect:
            mock_connect.side_effect = ConnectionRefusedError("Connection refused")

            with (
                patch("uma_api.websocket.asyncio.sleep", new_callable=AsyncMock),
                contextlib.suppress(TimeoutError, ConnectionError),
            ):
                await asyncio.wait_for(client.start(), timeout=1.0)

        # Should have called on_reconnect_failed
        assert len(reconnect_failed_called) >= 1

    @pytest.mark.asyncio
    async def test_retry_counter_resets_on_success(self):
        """Test that retry counter resets after successful connection."""
        client = UnraidWebSocketClient(
            host="192.168.1.100",
            auto_reconnect=True,
            reconnect_delays=[0.01],
            max_retries=3,
        )

        # Initially 0 retries
        assert client._retry_count == 0

        # Simulate successful connection
        client._reset_retry_count()
        assert client._retry_count == 0

    def test_get_reconnect_delay(self):
        """Test get_reconnect_delay returns correct delays."""
        client = UnraidWebSocketClient(
            host="192.168.1.100",
            reconnect_delays=[1, 2, 4, 8],
        )

        # First retry uses first delay
        client._retry_count = 0
        assert client._get_reconnect_delay() == 1

        # Second retry uses second delay
        client._retry_count = 1
        assert client._get_reconnect_delay() == 2

        # Beyond delays list uses last delay
        client._retry_count = 10
        assert client._get_reconnect_delay() == 8

    @pytest.mark.asyncio
    async def test_disable_auto_reconnect(self):
        """Test that auto_reconnect=False disables reconnection."""
        disconnect_called = []

        def on_disconnect():
            disconnect_called.append(True)

        client = UnraidWebSocketClient(
            host="192.168.1.100",
            on_disconnect=on_disconnect,
            auto_reconnect=False,
        )

        mock_ws = AsyncMock()
        mock_ws.recv = AsyncMock(side_effect=[websockets.exceptions.ConnectionClosed(None, None)])

        with patch("websockets.connect") as mock_connect:
            mock_connect.return_value.__aenter__.return_value = mock_ws
            mock_connect.return_value.__aexit__.return_value = None

            await client.start()

        # Should disconnect without attempting reconnect
        assert len(disconnect_called) == 1
        # connect should only be called once
        assert mock_connect.call_count == 1


class TestWebSocketBackgroundMode:
    """Test non-blocking WebSocket client modes."""

    @pytest.mark.asyncio
    async def test_start_background_returns_task(self):
        """Test that start_background returns an asyncio.Task."""
        client = UnraidWebSocketClient(host="192.168.1.100")

        mock_ws = AsyncMock()
        mock_ws.recv = AsyncMock(side_effect=[asyncio.CancelledError()])

        with patch("websockets.connect") as mock_connect:
            mock_connect.return_value.__aenter__.return_value = mock_ws
            mock_connect.return_value.__aexit__.return_value = None

            task = await client.start_background()

            # Task should be an asyncio.Task
            assert isinstance(task, asyncio.Task)
            assert client._background_task is task

            # Cancel and cleanup
            task.cancel()
            with contextlib.suppress(asyncio.CancelledError):
                await task

    @pytest.mark.asyncio
    async def test_start_background_runs_in_background(self):
        """Test that start_background doesn't block."""
        client = UnraidWebSocketClient(host="192.168.1.100")
        code_reached = []

        mock_ws = AsyncMock()
        # Use event to control the recv call
        recv_event = asyncio.Event()

        async def slow_recv():
            await recv_event.wait()
            raise asyncio.CancelledError()

        mock_ws.recv = slow_recv

        with patch("websockets.connect") as mock_connect:
            mock_connect.return_value.__aenter__.return_value = mock_ws
            mock_connect.return_value.__aexit__.return_value = None

            task = await client.start_background()
            code_reached.append("after_start")  # This should be reached immediately

            # Verify we got here without blocking
            assert "after_start" in code_reached

            # Cleanup
            recv_event.set()
            task.cancel()
            with contextlib.suppress(asyncio.CancelledError):
                await task

    @pytest.mark.asyncio
    async def test_context_manager_starts_and_stops(self):
        """Test async context manager starts and stops client."""
        connect_called = []

        client = UnraidWebSocketClient(
            host="192.168.1.100",
            on_connect=lambda: connect_called.append(True),
        )

        mock_ws = AsyncMock()
        mock_ws.closed = False  # Set the closed property for is_connected check
        recv_event = asyncio.Event()

        async def controlled_recv():
            await recv_event.wait()
            raise websockets.exceptions.ConnectionClosed(None, None)

        mock_ws.recv = controlled_recv
        mock_ws.close = AsyncMock()

        with patch("websockets.connect") as mock_connect:
            mock_connect.return_value.__aenter__.return_value = mock_ws
            mock_connect.return_value.__aexit__.return_value = None

            async with client:
                # Give time for on_connect to be called
                await asyncio.sleep(0.01)
                assert len(connect_called) == 1
                assert client.is_connected

                # Signal recv to complete
                recv_event.set()

            # After context, stop should have been called
            assert not client._running

    @pytest.mark.asyncio
    async def test_context_manager_returns_client(self):
        """Test that context manager returns the client instance."""
        client = UnraidWebSocketClient(host="192.168.1.100")

        mock_ws = AsyncMock()
        mock_ws.recv = AsyncMock(side_effect=[websockets.exceptions.ConnectionClosed(None, None)])

        with patch("websockets.connect") as mock_connect:
            mock_connect.return_value.__aenter__.return_value = mock_ws
            mock_connect.return_value.__aexit__.return_value = None

            async with client as ws:
                assert ws is client

    @pytest.mark.asyncio
    async def test_background_task_attribute_initialized(self):
        """Test that _background_task attribute is None initially."""
        client = UnraidWebSocketClient(host="192.168.1.100")
        assert client._background_task is None
