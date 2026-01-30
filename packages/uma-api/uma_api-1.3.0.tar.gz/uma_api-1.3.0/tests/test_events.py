"""Tests for the WebSocket event models and parsing."""

from uma_api.constants import EventType
from uma_api.events import (
    ArrayStatusUpdateEvent,
    ContainerListUpdateEvent,
    DiskListUpdateEvent,
    GPUUpdateEvent,
    NetworkListUpdateEvent,
    NotificationUpdateEvent,
    ShareListUpdateEvent,
    SystemUpdateEvent,
    UnknownEvent,
    UPSStatusUpdateEvent,
    VMListUpdateEvent,
    WebSocketEvent,
    ZFSArcUpdateEvent,
    ZFSDatasetUpdateEvent,
    ZFSPoolUpdateEvent,
    ZFSSnapshotUpdateEvent,
    identify_event_type,
    parse_event,
)
from uma_api.models import (
    ArrayStatus,
    ContainerInfo,
    DiskInfo,
    GPUInfo,
    NetworkInterface,
    Notification,
    ShareInfo,
    SystemInfo,
    UPSInfo,
    VMInfo,
    ZFSArcStats,
    ZFSDataset,
    ZFSPool,
    ZFSSnapshot,
)


class TestIdentifyEventType:
    """Tests for identify_event_type function."""

    def test_system_update(self):
        """Test identifying system update events."""
        data = {
            "hostname": "unraid",
            "cpu_usage_percent": 25.5,
            "ram_usage_percent": 50.0,
        }
        assert identify_event_type(data) == EventType.SYSTEM_UPDATE

    def test_array_status_update(self):
        """Test identifying array status update events."""
        data = {
            "state": "STARTED",
            "total_disks": 10,
        }
        assert identify_event_type(data) == EventType.ARRAY_STATUS_UPDATE

    def test_disk_list_update(self):
        """Test identifying disk list update events."""
        data = [
            {"device": "/dev/sda", "filesystem": "xfs", "name": "disk1"},
        ]
        assert identify_event_type(data) == EventType.DISK_LIST_UPDATE

    def test_container_list_update(self):
        """Test identifying container list update events."""
        data = [
            {"image": "nginx:latest", "name": "nginx"},
        ]
        assert identify_event_type(data) == EventType.CONTAINER_LIST_UPDATE

    def test_vm_list_update(self):
        """Test identifying VM list update events."""
        data = [
            {"cpu_count": 4, "memory_bytes": 8589934592, "name": "Windows"},
        ]
        assert identify_event_type(data) == EventType.VM_LIST_UPDATE

    def test_network_list_update(self):
        """Test identifying network list update events."""
        data = [
            {"mac_address": "00:11:22:33:44:55", "ip_address": "192.168.1.100", "name": "eth0"},
        ]
        assert identify_event_type(data) == EventType.NETWORK_LIST_UPDATE

    def test_share_list_update(self):
        """Test identifying share list update events."""
        data = [
            {"path": "/mnt/user/media", "name": "media"},
        ]
        assert identify_event_type(data) == EventType.SHARE_LIST_UPDATE

    def test_ups_status_update(self):
        """Test identifying UPS status update events."""
        data = {
            "battery_charge_percent": 100.0,
            "load_percent": 25.0,
            "model": "APC Smart-UPS",
        }
        assert identify_event_type(data) == EventType.UPS_STATUS_UPDATE

    def test_gpu_update(self):
        """Test identifying GPU update events."""
        data = [
            {"vendor": "NVIDIA", "utilization_percent": 50.0, "name": "GTX 1080"},
        ]
        assert identify_event_type(data) == EventType.GPU_UPDATE

    def test_notification_update(self):
        """Test identifying notification update events."""
        data = [
            {"importance": "warning", "subject": "Disk warning", "id": "123"},
        ]
        assert identify_event_type(data) == EventType.NOTIFICATION_UPDATE

    def test_zfs_pool_update(self):
        """Test identifying ZFS pool update events."""
        data = [
            {"health": "ONLINE", "name": "tank"},
        ]
        assert identify_event_type(data) == EventType.ZFS_POOL_UPDATE

    def test_zfs_dataset_update(self):
        """Test identifying ZFS dataset update events."""
        data = [
            {"mountpoint": "/mnt/tank/data", "pool": "tank", "name": "tank/data"},
        ]
        assert identify_event_type(data) == EventType.ZFS_DATASET_UPDATE

    def test_zfs_snapshot_update(self):
        """Test identifying ZFS snapshot update events."""
        data = [
            {"dataset": "tank/data", "creation": "2024-01-01", "name": "tank/data@snap1"},
        ]
        assert identify_event_type(data) == EventType.ZFS_SNAPSHOT_UPDATE

    def test_zfs_arc_update(self):
        """Test identifying ZFS ARC update events."""
        data = {
            "hit_ratio_percent": 95.5,
            "size_bytes": 1073741824,
        }
        assert identify_event_type(data) == EventType.ZFS_ARC_UPDATE

    def test_empty_list(self):
        """Test that empty lists return None."""
        assert identify_event_type([]) is None

    def test_unknown_dict(self):
        """Test that unknown dict structures return None."""
        data = {"some_unknown_field": "value"}
        assert identify_event_type(data) is None

    def test_unknown_list(self):
        """Test that unknown list structures return None."""
        data = [{"unknown_field": "value"}]
        assert identify_event_type(data) is None


class TestParseEvent:
    """Tests for parse_event function."""

    def test_parse_system_update(self):
        """Test parsing system update events."""
        data = {
            "hostname": "unraid",
            "cpu_usage_percent": 25.5,
            "ram_usage_percent": 50.0,
        }
        event = parse_event(data)

        assert isinstance(event, SystemUpdateEvent)
        assert event.event_type == EventType.SYSTEM_UPDATE
        assert isinstance(event.data, SystemInfo)
        assert event.data.hostname == "unraid"
        assert event.data.cpu_usage_percent == 25.5

    def test_parse_array_status_update(self):
        """Test parsing array status update events."""
        data = {
            "state": "STARTED",
            "total_disks": 10,
            "usage_percent": 65.5,
        }
        event = parse_event(data)

        assert isinstance(event, ArrayStatusUpdateEvent)
        assert event.event_type == EventType.ARRAY_STATUS_UPDATE
        assert isinstance(event.data, ArrayStatus)
        assert event.data.state == "STARTED"

    def test_parse_disk_list_update(self):
        """Test parsing disk list update events."""
        data = [
            {"device": "/dev/sda", "filesystem": "xfs", "name": "disk1", "id": "disk1"},
            {"device": "/dev/sdb", "filesystem": "xfs", "name": "disk2", "id": "disk2"},
        ]
        event = parse_event(data)

        assert isinstance(event, DiskListUpdateEvent)
        assert event.event_type == EventType.DISK_LIST_UPDATE
        assert len(event.data) == 2
        assert all(isinstance(d, DiskInfo) for d in event.data)
        assert event.data[0].name == "disk1"

    def test_parse_container_list_update(self):
        """Test parsing container list update events."""
        data = [
            {"image": "nginx:latest", "name": "nginx", "state": "running"},
        ]
        event = parse_event(data)

        assert isinstance(event, ContainerListUpdateEvent)
        assert event.event_type == EventType.CONTAINER_LIST_UPDATE
        assert len(event.data) == 1
        assert isinstance(event.data[0], ContainerInfo)
        assert event.data[0].name == "nginx"

    def test_parse_vm_list_update(self):
        """Test parsing VM list update events."""
        data = [
            {"cpu_count": 4, "memory_bytes": 8589934592, "name": "Windows", "state": "running"},
        ]
        event = parse_event(data)

        assert isinstance(event, VMListUpdateEvent)
        assert event.event_type == EventType.VM_LIST_UPDATE
        assert len(event.data) == 1
        assert isinstance(event.data[0], VMInfo)

    def test_parse_network_list_update(self):
        """Test parsing network list update events."""
        data = [
            {"mac_address": "00:11:22:33:44:55", "ip_address": "192.168.1.100", "name": "eth0"},
        ]
        event = parse_event(data)

        assert isinstance(event, NetworkListUpdateEvent)
        assert event.event_type == EventType.NETWORK_LIST_UPDATE
        assert len(event.data) == 1
        assert isinstance(event.data[0], NetworkInterface)

    def test_parse_share_list_update(self):
        """Test parsing share list update events."""
        data = [
            {"path": "/mnt/user/media", "name": "media"},
        ]
        event = parse_event(data)

        assert isinstance(event, ShareListUpdateEvent)
        assert event.event_type == EventType.SHARE_LIST_UPDATE
        assert len(event.data) == 1
        assert isinstance(event.data[0], ShareInfo)

    def test_parse_ups_status_update(self):
        """Test parsing UPS status update events."""
        data = {
            "battery_charge_percent": 100.0,
            "load_percent": 25.0,
            "model": "APC Smart-UPS",
        }
        event = parse_event(data)

        assert isinstance(event, UPSStatusUpdateEvent)
        assert event.event_type == EventType.UPS_STATUS_UPDATE
        assert isinstance(event.data, UPSInfo)

    def test_parse_gpu_update(self):
        """Test parsing GPU update events."""
        data = [
            {"vendor": "NVIDIA", "utilization_percent": 50.0, "name": "GTX 1080"},
        ]
        event = parse_event(data)

        assert isinstance(event, GPUUpdateEvent)
        assert event.event_type == EventType.GPU_UPDATE
        assert len(event.data) == 1
        assert isinstance(event.data[0], GPUInfo)

    def test_parse_notification_update(self):
        """Test parsing notification update events."""
        data = [
            {"importance": "warning", "subject": "Disk warning", "id": "123"},
        ]
        event = parse_event(data)

        assert isinstance(event, NotificationUpdateEvent)
        assert event.event_type == EventType.NOTIFICATION_UPDATE
        assert len(event.data) == 1
        assert isinstance(event.data[0], Notification)

    def test_parse_zfs_pool_update(self):
        """Test parsing ZFS pool update events."""
        data = [
            {"health": "ONLINE", "name": "tank", "state": "ONLINE"},
        ]
        event = parse_event(data)

        assert isinstance(event, ZFSPoolUpdateEvent)
        assert event.event_type == EventType.ZFS_POOL_UPDATE
        assert len(event.data) == 1
        assert isinstance(event.data[0], ZFSPool)

    def test_parse_zfs_dataset_update(self):
        """Test parsing ZFS dataset update events."""
        data = [
            {"mountpoint": "/mnt/tank/data", "pool": "tank", "name": "tank/data"},
        ]
        event = parse_event(data)

        assert isinstance(event, ZFSDatasetUpdateEvent)
        assert event.event_type == EventType.ZFS_DATASET_UPDATE
        assert len(event.data) == 1
        assert isinstance(event.data[0], ZFSDataset)

    def test_parse_zfs_snapshot_update(self):
        """Test parsing ZFS snapshot update events."""
        data = [
            {"dataset": "tank/data", "creation": "2024-01-01", "name": "tank/data@snap1"},
        ]
        event = parse_event(data)

        assert isinstance(event, ZFSSnapshotUpdateEvent)
        assert event.event_type == EventType.ZFS_SNAPSHOT_UPDATE
        assert len(event.data) == 1
        assert isinstance(event.data[0], ZFSSnapshot)

    def test_parse_zfs_arc_update(self):
        """Test parsing ZFS ARC update events."""
        data = {
            "hit_ratio_percent": 95.5,
            "size_bytes": 1073741824,
        }
        event = parse_event(data)

        assert isinstance(event, ZFSArcUpdateEvent)
        assert event.event_type == EventType.ZFS_ARC_UPDATE
        assert isinstance(event.data, ZFSArcStats)

    def test_parse_unknown_event(self):
        """Test parsing unknown event returns UnknownEvent."""
        data = {"unknown_field": "value"}
        event = parse_event(data)

        assert isinstance(event, UnknownEvent)
        assert event.event_type is None
        assert event.data == data

    def test_parse_empty_list(self):
        """Test parsing empty list returns UnknownEvent."""
        event = parse_event([])

        assert isinstance(event, UnknownEvent)
        assert event.event_type is None


class TestWebSocketEvent:
    """Tests for WebSocketEvent base class."""

    def test_event_inheritance(self):
        """Test that all event classes inherit from WebSocketEvent."""
        data = {"hostname": "unraid", "cpu_usage_percent": 25.5}
        event = parse_event(data)

        assert isinstance(event, WebSocketEvent)

    def test_event_type_attribute(self):
        """Test that events have event_type attribute."""
        data = {"hostname": "unraid", "cpu_usage_percent": 25.5}
        event = parse_event(data)

        assert hasattr(event, "event_type")
        assert hasattr(event, "data")


class TestEventMatchPattern:
    """Tests for using events with Python match statement."""

    def test_match_system_update(self):
        """Test matching SystemUpdateEvent."""
        data = {"hostname": "unraid", "cpu_usage_percent": 25.5}
        event = parse_event(data)

        result = None
        match event:
            case SystemUpdateEvent(data=system_info):
                result = f"System: {system_info.hostname}"
            case ContainerListUpdateEvent(data=containers):
                result = f"Containers: {len(containers)}"
            case _:
                result = "Unknown"

        assert result == "System: unraid"

    def test_match_container_list(self):
        """Test matching ContainerListUpdateEvent."""
        data = [{"image": "nginx:latest", "name": "nginx"}]
        event = parse_event(data)

        result = None
        match event:
            case SystemUpdateEvent():
                result = "system"
            case ContainerListUpdateEvent(data=containers):
                result = f"containers: {len(containers)}"
            case _:
                result = "unknown"

        assert result == "containers: 1"
