"""Tests for the constants module (enums and event types)."""

from uma_api.constants import (
    ArrayState,
    ContainerState,
    DiskSpinState,
    DiskStatus,
    EventType,
    VMState,
)


class TestEventType:
    """Tests for EventType enum."""

    def test_system_update(self):
        """Test system update event type."""
        assert EventType.SYSTEM_UPDATE == "system_update"
        assert EventType.SYSTEM_UPDATE.value == "system_update"

    def test_array_status_update(self):
        """Test array status update event type."""
        assert EventType.ARRAY_STATUS_UPDATE == "array_status_update"

    def test_disk_list_update(self):
        """Test disk list update event type."""
        assert EventType.DISK_LIST_UPDATE == "disk_list_update"

    def test_container_list_update(self):
        """Test container list update event type."""
        assert EventType.CONTAINER_LIST_UPDATE == "container_list_update"

    def test_vm_list_update(self):
        """Test VM list update event type."""
        assert EventType.VM_LIST_UPDATE == "vm_list_update"

    def test_network_list_update(self):
        """Test network list update event type."""
        assert EventType.NETWORK_LIST_UPDATE == "network_list_update"

    def test_share_list_update(self):
        """Test share list update event type."""
        assert EventType.SHARE_LIST_UPDATE == "share_list_update"

    def test_ups_status_update(self):
        """Test UPS status update event type."""
        assert EventType.UPS_STATUS_UPDATE == "ups_status_update"

    def test_gpu_update(self):
        """Test GPU update event type."""
        assert EventType.GPU_UPDATE == "gpu_update"

    def test_notification_update(self):
        """Test notification update event type."""
        assert EventType.NOTIFICATION_UPDATE == "notification_update"

    def test_zfs_events(self):
        """Test ZFS event types."""
        assert EventType.ZFS_POOL_UPDATE == "zfs_pool_update"
        assert EventType.ZFS_DATASET_UPDATE == "zfs_dataset_update"
        assert EventType.ZFS_SNAPSHOT_UPDATE == "zfs_snapshot_update"
        assert EventType.ZFS_ARC_UPDATE == "zfs_arc_update"

    def test_event_type_is_string(self):
        """Test that EventType values can be used as strings."""
        event_type: str = EventType.SYSTEM_UPDATE
        assert event_type == "system_update"
        assert isinstance(EventType.SYSTEM_UPDATE, str)


class TestArrayState:
    """Tests for ArrayState enum."""

    def test_started(self):
        """Test started state."""
        assert ArrayState.STARTED == "Started"

    def test_stopped(self):
        """Test stopped state."""
        assert ArrayState.STOPPED == "Stopped"

    def test_starting(self):
        """Test starting state."""
        assert ArrayState.STARTING == "Starting"

    def test_stopping(self):
        """Test stopping state."""
        assert ArrayState.STOPPING == "Stopping"

    def test_maintenance(self):
        """Test maintenance state."""
        assert ArrayState.MAINTENANCE == "Maintenance"

    def test_is_string(self):
        """Test that ArrayState values can be used as strings."""
        state: str = ArrayState.STARTED
        assert state == "Started"
        assert isinstance(ArrayState.STARTED, str)


class TestContainerState:
    """Tests for ContainerState enum."""

    def test_running(self):
        """Test running state."""
        assert ContainerState.RUNNING == "running"

    def test_stopped(self):
        """Test stopped state."""
        assert ContainerState.STOPPED == "stopped"

    def test_paused(self):
        """Test paused state."""
        assert ContainerState.PAUSED == "paused"

    def test_restarting(self):
        """Test restarting state."""
        assert ContainerState.RESTARTING == "restarting"

    def test_created(self):
        """Test created state."""
        assert ContainerState.CREATED == "created"

    def test_exited(self):
        """Test exited state."""
        assert ContainerState.EXITED == "exited"

    def test_is_string(self):
        """Test that ContainerState values can be used as strings."""
        state: str = ContainerState.RUNNING
        assert state == "running"


class TestVMState:
    """Tests for VMState enum."""

    def test_running(self):
        """Test running state."""
        assert VMState.RUNNING == "running"

    def test_stopped(self):
        """Test stopped state."""
        assert VMState.STOPPED == "stopped"

    def test_paused(self):
        """Test paused state."""
        assert VMState.PAUSED == "paused"

    def test_pmsuspended(self):
        """Test pmsuspended state."""
        assert VMState.PMSUSPENDED == "pmsuspended"

    def test_shutoff(self):
        """Test shutoff state."""
        assert VMState.SHUTOFF == "shutoff"

    def test_is_string(self):
        """Test that VMState values can be used as strings."""
        state: str = VMState.RUNNING
        assert state == "running"


class TestDiskStatus:
    """Tests for DiskStatus enum."""

    def test_normal(self):
        """Test normal status."""
        assert DiskStatus.NORMAL == "Normal"

    def test_disabled(self):
        """Test disabled status."""
        assert DiskStatus.DISABLED == "Disabled"

    def test_standby(self):
        """Test standby status."""
        assert DiskStatus.STANDBY == "Standby"

    def test_absent(self):
        """Test absent status."""
        assert DiskStatus.ABSENT == "Absent"

    def test_is_string(self):
        """Test that DiskStatus values can be used as strings."""
        status: str = DiskStatus.NORMAL
        assert status == "Normal"


class TestDiskSpinState:
    """Tests for DiskSpinState enum."""

    def test_active(self):
        """Test active spin state."""
        assert DiskSpinState.ACTIVE == "active"

    def test_standby(self):
        """Test standby spin state."""
        assert DiskSpinState.STANDBY == "standby"

    def test_unknown(self):
        """Test unknown spin state."""
        assert DiskSpinState.UNKNOWN == "unknown"

    def test_is_string(self):
        """Test that DiskSpinState values can be used as strings."""
        state: str = DiskSpinState.ACTIVE
        assert state == "active"


class TestEnumComparisons:
    """Tests for enum comparisons with string values."""

    def test_compare_container_state_with_string(self):
        """Test comparing enum with raw string value."""
        container_state = "running"
        assert container_state == ContainerState.RUNNING
        assert container_state == ContainerState.RUNNING  # Bidirectional comparison

    def test_compare_array_state_with_string(self):
        """Test comparing array state enum with raw string."""
        array_state = "Started"
        assert array_state == ArrayState.STARTED
        assert array_state == ArrayState.STARTED  # Bidirectional comparison

    def test_use_in_dict_key(self):
        """Test using enum as dictionary key."""
        handlers = {
            EventType.SYSTEM_UPDATE: lambda: "system",
            EventType.CONTAINER_LIST_UPDATE: lambda: "container",
        }
        assert handlers[EventType.SYSTEM_UPDATE]() == "system"
        # Can also use string key due to str inheritance
        assert handlers["system_update"]() == "system"

    def test_use_in_match_statement(self):
        """Test using enum in match statement."""
        event_type = EventType.SYSTEM_UPDATE

        match event_type:
            case EventType.SYSTEM_UPDATE:
                result = "system"
            case EventType.CONTAINER_LIST_UPDATE:
                result = "container"
            case _:
                result = "unknown"

        assert result == "system"
