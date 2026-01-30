"""Tests for the formatting utilities."""

from uma_api.formatting import (
    format_bytes,
    format_duration,
    format_percentage,
    format_speed,
    format_temperature,
)


class TestFormatBytes:
    """Tests for format_bytes function."""

    def test_bytes(self):
        """Test formatting bytes."""
        assert format_bytes(500) == "500.0 B"
        assert format_bytes(0) == "0.0 B"

    def test_kilobytes(self):
        """Test formatting kilobytes."""
        assert format_bytes(1024) == "1.0 KB"
        assert format_bytes(1536) == "1.5 KB"

    def test_megabytes(self):
        """Test formatting megabytes."""
        assert format_bytes(1048576) == "1.0 MB"
        assert format_bytes(536870912) == "512.0 MB"

    def test_gigabytes(self):
        """Test formatting gigabytes."""
        assert format_bytes(1073741824) == "1.0 GB"
        assert format_bytes(5368709120) == "5.0 GB"

    def test_terabytes(self):
        """Test formatting terabytes."""
        assert format_bytes(1099511627776) == "1.0 TB"
        assert format_bytes(4000000000000) == "3.6 TB"

    def test_petabytes(self):
        """Test formatting petabytes."""
        assert format_bytes(1125899906842624) == "1.0 PB"

    def test_precision(self):
        """Test custom precision."""
        assert format_bytes(1536, precision=0) == "2 KB"
        assert format_bytes(1536, precision=2) == "1.50 KB"

    def test_negative_bytes(self):
        """Test negative bytes."""
        assert format_bytes(-1024) == "-1.0 KB"

    def test_binary_vs_decimal(self):
        """Test binary (1024) vs decimal (1000) mode."""
        # Binary (default)
        assert format_bytes(1024, binary=True) == "1.0 KB"
        # Decimal
        assert format_bytes(1000, binary=False) == "1.0 KB"
        assert format_bytes(1024, binary=False) == "1.0 KB"  # Still rounds to 1.0


class TestFormatDuration:
    """Tests for format_duration function."""

    def test_seconds_only(self):
        """Test formatting seconds only."""
        assert format_duration(45) == "45 seconds"
        assert format_duration(1) == "1 second"
        assert format_duration(0) == "0 seconds"

    def test_minutes(self):
        """Test formatting minutes."""
        assert format_duration(60) == "1 minute"
        assert format_duration(120) == "2 minutes"
        assert format_duration(90) == "1 minute, 30 seconds"

    def test_hours(self):
        """Test formatting hours."""
        assert format_duration(3600) == "1 hour"
        assert format_duration(7200) == "2 hours"
        assert format_duration(3660) == "1 hour, 1 minute"

    def test_days(self):
        """Test formatting days."""
        assert format_duration(86400) == "1 day"
        assert format_duration(172800) == "2 days"
        assert format_duration(432000) == "5 days"

    def test_complex_duration(self):
        """Test complex duration with multiple units."""
        # 5 days, 3 hours, 12 minutes, 30 seconds
        assert format_duration(450750) == "5 days, 5 hours, 12 minutes, 30 seconds"

    def test_short_format(self):
        """Test short duration format."""
        assert format_duration(432000, short=True) == "5d 0h 0m"
        assert format_duration(450750, short=True) == "5d 5h 12m"
        assert format_duration(3661, short=True) == "0d 1h 1m"

    def test_negative_duration(self):
        """Test negative duration returns 0."""
        assert format_duration(-100) == "0 seconds"


class TestFormatSpeed:
    """Tests for format_speed function."""

    def test_mbps(self):
        """Test formatting Mbps."""
        assert format_speed(100) == "100 Mbps"
        assert format_speed(10) == "10 Mbps"
        assert format_speed(1) == "1 Mbps"

    def test_gbps(self):
        """Test formatting Gbps."""
        assert format_speed(1000) == "1 Gbps"
        assert format_speed(2500) == "2.5 Gbps"
        assert format_speed(10000) == "10 Gbps"

    def test_tbps(self):
        """Test formatting Tbps."""
        assert format_speed(1000000) == "1 Tbps"

    def test_zero_speed(self):
        """Test zero speed."""
        assert format_speed(0) == "0 Mbps"

    def test_negative_speed(self):
        """Test negative speed."""
        assert format_speed(-100) == "-100 Mbps"


class TestFormatPercentage:
    """Tests for format_percentage function."""

    def test_basic_percentage(self):
        """Test basic percentage formatting."""
        assert format_percentage(50.0) == "50.0%"
        assert format_percentage(100.0) == "100.0%"
        assert format_percentage(0.0) == "0.0%"

    def test_decimal_percentage(self):
        """Test percentage with decimals."""
        assert format_percentage(85.555) == "85.6%"
        assert format_percentage(33.333) == "33.3%"

    def test_precision(self):
        """Test custom precision."""
        assert format_percentage(85.555, precision=0) == "86%"
        assert format_percentage(85.555, precision=2) == "85.56%"

    def test_negative_percentage(self):
        """Test negative percentage."""
        assert format_percentage(-10.0) == "-10.0%"

    def test_over_100(self):
        """Test percentages over 100."""
        assert format_percentage(150.0) == "150.0%"


class TestFormatTemperature:
    """Tests for format_temperature function."""

    def test_positive_temperature(self):
        """Test positive temperature."""
        assert format_temperature(45.5) == "45.5°C"
        assert format_temperature(100.0) == "100.0°C"

    def test_zero_temperature(self):
        """Test zero temperature."""
        assert format_temperature(0.0) == "0.0°C"

    def test_negative_temperature(self):
        """Test negative temperature."""
        assert format_temperature(-10.5) == "-10.5°C"

    def test_precision(self):
        """Test custom precision."""
        assert format_temperature(45.567, precision=0) == "46°C"
        assert format_temperature(45.567, precision=2) == "45.57°C"

    def test_fahrenheit(self):
        """Test Fahrenheit conversion."""
        assert format_temperature(0.0, fahrenheit=True) == "32.0°F"
        assert format_temperature(100.0, fahrenheit=True) == "212.0°F"
        assert format_temperature(37.0, fahrenheit=True) == "98.6°F"
