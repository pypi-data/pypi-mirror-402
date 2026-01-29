"""Bluetooth Classic adapter - Platform-independent interface."""

import logging
import platform
from typing import Optional

logger = logging.getLogger(__name__)


class ClassicBluetoothAdapter:
    """
    Platform-independent Bluetooth Classic adapter.

    Handles device pairing and bonding via Bluetooth Classic (BR/EDR).
    """

    def __init__(self):
        self.platform = platform.system()

        # For now, use a stub implementation
        # Full Linux/Windows implementations would go in separate modules
        logger.info(f"Bluetooth Classic adapter initialized for {self.platform}")

    async def pair_device(self, address: str, pin: str = "0000") -> bool:
        """
        Pair with a Bluetooth Classic device.

        Args:
            address: MAC address of device
            pin: PIN code for pairing (default "0000")

        Returns:
            True if pairing succeeded, False otherwise
        """
        logger.warning(f"Bluetooth Classic pairing not yet implemented for {self.platform}")
        logger.info(f"Would pair with device: {address} using PIN: {pin}")
        # TODO: Implement platform-specific pairing
        return False

    async def unpair_device(self, address: str) -> bool:
        """Unpair device."""
        logger.warning(f"Bluetooth Classic unpairing not yet implemented")
        return False

    def is_paired(self, address: str) -> bool:
        """Check if device is paired."""
        logger.warning(f"Bluetooth Classic pairing check not yet implemented")
        return False
