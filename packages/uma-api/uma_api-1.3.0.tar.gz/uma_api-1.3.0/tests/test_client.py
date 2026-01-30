"""Tests for the UnraidClient."""

from unittest.mock import AsyncMock, MagicMock, patch

import pytest

from uma_api.client import UnraidClient
from uma_api.exceptions import (
    UnraidAPIError,
    UnraidConflictError,
    UnraidConnectionError,
    UnraidNotFoundError,
    UnraidValidationError,
)
from uma_api.models import (
    CollectorStatus,
    DiskSettings,
    DockerSettings,
    HardwareFullInfo,
    LogContent,
    LogList,
    NetworkAccessUrls,
    NetworkConfig,
    NUTInfo,
    ParityHistory,
    RemoteSharesResponse,
    SystemSettings,
    UnassignedDevicesResponse,
    UnassignedInfo,
    VMSettings,
    ZFSArcStats,
)


class TestUnraidClientInit:
    """Test UnraidClient initialization."""

    def test_basic_initialization(self):
        """Test basic initialization."""
        client = UnraidClient(host="192.168.1.100")

        assert client.host == "192.168.1.100"
        assert client.port == 8043
        assert client.timeout == 10
        assert client.verify_ssl is True
        assert client.use_https is False
        assert client.base_url == "http://192.168.1.100:8043/api/v1"

    def test_custom_port(self):
        """Test custom port initialization."""
        client = UnraidClient(host="192.168.1.100", port=9000)

        assert client.port == 9000
        assert client.base_url == "http://192.168.1.100:9000/api/v1"

    def test_https_initialization(self):
        """Test HTTPS initialization."""
        client = UnraidClient(host="192.168.1.100", use_https=True)

        assert client.use_https is True
        assert client.base_url == "https://192.168.1.100:8043/api/v1"

    def test_custom_timeout(self):
        """Test custom timeout initialization."""
        client = UnraidClient(host="192.168.1.100", timeout=30)

        assert client.timeout == 30

    def test_verify_ssl_disabled(self):
        """Test verify_ssl disabled."""
        client = UnraidClient(host="192.168.1.100", verify_ssl=False)

        assert client.verify_ssl is False


class TestUnraidClientContextManager:
    """Test UnraidClient context manager."""

    @pytest.mark.asyncio
    async def test_context_manager(self):
        """Test async context manager."""
        async with UnraidClient(host="192.168.1.100") as client:
            assert client is not None

    @pytest.mark.asyncio
    async def test_context_manager_with_session(self):
        """Test context manager with existing session."""
        mock_session = AsyncMock()
        mock_session.closed = False

        # Session should not be closed since we provided it
        client = UnraidClient(host="192.168.1.100", session=mock_session)
        await client.close()

        mock_session.close.assert_not_called()


class TestUnraidClientRequest:
    """Test UnraidClient _request method."""

    @pytest.mark.asyncio
    async def test_successful_request(self):
        """Test successful request."""
        mock_response = MagicMock()
        mock_response.status = 200
        mock_response.json = AsyncMock(return_value={"key": "value"})

        mock_session = MagicMock()
        mock_session.closed = False  # Critical: prevent _ensure_session from creating real session
        mock_context = MagicMock()
        mock_context.__aenter__ = AsyncMock(return_value=mock_response)
        mock_context.__aexit__ = AsyncMock(return_value=None)
        mock_session.request.return_value = mock_context

        client = UnraidClient(host="192.168.1.100")
        client._session = mock_session
        client._owns_session = False

        result = await client._request("GET", "/test")

        assert result == {"key": "value"}

    @pytest.mark.asyncio
    async def test_404_error(self):
        """Test 404 error handling."""
        mock_response = MagicMock()
        mock_response.status = 404
        mock_response.json = AsyncMock(
            return_value={"message": "Not found", "error_code": "NOT_FOUND"}
        )

        mock_session = MagicMock()
        mock_session.closed = False  # Critical: prevent _ensure_session from creating real session
        mock_context = MagicMock()
        mock_context.__aenter__ = AsyncMock(return_value=mock_response)
        mock_context.__aexit__ = AsyncMock(return_value=None)
        mock_session.request.return_value = mock_context

        client = UnraidClient(host="192.168.1.100")
        client._session = mock_session
        client._owns_session = False

        with pytest.raises(UnraidNotFoundError) as exc:
            await client._request("GET", "/test")

        assert exc.value.status_code == 404
        assert exc.value.error_code == "NOT_FOUND"

    @pytest.mark.asyncio
    async def test_409_error(self):
        """Test 409 conflict error handling."""
        mock_response = MagicMock()
        mock_response.status = 409
        mock_response.json = AsyncMock(
            return_value={"message": "Conflict", "error_code": "CONFLICT"}
        )

        mock_session = MagicMock()
        mock_session.closed = False  # Critical: prevent _ensure_session from creating real session
        mock_context = MagicMock()
        mock_context.__aenter__ = AsyncMock(return_value=mock_response)
        mock_context.__aexit__ = AsyncMock(return_value=None)
        mock_session.request.return_value = mock_context

        client = UnraidClient(host="192.168.1.100")
        client._session = mock_session
        client._owns_session = False

        with pytest.raises(UnraidConflictError) as exc:
            await client._request("GET", "/test")

        assert exc.value.status_code == 409

    @pytest.mark.asyncio
    async def test_400_error(self):
        """Test 400 validation error handling."""
        mock_response = MagicMock()
        mock_response.status = 400
        mock_response.json = AsyncMock(
            return_value={"message": "Bad request", "error_code": "VALIDATION_ERROR"}
        )

        mock_session = MagicMock()
        mock_session.closed = False  # Critical: prevent _ensure_session from creating real session
        mock_context = MagicMock()
        mock_context.__aenter__ = AsyncMock(return_value=mock_response)
        mock_context.__aexit__ = AsyncMock(return_value=None)
        mock_session.request.return_value = mock_context

        client = UnraidClient(host="192.168.1.100")
        client._session = mock_session
        client._owns_session = False

        with pytest.raises(UnraidValidationError) as exc:
            await client._request("GET", "/test")

        assert exc.value.status_code == 400

    @pytest.mark.asyncio
    async def test_500_error(self):
        """Test 500 error handling."""
        mock_response = MagicMock()
        mock_response.status = 500
        mock_response.json = AsyncMock(
            return_value={"message": "Server error", "error_code": "SERVER_ERROR"}
        )

        mock_session = MagicMock()
        mock_session.closed = False  # Critical: prevent _ensure_session from creating real session
        mock_context = MagicMock()
        mock_context.__aenter__ = AsyncMock(return_value=mock_response)
        mock_context.__aexit__ = AsyncMock(return_value=None)
        mock_session.request.return_value = mock_context

        client = UnraidClient(host="192.168.1.100")
        client._session = mock_session
        client._owns_session = False

        with pytest.raises(UnraidAPIError) as exc:
            await client._request("GET", "/test")

        assert exc.value.status_code == 500


class TestUnraidClientEndpoints:
    """Test UnraidClient endpoint methods."""

    @pytest.fixture
    def client(self):
        """Create a client for testing."""
        return UnraidClient(host="192.168.1.100")

    @pytest.mark.asyncio
    async def test_health_check(self, client):
        """Test health_check method."""
        with patch.object(client, "_request", new_callable=AsyncMock) as mock_request:
            mock_request.return_value = {"status": "ok", "version": "1.0.0"}

            result = await client.health_check()

            assert result.status == "ok"
            mock_request.assert_called_once_with("GET", "/health")

    @pytest.mark.asyncio
    async def test_get_system_info(self, client):
        """Test get_system_info method."""
        with patch.object(client, "_request", new_callable=AsyncMock) as mock_request:
            mock_request.return_value = {
                "hostname": "tower",
                "version": "6.12.0",
                "uptime": "10 days",
                "cpu_model": "Intel",
                "cpu_usage_percent": 25.5,
                "memory_total_bytes": 16000000000,
                "memory_used_bytes": 8000000000,
                "memory_usage_percent": 50.0,
            }

            result = await client.get_system_info()

            assert result.hostname == "tower"
            mock_request.assert_called_once_with("GET", "/system")

    @pytest.mark.asyncio
    async def test_get_array_status(self, client):
        """Test get_array_status method."""
        with patch.object(client, "_request", new_callable=AsyncMock) as mock_request:
            mock_request.return_value = {
                "state": "STARTED",
                "capacity_bytes": 10000000000000,
                "used_bytes": 5000000000000,
                "free_bytes": 5000000000000,
            }

            result = await client.get_array_status()

            assert result.state == "STARTED"
            mock_request.assert_called_once_with("GET", "/array")

    @pytest.mark.asyncio
    async def test_start_array(self, client):
        """Test start_array method."""
        with patch.object(client, "_request", new_callable=AsyncMock) as mock_request:
            mock_request.return_value = {"success": True, "message": "Array started"}

            result = await client.start_array()

            assert result.success is True
            mock_request.assert_called_once_with("POST", "/array/start")

    @pytest.mark.asyncio
    async def test_stop_array(self, client):
        """Test stop_array method."""
        with patch.object(client, "_request", new_callable=AsyncMock) as mock_request:
            mock_request.return_value = {"success": True, "message": "Array stopped"}

            result = await client.stop_array()

            assert result.success is True
            mock_request.assert_called_once_with("POST", "/array/stop")

    @pytest.mark.asyncio
    async def test_list_disks(self, client):
        """Test list_disks method."""
        with patch.object(client, "_request", new_callable=AsyncMock) as mock_request:
            mock_request.return_value = [
                {
                    "id": "disk1",
                    "name": "Disk 1",
                    "device": "/dev/sda",
                    "size_bytes": 1000000000000,
                    "status": "DISK_OK",
                }
            ]

            result = await client.list_disks()

            assert len(result) == 1
            assert result[0].id == "disk1"
            mock_request.assert_called_once_with("GET", "/disks")

    @pytest.mark.asyncio
    async def test_get_disk(self, client):
        """Test get_disk method."""
        with patch.object(client, "_request", new_callable=AsyncMock) as mock_request:
            mock_request.return_value = {
                "id": "disk1",
                "name": "Disk 1",
                "device": "/dev/sda",
                "size_bytes": 1000000000000,
                "status": "DISK_OK",
            }

            result = await client.get_disk("disk1")

            assert result.id == "disk1"
            mock_request.assert_called_once_with("GET", "/disks/disk1")

    @pytest.mark.asyncio
    async def test_list_containers(self, client):
        """Test list_containers method."""
        with patch.object(client, "_request", new_callable=AsyncMock) as mock_request:
            mock_request.return_value = [
                {
                    "id": "abc123",
                    "name": "plex",
                    "state": "running",
                    "image": "plexinc/pms-docker",
                }
            ]

            result = await client.list_containers()

            assert len(result) == 1
            assert result[0].name == "plex"
            mock_request.assert_called_once_with("GET", "/docker")

    @pytest.mark.asyncio
    async def test_get_container(self, client):
        """Test get_container method."""
        with patch.object(client, "_request", new_callable=AsyncMock) as mock_request:
            mock_request.return_value = {
                "id": "abc123",
                "name": "plex",
                "state": "running",
                "image": "plexinc/pms-docker",
            }

            result = await client.get_container("abc123")

            assert result.id == "abc123"
            mock_request.assert_called_once_with("GET", "/docker/abc123")

    @pytest.mark.asyncio
    async def test_start_container(self, client):
        """Test start_container method."""
        with patch.object(client, "_request", new_callable=AsyncMock) as mock_request:
            mock_request.return_value = {"success": True, "message": "Started"}

            result = await client.start_container("abc123")

            assert result.success is True
            mock_request.assert_called_once_with("POST", "/docker/abc123/start")

    @pytest.mark.asyncio
    async def test_stop_container(self, client):
        """Test stop_container method."""
        with patch.object(client, "_request", new_callable=AsyncMock) as mock_request:
            mock_request.return_value = {"success": True, "message": "Stopped"}

            result = await client.stop_container("abc123")

            assert result.success is True
            mock_request.assert_called_once_with("POST", "/docker/abc123/stop")

    @pytest.mark.asyncio
    async def test_list_vms(self, client):
        """Test list_vms method."""
        with patch.object(client, "_request", new_callable=AsyncMock) as mock_request:
            mock_request.return_value = [
                {
                    "id": "vm1",
                    "name": "Windows 10",
                    "state": "running",
                }
            ]

            result = await client.list_vms()

            assert len(result) == 1
            assert result[0].name == "Windows 10"
            mock_request.assert_called_once_with("GET", "/vm")

    @pytest.mark.asyncio
    async def test_get_vm(self, client):
        """Test get_vm method."""
        with patch.object(client, "_request", new_callable=AsyncMock) as mock_request:
            mock_request.return_value = {
                "id": "vm1",
                "name": "Windows 10",
                "state": "running",
            }

            result = await client.get_vm("vm1")

            assert result.id == "vm1"
            mock_request.assert_called_once_with("GET", "/vm/vm1")

    @pytest.mark.asyncio
    async def test_list_shares(self, client):
        """Test list_shares method."""
        with patch.object(client, "_request", new_callable=AsyncMock) as mock_request:
            mock_request.return_value = [
                {
                    "name": "media",
                    "path": "/mnt/user/media",
                    "size_bytes": 5000000000000,
                }
            ]

            result = await client.list_shares()

            assert len(result) == 1
            assert result[0].name == "media"
            mock_request.assert_called_once_with("GET", "/shares")

    @pytest.mark.asyncio
    async def test_get_share(self, client):
        """Test get_share method - filters from list_shares."""
        with patch.object(client, "_request", new_callable=AsyncMock) as mock_request:
            mock_request.return_value = [
                {
                    "name": "media",
                    "path": "/mnt/user/media",
                    "size_bytes": 5000000000000,
                },
                {
                    "name": "appdata",
                    "path": "/mnt/user/appdata",
                    "size_bytes": 1000000000000,
                },
            ]

            result = await client.get_share("media")

            assert result.name == "media"
            # Now calls list_shares internally
            mock_request.assert_called_once_with("GET", "/shares")

    @pytest.mark.asyncio
    async def test_get_share_not_found(self, client):
        """Test get_share raises UnraidNotFoundError when share doesn't exist."""
        from uma_api.exceptions import UnraidNotFoundError

        with patch.object(client, "_request", new_callable=AsyncMock) as mock_request:
            mock_request.return_value = [
                {"name": "other", "path": "/mnt/user/other", "size_bytes": 1000},
            ]

            with pytest.raises(UnraidNotFoundError) as exc:
                await client.get_share("nonexistent")

            assert exc.value.status_code == 404
            assert "nonexistent" in exc.value.message

    @pytest.mark.asyncio
    async def test_list_network_interfaces(self, client):
        """Test list_network_interfaces method."""
        with patch.object(client, "_request", new_callable=AsyncMock) as mock_request:
            mock_request.return_value = [
                {
                    "name": "eth0",
                    "mac_address": "00:11:22:33:44:55",
                    "ip_address": "192.168.1.100",
                }
            ]

            result = await client.list_network_interfaces()

            assert len(result) == 1
            assert result[0].name == "eth0"
            mock_request.assert_called_once_with("GET", "/network")

    @pytest.mark.asyncio
    async def test_get_hardware_info(self, client):
        """Test get_hardware_info method - alias for get_hardware_full_info."""
        with patch.object(client, "_request", new_callable=AsyncMock) as mock_request:
            mock_request.return_value = {
                "bios": {"vendor": "AMI"},
                "system": {"manufacturer": "Dell"},
                "baseboard": {"manufacturer": "Dell"},
            }

            result = await client.get_hardware_info()

            # Now an alias for get_hardware_full_info
            assert result.bios is not None
            mock_request.assert_called_once_with("GET", "/hardware/full")

    @pytest.mark.asyncio
    async def test_list_gpus(self, client):
        """Test list_gpus method."""
        with patch.object(client, "_request", new_callable=AsyncMock) as mock_request:
            mock_request.return_value = [
                {
                    "id": "gpu0",
                    "name": "NVIDIA GeForce RTX 3080",
                    "vendor": "NVIDIA",
                }
            ]

            result = await client.list_gpus()

            assert len(result) == 1
            assert result[0].name == "NVIDIA GeForce RTX 3080"
            mock_request.assert_called_once_with("GET", "/gpu")

    @pytest.mark.asyncio
    async def test_get_ups_info(self, client):
        """Test get_ups_info method."""
        with patch.object(client, "_request", new_callable=AsyncMock) as mock_request:
            mock_request.return_value = {
                "status": "online",
                "battery_charge": 100,
                "battery_runtime": 3600,
            }

            result = await client.get_ups_info()

            assert result.status == "online"
            mock_request.assert_called_once_with("GET", "/ups")

    @pytest.mark.asyncio
    async def test_list_notifications(self, client):
        """Test list_notifications method."""
        with patch.object(client, "_request", new_callable=AsyncMock) as mock_request:
            mock_request.return_value = {
                "notifications": [],
                "unread_count": 0,
            }

            result = await client.list_notifications()

            assert result.unread_count == 0
            mock_request.assert_called_once_with("GET", "/notifications")

    @pytest.mark.asyncio
    async def test_create_notification(self, client):
        """Test create_notification method."""
        with patch.object(client, "_request", new_callable=AsyncMock) as mock_request:
            mock_request.return_value = {
                "id": "notif1",
                "subject": "Test",
                "message": "Test message",
                "importance": "normal",
                "timestamp": "2026-01-12T00:00:00Z",
            }

            result = await client.create_notification(
                subject="Test",
                message="Test message",
                importance="normal",
            )

            assert result.subject == "Test"
            mock_request.assert_called_once_with(
                "POST",
                "/notifications",
                data={
                    "subject": "Test",
                    "message": "Test message",
                    "importance": "normal",
                },
            )

    @pytest.mark.asyncio
    async def test_reboot_system(self, client):
        """Test reboot_system method."""
        with patch.object(client, "_request", new_callable=AsyncMock) as mock_request:
            mock_request.return_value = {"success": True, "message": "Rebooting"}

            result = await client.reboot_system()

            assert result.success is True
            mock_request.assert_called_once_with("POST", "/system/reboot")

    @pytest.mark.asyncio
    async def test_shutdown_system(self, client):
        """Test shutdown_system method."""
        with patch.object(client, "_request", new_callable=AsyncMock) as mock_request:
            mock_request.return_value = {"success": True, "message": "Shutting down"}

            result = await client.shutdown_system()

            assert result.success is True
            mock_request.assert_called_once_with("POST", "/system/shutdown")

    @pytest.mark.asyncio
    async def test_execute_user_script(self, client):
        """Test execute_user_script method."""
        with patch.object(client, "_request", new_callable=AsyncMock) as mock_request:
            mock_request.return_value = {
                "success": True,
                "output": "Script executed",
            }

            result = await client.execute_user_script("test_script")

            assert result.success is True
            mock_request.assert_called_once_with(
                "POST",
                "/user-scripts/test_script/execute",
                data={"background": False, "wait": True},
            )

    @pytest.mark.asyncio
    async def test_execute_user_script_with_options(self, client):
        """Test execute_user_script with background option."""
        with patch.object(client, "_request", new_callable=AsyncMock) as mock_request:
            mock_request.return_value = {
                "success": True,
                "output": "Script started",
            }

            result = await client.execute_user_script("test_script", background=True, wait=False)

            assert result.success is True
            mock_request.assert_called_once_with(
                "POST",
                "/user-scripts/test_script/execute",
                data={"background": True, "wait": False},
            )


class TestUnraidClientConnectionError:
    """Test connection error handling."""

    @pytest.mark.asyncio
    async def test_connection_error(self):
        """Test connection error is raised properly."""
        import aiohttp

        mock_session = MagicMock()
        mock_session.closed = False  # Critical: prevent _ensure_session from creating real session
        mock_session.request.side_effect = aiohttp.ClientError("Connection failed")

        client = UnraidClient(host="192.168.1.100")
        client._session = mock_session
        client._owns_session = False

        with pytest.raises(UnraidConnectionError):
            await client._request("GET", "/test")

    @pytest.mark.asyncio
    async def test_timeout_error(self):
        """Test timeout error is raised properly."""

        mock_session = MagicMock()
        mock_session.closed = False  # Critical: prevent _ensure_session from creating real session
        mock_session.request.side_effect = TimeoutError()

        client = UnraidClient(host="192.168.1.100")
        client._session = mock_session
        client._owns_session = False

        with pytest.raises(UnraidConnectionError):
            await client._request("GET", "/test")


class TestUnraidClientSessionManagement:
    """Test session management."""

    @pytest.mark.asyncio
    async def test_own_session_created(self):
        """Test that a session is created if not provided."""
        client = UnraidClient(host="192.168.1.100")

        assert client._session is None
        assert client._owns_session is True

    @pytest.mark.asyncio
    async def test_provided_session_used(self):
        """Test that provided session is used."""
        mock_session = AsyncMock()

        client = UnraidClient(host="192.168.1.100", session=mock_session)

        assert client._session is mock_session
        assert client._owns_session is False

    @pytest.mark.asyncio
    async def test_close_own_session(self):
        """Test that own session is closed."""
        client = UnraidClient(host="192.168.1.100")
        mock_session = AsyncMock()
        client._session = mock_session
        client._owns_session = True

        await client.close()

        mock_session.close.assert_called_once()

    @pytest.mark.asyncio
    async def test_close_provided_session_not_closed(self):
        """Test that provided session is not closed."""
        mock_session = AsyncMock()
        mock_session.closed = False

        client = UnraidClient(host="192.168.1.100", session=mock_session)

        await client.close()

        mock_session.close.assert_not_called()


class TestUnraidClientAdditionalEndpoints:
    """Test additional UnraidClient endpoint methods for coverage."""

    @pytest.fixture
    def client(self):
        """Create a client for testing."""
        return UnraidClient(host="192.168.1.100")

    @pytest.mark.asyncio
    async def test_restart_container(self, client):
        """Test restart_container method."""
        with patch.object(client, "_request", new_callable=AsyncMock) as mock_request:
            mock_request.return_value = {"success": True, "message": "Restarted"}

            result = await client.restart_container("plex")

            assert result.success is True
            mock_request.assert_called_once_with("POST", "/docker/plex/restart")

    @pytest.mark.asyncio
    async def test_pause_container(self, client):
        """Test pause_container method."""
        with patch.object(client, "_request", new_callable=AsyncMock) as mock_request:
            mock_request.return_value = {"success": True, "message": "Paused"}

            result = await client.pause_container("plex")

            assert result.success is True
            mock_request.assert_called_once_with("POST", "/docker/plex/pause")

    @pytest.mark.asyncio
    async def test_unpause_container(self, client):
        """Test unpause_container method."""
        with patch.object(client, "_request", new_callable=AsyncMock) as mock_request:
            mock_request.return_value = {"success": True, "message": "Unpaused"}

            result = await client.unpause_container("plex")

            assert result.success is True
            mock_request.assert_called_once_with("POST", "/docker/plex/unpause")

    @pytest.mark.asyncio
    async def test_start_vm(self, client):
        """Test start_vm method."""
        with patch.object(client, "_request", new_callable=AsyncMock) as mock_request:
            mock_request.return_value = {"success": True, "message": "Started"}

            result = await client.start_vm("windows")

            assert result.success is True
            mock_request.assert_called_once_with("POST", "/vm/windows/start")

    @pytest.mark.asyncio
    async def test_stop_vm(self, client):
        """Test stop_vm method."""
        with patch.object(client, "_request", new_callable=AsyncMock) as mock_request:
            mock_request.return_value = {"success": True, "message": "Stopped"}

            result = await client.stop_vm("windows")

            assert result.success is True
            mock_request.assert_called_once_with("POST", "/vm/windows/stop")

    @pytest.mark.asyncio
    async def test_restart_vm(self, client):
        """Test restart_vm method."""
        with patch.object(client, "_request", new_callable=AsyncMock) as mock_request:
            mock_request.return_value = {"success": True, "message": "Restarted"}

            result = await client.restart_vm("windows")

            assert result.success is True
            mock_request.assert_called_once_with("POST", "/vm/windows/restart")

    @pytest.mark.asyncio
    async def test_pause_vm(self, client):
        """Test pause_vm method."""
        with patch.object(client, "_request", new_callable=AsyncMock) as mock_request:
            mock_request.return_value = {"success": True, "message": "Paused"}

            result = await client.pause_vm("windows")

            assert result.success is True
            mock_request.assert_called_once_with("POST", "/vm/windows/pause")

    @pytest.mark.asyncio
    async def test_resume_vm(self, client):
        """Test resume_vm method."""
        with patch.object(client, "_request", new_callable=AsyncMock) as mock_request:
            mock_request.return_value = {"success": True, "message": "Resumed"}

            result = await client.resume_vm("windows")

            assert result.success is True
            mock_request.assert_called_once_with("POST", "/vm/windows/resume")

    @pytest.mark.asyncio
    async def test_spin_up_disk(self, client):
        """Test spin_up_disk method."""
        with patch.object(client, "_request", new_callable=AsyncMock) as mock_request:
            mock_request.return_value = {"success": True, "message": "Disk spinning up"}

            result = await client.spin_up_disk("disk1")

            assert result.success is True
            mock_request.assert_called_once_with("POST", "/disks/disk1/spinup")

    @pytest.mark.asyncio
    async def test_spin_down_disk(self, client):
        """Test spin_down_disk method."""
        with patch.object(client, "_request", new_callable=AsyncMock) as mock_request:
            mock_request.return_value = {"success": True, "message": "Disk spinning down"}

            result = await client.spin_down_disk("disk1")

            assert result.success is True
            mock_request.assert_called_once_with("POST", "/disks/disk1/spindown")

    # Note: get_parity_status() was removed - parity status is included in ArrayStatus

    @pytest.mark.asyncio
    async def test_get_parity_history(self, client):
        """Test get_parity_history method."""
        with patch.object(client, "_request", new_callable=AsyncMock) as mock_request:
            mock_request.return_value = {"history": []}

            result = await client.get_parity_history()

            assert isinstance(result, ParityHistory)
            mock_request.assert_called_once_with("GET", "/array/parity-check/history")

    @pytest.mark.asyncio
    async def test_get_network_interface(self, client):
        """Test get_network_interface method - filters from list_network_interfaces."""
        with patch.object(client, "_request", new_callable=AsyncMock) as mock_request:
            mock_request.return_value = [
                {
                    "name": "eth0",
                    "ip_address": "192.168.1.100",
                    "mac_address": "00:11:22:33:44:55",
                    "state": "up",
                },
                {
                    "name": "eth1",
                    "ip_address": "192.168.1.101",
                    "mac_address": "00:11:22:33:44:66",
                    "state": "down",
                },
            ]

            result = await client.get_network_interface("eth0")

            assert result.name == "eth0"
            # Now calls list_network_interfaces internally
            mock_request.assert_called_once_with("GET", "/network")

    @pytest.mark.asyncio
    async def test_get_network_interface_not_found(self, client):
        """Test get_network_interface raises UnraidNotFoundError when interface doesn't exist."""
        from uma_api.exceptions import UnraidNotFoundError

        with patch.object(client, "_request", new_callable=AsyncMock) as mock_request:
            mock_request.return_value = [
                {"name": "eth0", "ip_address": "192.168.1.100", "mac_address": "00:00:00"},
            ]

            with pytest.raises(UnraidNotFoundError) as exc:
                await client.get_network_interface("nonexistent")

            assert exc.value.status_code == 404
            assert "nonexistent" in exc.value.message

    @pytest.mark.asyncio
    async def test_get_network_access_urls(self, client):
        """Test get_network_access_urls method."""
        with patch.object(client, "_request", new_callable=AsyncMock) as mock_request:
            mock_request.return_value = {
                "local_url": "http://192.168.1.100",
                "remote_url": None,
            }

            result = await client.get_network_access_urls()

            assert isinstance(result, NetworkAccessUrls)
            mock_request.assert_called_once_with("GET", "/network/access-urls")

    @pytest.mark.asyncio
    async def test_get_hardware_full_info(self, client):
        """Test get_hardware_full_info method."""
        with patch.object(client, "_request", new_callable=AsyncMock) as mock_request:
            mock_request.return_value = {
                "bios": {"vendor": "AMI"},
                "system": {"manufacturer": "Dell"},
                "baseboard": {"manufacturer": "ASUS"},
                "processor": {"name": "Intel"},
                "memory": {"total_bytes": 16000000000},
            }

            result = await client.get_hardware_full_info()

            assert isinstance(result, HardwareFullInfo)
            mock_request.assert_called_once_with("GET", "/hardware/full")

    @pytest.mark.asyncio
    async def test_get_registration_info(self, client):
        """Test get_registration_info method."""
        with patch.object(client, "_request", new_callable=AsyncMock) as mock_request:
            mock_request.return_value = {
                "registered": True,
                "guid": "abc123",
                "type": "Pro",
            }

            result = await client.get_registration_info()

            assert result.registered is True
            mock_request.assert_called_once_with("GET", "/registration")

    @pytest.mark.asyncio
    async def test_list_logs(self, client):
        """Test list_logs method."""
        with patch.object(client, "_request", new_callable=AsyncMock) as mock_request:
            mock_request.return_value = {
                "logs": [
                    {"name": "syslog", "path": "/var/log/syslog"},
                    {"name": "docker.log", "path": "/var/log/docker.log"},
                ]
            }

            result = await client.list_logs()

            assert isinstance(result, LogList)
            mock_request.assert_called_once_with("GET", "/logs")

    @pytest.mark.asyncio
    async def test_get_log(self, client):
        """Test get_log method."""
        with patch.object(client, "_request", new_callable=AsyncMock) as mock_request:
            mock_request.return_value = {"path": "/var/log/syslog", "content": "log content"}

            result = await client.get_log("syslog")

            assert isinstance(result, LogContent)
            mock_request.assert_called_once_with("GET", "/logs/syslog", params={"lines": 100})

    @pytest.mark.asyncio
    async def test_get_notification_overview(self, client):
        """Test get_notification_overview method."""
        with patch.object(client, "_request", new_callable=AsyncMock) as mock_request:
            mock_request.return_value = {
                "unread_count": 5,
                "total_count": 10,
            }

            result = await client.get_notification_overview()

            assert result.unread_count == 5
            mock_request.assert_called_once_with("GET", "/notifications/overview")

    @pytest.mark.asyncio
    async def test_list_unread_notifications(self, client):
        """Test list_unread_notifications method."""
        with patch.object(client, "_request", new_callable=AsyncMock) as mock_request:
            mock_request.return_value = {
                "notifications": [],
                "unread_count": 0,
            }

            result = await client.list_unread_notifications()

            assert result.unread_count == 0
            mock_request.assert_called_once_with("GET", "/notifications/unread")

    @pytest.mark.asyncio
    async def test_list_archived_notifications(self, client):
        """Test list_archived_notifications method."""
        with patch.object(client, "_request", new_callable=AsyncMock) as mock_request:
            mock_request.return_value = {
                "notifications": [],
                "unread_count": 0,
            }

            result = await client.list_archived_notifications()

            assert result.unread_count == 0
            mock_request.assert_called_once_with("GET", "/notifications/archive")

    @pytest.mark.asyncio
    async def test_get_unassigned_info(self, client):
        """Test get_unassigned_info method."""
        with patch.object(client, "_request", new_callable=AsyncMock) as mock_request:
            mock_request.return_value = {"devices": [], "remote_shares": []}

            result = await client.get_unassigned_info()

            assert isinstance(result, UnassignedInfo)
            mock_request.assert_called_once_with("GET", "/unassigned")

    @pytest.mark.asyncio
    async def test_list_unassigned_devices(self, client):
        """Test list_unassigned_devices method."""
        with patch.object(client, "_request", new_callable=AsyncMock) as mock_request:
            mock_request.return_value = {"devices": []}

            result = await client.list_unassigned_devices()

            assert isinstance(result, UnassignedDevicesResponse)
            mock_request.assert_called_once_with("GET", "/unassigned/devices")

    @pytest.mark.asyncio
    async def test_list_remote_shares(self, client):
        """Test list_remote_shares method."""
        with patch.object(client, "_request", new_callable=AsyncMock) as mock_request:
            mock_request.return_value = {"remote_shares": []}

            result = await client.list_remote_shares()

            assert isinstance(result, RemoteSharesResponse)
            mock_request.assert_called_once_with("GET", "/unassigned/remote-shares")

    @pytest.mark.asyncio
    async def test_get_system_settings(self, client):
        """Test get_system_settings method."""
        with patch.object(client, "_request", new_callable=AsyncMock) as mock_request:
            mock_request.return_value = {"timezone": "UTC", "language": "en"}

            result = await client.get_system_settings()

            assert isinstance(result, SystemSettings)
            mock_request.assert_called_once_with("GET", "/settings/system")

    @pytest.mark.asyncio
    async def test_get_docker_settings(self, client):
        """Test get_docker_settings method."""
        with patch.object(client, "_request", new_callable=AsyncMock) as mock_request:
            mock_request.return_value = {"enabled": True, "image_path": "/mnt/user/docker"}

            result = await client.get_docker_settings()

            assert isinstance(result, DockerSettings)
            mock_request.assert_called_once_with("GET", "/settings/docker")

    @pytest.mark.asyncio
    async def test_get_vm_settings(self, client):
        """Test get_vm_settings method."""
        with patch.object(client, "_request", new_callable=AsyncMock) as mock_request:
            mock_request.return_value = {"enabled": True, "default_domain": "/mnt/user/domains"}

            result = await client.get_vm_settings()

            assert isinstance(result, VMSettings)
            mock_request.assert_called_once_with("GET", "/settings/vm")

    @pytest.mark.asyncio
    async def test_get_disk_settings(self, client):
        """Test get_disk_settings method."""
        with patch.object(client, "_request", new_callable=AsyncMock) as mock_request:
            mock_request.return_value = {"spindown_delay": 30}

            result = await client.get_disk_settings()

            assert isinstance(result, DiskSettings)
            mock_request.assert_called_once_with("GET", "/settings/disk-thresholds")

    @pytest.mark.asyncio
    async def test_list_user_scripts(self, client):
        """Test list_user_scripts method."""
        with patch.object(client, "_request", new_callable=AsyncMock) as mock_request:
            mock_request.return_value = []

            result = await client.list_user_scripts()

            assert result == []
            mock_request.assert_called_once_with("GET", "/user-scripts")

    @pytest.mark.asyncio
    async def test_list_zfs_pools(self, client):
        """Test list_zfs_pools method."""
        with patch.object(client, "_request", new_callable=AsyncMock) as mock_request:
            mock_request.return_value = []

            result = await client.list_zfs_pools()

            assert result == []
            mock_request.assert_called_once_with("GET", "/zfs/pools")

    @pytest.mark.asyncio
    async def test_list_zfs_datasets(self, client):
        """Test list_zfs_datasets method."""
        with patch.object(client, "_request", new_callable=AsyncMock) as mock_request:
            mock_request.return_value = []

            result = await client.list_zfs_datasets()

            assert result == []
            mock_request.assert_called_once_with("GET", "/zfs/datasets")

    @pytest.mark.asyncio
    async def test_list_zfs_snapshots(self, client):
        """Test list_zfs_snapshots method."""
        with patch.object(client, "_request", new_callable=AsyncMock) as mock_request:
            mock_request.return_value = []

            result = await client.list_zfs_snapshots()

            assert result == []
            mock_request.assert_called_once_with("GET", "/zfs/snapshots")

    @pytest.mark.asyncio
    async def test_get_zfs_arc_stats(self, client):
        """Test get_zfs_arc_stats method."""
        with patch.object(client, "_request", new_callable=AsyncMock) as mock_request:
            mock_request.return_value = {"size_bytes": 1000000, "hit_ratio_percent": 95.0}

            result = await client.get_zfs_arc_stats()

            assert isinstance(result, ZFSArcStats)
            # Endpoint is /zfs/arc not /zfs/arc-stats
            mock_request.assert_called_once_with("GET", "/zfs/arc")

    @pytest.mark.asyncio
    async def test_get_zfs_pool(self, client):
        """Test get_zfs_pool method."""
        with patch.object(client, "_request", new_callable=AsyncMock) as mock_request:
            mock_request.return_value = {
                "name": "tank",
                "state": "ONLINE",
                "size": 1000000000,
                "allocated": 500000000,
                "free": 500000000,
            }

            from uma_api.models import ZFSPool

            result = await client.get_zfs_pool("tank")

            assert isinstance(result, ZFSPool)
            assert result.name == "tank"
            mock_request.assert_called_once_with("GET", "/zfs/pools/tank")

    @pytest.mark.asyncio
    async def test_get_nut_info(self, client):
        """Test get_nut_info method."""
        with patch.object(client, "_request", new_callable=AsyncMock) as mock_request:
            mock_request.return_value = {"enabled": True, "ups_name": "myups"}

            result = await client.get_nut_info()

            assert isinstance(result, NUTInfo)
            mock_request.assert_called_once_with("GET", "/nut")

    @pytest.mark.asyncio
    async def test_get_collectors_status(self, client):
        """Test get_collectors_status method."""
        with patch.object(client, "_request", new_callable=AsyncMock) as mock_request:
            mock_request.return_value = {"collectors": []}

            result = await client.get_collectors_status()

            assert isinstance(result, CollectorStatus)
            mock_request.assert_called_once_with("GET", "/collectors/status")

    # Tests for Issue #25: Disk Settings with temperature thresholds
    @pytest.mark.asyncio
    async def test_get_disk_settings_with_thresholds(self, client):
        """Test get_disk_settings method returns full threshold data (Issue #25)."""
        with patch.object(client, "_request", new_callable=AsyncMock) as mock_request:
            mock_request.return_value = {
                "spindown_delay_minutes": 30,
                "start_array": True,
                "spinup_groups": False,
                "shutdown_timeout_seconds": 90,
                "default_filesystem": "xfs",
                "hdd_temp_warning_celsius": 45,
                "hdd_temp_critical_celsius": 55,
                "ssd_temp_warning_celsius": 60,
                "ssd_temp_critical_celsius": 70,
                "warning_utilization_percent": 70,
                "critical_utilization_percent": 90,
                "nvme_power_monitoring": False,
                "timestamp": "2026-01-22T14:18:14.815689272+10:00",
            }

            result = await client.get_disk_settings()

            assert isinstance(result, DiskSettings)
            assert result.spindown_delay_minutes == 30
            assert result.hdd_temp_warning_celsius == 45
            assert result.hdd_temp_critical_celsius == 55
            assert result.ssd_temp_warning_celsius == 60
            assert result.ssd_temp_critical_celsius == 70
            assert result.warning_utilization_percent == 70
            assert result.critical_utilization_percent == 90
            mock_request.assert_called_once_with("GET", "/settings/disk-thresholds")

    # Tests for Issue #27: Parity Schedule
    @pytest.mark.asyncio
    async def test_get_parity_schedule(self, client):
        """Test get_parity_schedule method."""
        from uma_api.models import ParitySchedule

        with patch.object(client, "_request", new_callable=AsyncMock) as mock_request:
            mock_request.return_value = {
                "mode": "weekly",
                "day": 0,
                "hour": 2,
                "day_of_month": 1,
                "frequency": 1,
                "duration_hours": 6,
                "cumulative": True,
                "correcting": True,
                "pause_hour": 6,
                "timestamp": "2026-01-22T14:18:28.611211365+10:00",
            }

            result = await client.get_parity_schedule()

            assert isinstance(result, ParitySchedule)
            assert result.mode == "weekly"
            assert result.correcting is True
            assert result.cumulative is True
            mock_request.assert_called_once_with("GET", "/array/parity-check/schedule")

    # Tests for Issue #28: Mover Settings
    @pytest.mark.asyncio
    async def test_get_mover_settings(self, client):
        """Test get_mover_settings method."""
        from uma_api.models import MoverSettings

        with patch.object(client, "_request", new_callable=AsyncMock) as mock_request:
            mock_request.return_value = {
                "active": False,
                "schedule": "0 12 * * *",
                "logging": False,
                "cache_floor_kb": 2000000,
                "timestamp": "2026-01-22T14:18:28.656460845+10:00",
            }

            result = await client.get_mover_settings()

            assert isinstance(result, MoverSettings)
            assert result.active is False
            assert result.schedule == "0 12 * * *"
            assert result.cache_floor_kb == 2000000
            mock_request.assert_called_once_with("GET", "/settings/mover")

    # Tests for Issue #29: Service Status
    @pytest.mark.asyncio
    async def test_get_service_status(self, client):
        """Test get_service_status method."""
        from uma_api.models import ServiceStatus

        with patch.object(client, "_request", new_callable=AsyncMock) as mock_request:
            mock_request.return_value = {
                "docker_enabled": True,
                "docker_autostart": True,
                "vm_manager_enabled": True,
                "vm_autostart": False,
                "timestamp": "2026-01-22T14:18:14.854247227+10:00",
            }

            result = await client.get_service_status()

            assert isinstance(result, ServiceStatus)
            assert result.docker_enabled is True
            assert result.docker_autostart is True
            assert result.vm_manager_enabled is True
            assert result.vm_autostart is False
            mock_request.assert_called_once_with("GET", "/settings/services")

    # Tests for Issue #30: Update Status
    @pytest.mark.asyncio
    async def test_get_update_status(self, client):
        """Test get_update_status method."""
        from uma_api.models import UpdateStatus

        with patch.object(client, "_request", new_callable=AsyncMock) as mock_request:
            mock_request.return_value = {
                "current_version": "7.2.3",
                "os_update_available": False,
                "total_plugins": 18,
                "plugin_updates_count": 0,
                "timestamp": "2026-01-22T14:18:33.31974833+10:00",
            }

            result = await client.get_update_status()

            assert isinstance(result, UpdateStatus)
            assert result.current_version == "7.2.3"
            assert result.os_update_available is False
            assert result.total_plugins == 18
            assert result.plugin_updates_count == 0
            mock_request.assert_called_once_with("GET", "/updates")

    # Tests for Issue #31: Flash Drive Info
    @pytest.mark.asyncio
    async def test_get_flash_info(self, client):
        """Test get_flash_info method."""
        from uma_api.models import FlashDriveInfo

        with patch.object(client, "_request", new_callable=AsyncMock) as mock_request:
            mock_request.return_value = {
                "device": "/dev/sda",
                "model": "Ultra_Fit",
                "vendor": "SanDisk",
                "guid": "0781-5583-8355-8107962689D6",
                "size_bytes": 30749130752,
                "used_bytes": 2039070720,
                "free_bytes": 28710060032,
                "usage_percent": 6.63,
                "smart_available": False,
                "timestamp": "2026-01-22T14:18:33.362127545+10:00",
            }

            result = await client.get_flash_info()

            assert isinstance(result, FlashDriveInfo)
            assert result.device == "/dev/sda"
            assert result.model == "Ultra_Fit"
            assert result.vendor == "SanDisk"
            assert result.guid == "0781-5583-8355-8107962689D6"
            assert result.usage_percent == 6.63
            mock_request.assert_called_once_with("GET", "/system/flash")

    # Tests for Issue #32: Plugin List
    @pytest.mark.asyncio
    async def test_list_plugins(self, client):
        """Test list_plugins method."""
        from uma_api.models import PluginList

        with patch.object(client, "_request", new_callable=AsyncMock) as mock_request:
            mock_request.return_value = {
                "plugins": [
                    {
                        "name": "unraid-management-agent",
                        "version": "2026.01.01",
                        "update_available": False,
                    },
                    {
                        "name": "ca.cleanup.appdata",
                        "version": "2024.11.28",
                        "update_available": False,
                    },
                ],
                "total_plugins": 2,
                "plugins_with_updates": 0,
                "timestamp": "2026-01-22T14:20:00+10:00",
            }

            result = await client.list_plugins()

            assert isinstance(result, PluginList)
            assert result.total_plugins == 2
            assert result.plugins_with_updates == 0
            assert len(result.plugins) == 2
            assert result.plugins[0].name == "unraid-management-agent"
            mock_request.assert_called_once_with("GET", "/plugins")

    # Tests for Issue #34: Network Services Status
    @pytest.mark.asyncio
    async def test_get_network_services(self, client):
        """Test get_network_services method."""
        from uma_api.models import NetworkServicesStatus

        with patch.object(client, "_request", new_callable=AsyncMock) as mock_request:
            mock_request.return_value = {
                "smb": {
                    "name": "SMB",
                    "enabled": True,
                    "running": True,
                    "port": 445,
                    "description": "Windows file sharing",
                },
                "nfs": {
                    "name": "NFS",
                    "enabled": True,
                    "running": True,
                    "port": 2049,
                    "description": "Network File System",
                },
                "afp": {
                    "name": "AFP",
                    "enabled": False,
                    "running": False,
                    "port": 548,
                    "description": "Apple Filing Protocol",
                },
                "ftp": {
                    "name": "FTP",
                    "enabled": False,
                    "running": False,
                    "port": 21,
                    "description": "File Transfer Protocol",
                },
                "ssh": {
                    "name": "SSH",
                    "enabled": True,
                    "running": True,
                    "port": 22,
                    "description": "Secure Shell",
                },
                "telnet": {
                    "name": "Telnet",
                    "enabled": False,
                    "running": False,
                    "port": 23,
                    "description": "Telnet (insecure)",
                },
                "avahi": {
                    "name": "Avahi",
                    "enabled": True,
                    "running": True,
                    "port": 5353,
                    "description": "mDNS/DNS-SD service discovery",
                },
                "netbios": {
                    "name": "NetBIOS",
                    "enabled": True,
                    "running": True,
                    "port": 137,
                    "description": "NetBIOS name service",
                },
                "wsd": {
                    "name": "WSD",
                    "enabled": True,
                    "running": True,
                    "port": 3702,
                    "description": "Web Services Discovery",
                },
                "wireguard": {
                    "name": "WireGuard",
                    "enabled": False,
                    "running": False,
                    "port": 51820,
                    "description": "WireGuard VPN",
                },
                "upnp": {
                    "name": "UPnP",
                    "enabled": False,
                    "running": False,
                    "port": 1900,
                    "description": "Universal Plug and Play",
                },
                "ntp": {
                    "name": "NTP",
                    "enabled": False,
                    "running": False,
                    "port": 123,
                    "description": "Network Time Protocol server",
                },
                "syslog": {
                    "name": "Syslog",
                    "enabled": False,
                    "running": False,
                    "port": 514,
                    "description": "Remote syslog server",
                },
                "services_enabled": 7,
                "services_running": 7,
                "timestamp": "2026-01-22T14:20:00+10:00",
            }

            result = await client.get_network_services()

            assert isinstance(result, NetworkServicesStatus)
            assert result.services_enabled == 7
            assert result.services_running == 7
            assert result.smb.running is True
            assert result.smb.port == 445
            assert result.ssh.enabled is True
            assert result.wireguard.running is False
            mock_request.assert_called_once_with("GET", "/settings/network-services")

    @pytest.mark.asyncio
    async def test_get_metrics(self, client):
        """Test get_metrics method returns Prometheus metrics at root path."""
        from unittest.mock import AsyncMock as AM

        # Mock the session's request method directly since get_metrics uses root URL
        mock_response = MagicMock()
        mock_response.status = 200
        mock_response.text = AM(
            return_value=(
                "# HELP cpu_usage_percent CPU usage percentage\n"
                "# TYPE cpu_usage_percent gauge\n"
                "cpu_usage_percent 45.5\n"
            )
        )

        mock_cm = MagicMock()
        mock_cm.__aenter__ = AM(return_value=mock_response)
        mock_cm.__aexit__ = AM(return_value=None)

        # Need to set up the session mock
        mock_session = MagicMock()
        mock_session.closed = False
        mock_session.request = MagicMock(return_value=mock_cm)
        client._session = mock_session
        client._owns_session = False

        result = await client.get_metrics()

        assert isinstance(result, str)
        assert "cpu_usage_percent" in result
        # Verify it called the root /metrics endpoint
        mock_session.request.assert_called_once()
        call_kwargs = mock_session.request.call_args
        assert call_kwargs[1]["url"] == "http://192.168.1.100:8043/metrics"
        assert call_kwargs[1]["method"] == "GET"

    @pytest.mark.asyncio
    async def test_update_system_settings(self, client):
        """Test update_system_settings method."""
        with patch.object(client, "_request", new_callable=AsyncMock) as mock_request:
            mock_request.return_value = {"success": True, "message": "Settings updated"}

            result = await client.update_system_settings({"server_name": "MyServer"})

            assert result.success is True
            mock_request.assert_called_once_with(
                "POST", "/settings/system", data={"server_name": "MyServer"}
            )

    @pytest.mark.asyncio
    async def test_get_basic_disk_settings(self, client):
        """Test get_basic_disk_settings method."""
        with patch.object(client, "_request", new_callable=AsyncMock) as mock_request:
            mock_request.return_value = {
                "spindown_delay_minutes": 30,
                "start_array": True,
                "spinup_groups": False,
                "shutdown_timeout_seconds": 90,
                "default_filesystem": "xfs",
                "timestamp": "2026-01-22T14:20:00+10:00",
            }

            result = await client.get_basic_disk_settings()

            assert isinstance(result, DiskSettings)
            assert result.spindown_delay_minutes == 30
            assert result.start_array is True
            mock_request.assert_called_once_with("GET", "/settings/disks")

    @pytest.mark.asyncio
    async def test_get_network_config(self, client):
        """Test get_network_config method with correct endpoint path."""
        with patch.object(client, "_request", new_callable=AsyncMock) as mock_request:
            mock_request.return_value = {
                "interface": "eth0",
                "ip_address": "192.168.1.100",
                "netmask": "255.255.255.0",
                "gateway": "192.168.1.1",
                "type": "physical",
                "timestamp": "2026-01-22T14:20:00+10:00",
            }

            result = await client.get_network_config("eth0")

            assert isinstance(result, NetworkConfig)
            assert result.interface == "eth0"
            assert result.ip_address == "192.168.1.100"
            mock_request.assert_called_once_with("GET", "/network/eth0/config")
