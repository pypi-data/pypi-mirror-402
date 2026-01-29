"""Unit tests for BLE scanner."""

import pytest
from wpair.core.scanner import BLEScanner
from wpair.core.device import FastPairDevice


def test_scanner_initialization():
    """Test scanner can be initialized."""
    devices_found = []

    def callback(device):
        devices_found.append(device)

    scanner = BLEScanner(callback)
    assert scanner is not None
    assert not scanner.is_currently_scanning()


def test_parse_fast_pair_pairing_mode():
    """Test parsing Fast Pair advertisement in pairing mode."""
    # Model ID with bit 7 = 0 (e.g., 0x3AB21C)
    data = bytes.fromhex("3AB21C")

    device = BLEScanner._parse_fast_pair_advertisement(
        name="JBL Tune Buds",
        address="AA:BB:CC:DD:EE:FF",
        data=data,
        rssi=-60
    )

    assert device.name == "JBL Tune Buds"
    assert device.address == "AA:BB:CC:DD:EE:FF"
    assert device.model_id == "3AB21C"
    assert device.is_pairing_mode is True
    assert device.has_account_key_filter is False
    assert device.rssi == -60


def test_parse_fast_pair_idle_mode():
    """Test parsing Fast Pair advertisement in idle mode."""
    # Idle mode: bit 5-6 set (account key filter)
    data = bytes.fromhex("60AABBCC")

    device = BLEScanner._parse_fast_pair_advertisement(
        name="Test Device",
        address="11:22:33:44:55:66",
        data=data,
        rssi=-70
    )

    assert device.is_pairing_mode is False
    assert device.has_account_key_filter is True
    assert device.model_id is None  # Not in pairing mode


def test_parse_fast_pair_extended_format():
    """Test parsing extended Fast Pair advertisement."""
    # Extended format with Model ID (bit 7 = 0, bits 5-6 = 0) + extra data
    # Use 0x12 0x34 0x56 for Model ID
    data = bytes.fromhex("12345600112233")

    device = BLEScanner._parse_fast_pair_advertisement(
        name="Extended Device",
        address="AA:BB:CC:DD:EE:FF",
        data=data,
        rssi=-55
    )

    assert device.model_id == "123456"
    assert device.rssi == -55


def test_parse_empty_advertisement():
    """Test parsing empty advertisement data."""
    data = bytes()

    device = BLEScanner._parse_fast_pair_advertisement(
        name=None,
        address="AA:BB:CC:DD:EE:FF",
        data=data,
        rssi=-80
    )

    assert device.model_id is None
    assert device.is_pairing_mode is False
    assert device.has_account_key_filter is False
