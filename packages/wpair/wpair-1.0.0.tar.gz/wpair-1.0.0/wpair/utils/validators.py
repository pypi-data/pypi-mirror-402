"""Validation utilities."""

import re


def validate_mac_address(address: str) -> bool:
    """
    Validate Bluetooth MAC address format.

    Args:
        address: MAC address string

    Returns:
        True if valid MAC address format, False otherwise
    """
    if not address:
        return False

    # Pattern: XX:XX:XX:XX:XX:XX where X is hex digit
    pattern = r'^([0-9A-Fa-f]{2}:){5}[0-9A-Fa-f]{2}$'
    return bool(re.match(pattern, address))
