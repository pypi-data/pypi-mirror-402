"""Unit tests for device data model."""

import pytest
from wpair.core.device import FastPairDevice, DeviceStatus, SignalStrength


def test_fast_pair_device_creation():
    """Test FastPairDevice instantiation."""
    device = FastPairDevice(
        name="Test Device",
        address="AA:BB:CC:DD:EE:FF",
        is_pairing_mode=True,
        has_account_key_filter=False,
        model_id="F52494",
        rssi=-65
    )

    assert device.name == "Test Device"
    assert device.address == "AA:BB:CC:DD:EE:FF"
    assert device.is_pairing_mode is True
    assert device.signal_strength == SignalStrength.FAIR
    assert device.status == DeviceStatus.NOT_TESTED


def test_device_display_name_known():
    """Test display name for known device."""
    device = FastPairDevice(
        name=None,
        address="AA:BB:CC:DD:EE:FF",
        is_pairing_mode=False,
        has_account_key_filter=True,
        model_id="F52494"  # JBL Tune Buds
    )

    assert device.display_name == "Tune Buds"
    assert device.manufacturer == "JBL"
    assert device.is_known_vulnerable is True


def test_device_display_name_unknown():
    """Test display name for unknown device."""
    device = FastPairDevice(
        name=None,
        address="AA:BB:CC:DD:EE:FF",
        is_pairing_mode=False,
        has_account_key_filter=False,
        model_id="UNKNOWN"
    )

    assert device.display_name == "Unknown Fast Pair Device"
    assert device.manufacturer is None
    assert device.is_known_vulnerable is False


def test_signal_strength_classification():
    """Test RSSI to signal strength conversion."""
    test_cases = [
        (-45, SignalStrength.EXCELLENT),
        (-55, SignalStrength.GOOD),
        (-65, SignalStrength.FAIR),
        (-75, SignalStrength.WEAK),
        (-85, SignalStrength.VERY_WEAK),
    ]

    for rssi, expected_strength in test_cases:
        device = FastPairDevice(
            name="Test",
            address="AA:BB:CC:DD:EE:FF",
            is_pairing_mode=False,
            has_account_key_filter=False,
            rssi=rssi
        )
        assert device.signal_strength == expected_strength


def test_device_with_custom_name():
    """Test device that has a custom name."""
    device = FastPairDevice(
        name="My Custom Name",
        address="AA:BB:CC:DD:EE:FF",
        is_pairing_mode=True,
        has_account_key_filter=False,
        model_id="F52494"
    )

    # Custom name should override known device name
    assert device.display_name == "My Custom Name"
