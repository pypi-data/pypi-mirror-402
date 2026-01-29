"""Unit tests for known devices database."""

import pytest
from wpair.database.known_devices import KnownDevices, DeviceInfo


def test_get_device_info_valid():
    """Test getting device info for known model ID."""
    info = KnownDevices.get_device_info("F52494")

    assert info is not None
    assert info.name == "Tune Buds"
    assert info.manufacturer == "JBL"
    assert info.known_vulnerable is True


def test_get_device_info_case_insensitive():
    """Test that model ID lookup is case insensitive."""
    info_upper = KnownDevices.get_device_info("F52494")
    info_lower = KnownDevices.get_device_info("f52494")

    assert info_upper == info_lower


def test_get_device_info_none():
    """Test getting device info with None model ID."""
    info = KnownDevices.get_device_info(None)
    assert info is None


def test_get_device_info_unknown():
    """Test getting device info for unknown model ID."""
    info = KnownDevices.get_device_info("UNKNOWN")
    assert info is None


def test_get_device_name():
    """Test getting device name."""
    name = KnownDevices.get_device_name("CD8256")
    assert name == "WF-1000XM4"


def test_get_manufacturer():
    """Test getting manufacturer name."""
    manufacturer = KnownDevices.get_manufacturer("CD8256")
    assert manufacturer == "Sony"


def test_is_known_vulnerable_true():
    """Test checking if device is vulnerable."""
    is_vuln = KnownDevices.is_known_vulnerable("F52494")
    assert is_vuln is True


def test_is_known_vulnerable_false():
    """Test checking if device is patched."""
    # Samsung devices are marked as not vulnerable
    is_vuln = KnownDevices.is_known_vulnerable("0082DA")
    assert is_vuln is False


def test_is_known_vulnerable_unknown():
    """Test checking unknown device returns False."""
    is_vuln = KnownDevices.is_known_vulnerable("UNKNOWN")
    assert is_vuln is False


def test_database_coverage():
    """Test that database contains expected devices."""
    # Check we have devices from multiple manufacturers
    assert "F52494" in KnownDevices.DEVICES  # JBL
    assert "CD8256" in KnownDevices.DEVICES  # Sony
    assert "30018E" in KnownDevices.DEVICES  # Google
    assert "9D3F8A" in KnownDevices.DEVICES  # Anker
