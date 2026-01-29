"""Unit tests for validators."""

import pytest
from wpair.utils.validators import validate_mac_address


def test_valid_mac_addresses():
    """Test valid MAC address formats."""
    valid_addresses = [
        "AA:BB:CC:DD:EE:FF",
        "00:11:22:33:44:55",
        "FF:FF:FF:FF:FF:FF",
        "12:34:56:78:9A:BC",
        "aa:bb:cc:dd:ee:ff",  # lowercase
        "Aa:Bb:Cc:Dd:Ee:Ff",  # mixed case
    ]

    for addr in valid_addresses:
        assert validate_mac_address(addr) is True, f"Failed for {addr}"


def test_invalid_mac_addresses():
    """Test invalid MAC address formats."""
    invalid_addresses = [
        "AA:BB:CC:DD:EE",      # Too short
        "AA:BB:CC:DD:EE:FF:11", # Too long
        "ZZ:BB:CC:DD:EE:FF",   # Invalid hex
        "AA-BB-CC-DD-EE-FF",   # Wrong separator
        "AABBCCDDEEFF",        # No separators
        "",                     # Empty string
        "AA:BB:CC:DD:EE:GG",   # Invalid hex character
        "AA:BB:CC:DD:EE:F",    # Incomplete byte
        "AA:BB:CC:DD:EE:FFF",  # Too many hex digits
    ]

    for addr in invalid_addresses:
        assert validate_mac_address(addr) is False, f"Should fail for {addr}"


def test_none_address():
    """Test that None is handled."""
    # Should handle empty/None gracefully
    assert validate_mac_address("") is False
