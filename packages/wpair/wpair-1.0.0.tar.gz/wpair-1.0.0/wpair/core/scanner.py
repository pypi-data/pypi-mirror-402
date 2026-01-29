"""BLE Scanner for Fast Pair devices."""

import asyncio
import logging
from typing import Callable, Optional, Set
from bleak import BleakScanner
from bleak.backends.device import BLEDevice
from bleak.backends.scanner import AdvertisementData

from wpair.core.device import FastPairDevice

logger = logging.getLogger(__name__)


class BLEScanner:
    """
    Scans for Fast Pair capable Bluetooth Low Energy devices.

    This scanner filters for devices advertising the Fast Pair service
    (UUID: 0xFE2C) and parses their advertisement data to extract
    Model ID, pairing mode status, and signal strength.
    """

    FAST_PAIR_SERVICE_UUID = "0000fe2c-0000-1000-8000-00805f9b34fb"

    def __init__(self, on_device_found: Callable[[FastPairDevice], None]):
        """
        Initialize BLE scanner.

        Args:
            on_device_found: Callback invoked when a device is discovered
        """
        self.on_device_found = on_device_found
        self._scanner: Optional[BleakScanner] = None
        self._is_scanning = False
        self._scan_all_devices = False
        self._discovered_addresses: Set[str] = set()

    async def start_scanning(self, scan_all: bool = False) -> bool:
        """
        Start scanning for BLE devices.

        Args:
            scan_all: If True, scan all BLE devices. If False, filter for Fast Pair only.

        Returns:
            True if scan started successfully, False otherwise.
        """
        if self._is_scanning:
            logger.warning("Already scanning")
            return True

        self._scan_all_devices = scan_all
        self._discovered_addresses.clear()

        try:
            # Create scanner with detection callback
            self._scanner = BleakScanner(
                detection_callback=self._handle_device_found,
                service_uuids=None if scan_all else [self.FAST_PAIR_SERVICE_UUID]
            )

            await self._scanner.start()
            self._is_scanning = True

            mode = "all BLE devices" if scan_all else "Fast Pair devices only"
            logger.info(f"Started scanning for {mode}")
            return True

        except Exception as e:
            logger.error(f"Failed to start BLE scan: {e}")
            return False

    async def stop_scanning(self):
        """Stop the BLE scan."""
        if not self._is_scanning or not self._scanner:
            return

        try:
            await self._scanner.stop()
            self._is_scanning = False
            logger.info("Stopped BLE scanning")
        except Exception as e:
            logger.error(f"Error stopping scan: {e}")

    def is_currently_scanning(self) -> bool:
        """Check if scanner is currently active."""
        return self._is_scanning

    def _handle_device_found(self, device: BLEDevice, advertisement_data: AdvertisementData):
        """
        Process discovered BLE device.

        Args:
            device: BLE device object from Bleak
            advertisement_data: Advertisement data from device
        """
        # Avoid duplicates
        if device.address in self._discovered_addresses:
            return
        self._discovered_addresses.add(device.address)

        # Check for Fast Pair service data
        service_data = advertisement_data.service_data
        fast_pair_data = service_data.get(self.FAST_PAIR_SERVICE_UUID)

        if fast_pair_data is not None:
            # Parse Fast Pair advertisement
            fp_device = self._parse_fast_pair_advertisement(
                name=device.name,
                address=device.address,
                data=fast_pair_data,
                rssi=advertisement_data.rssi
            )
            self.on_device_found(fp_device)

        elif self._scan_all_devices:
            # Generic BLE device (not Fast Pair)
            generic_device = FastPairDevice(
                name=device.name,
                address=device.address,
                is_pairing_mode=False,
                has_account_key_filter=False,
                model_id=None,
                rssi=advertisement_data.rssi,
                is_fast_pair=False
            )
            self.on_device_found(generic_device)

    @staticmethod
    def _parse_fast_pair_advertisement(
        name: Optional[str],
        address: str,
        data: bytes,
        rssi: int
    ) -> FastPairDevice:
        """
        Parse Fast Pair service data from advertisement.

        Fast Pair Advertisement Formats:
        - Pairing Mode: 3 bytes (Model ID), bit 7 of byte 0 = 0
        - Idle Mode: Variable length with Account Key Filter, bits 5-6 != 0

        Args:
            name: Device name
            address: MAC address
            data: Service data bytes
            rssi: Signal strength

        Returns:
            FastPairDevice object with parsed information
        """
        model_id: Optional[str] = None
        is_pairing_mode = False
        has_account_key_filter = False

        if len(data) > 0:
            first_byte = data[0]

            # Check for 3-byte Model ID (pairing mode)
            # In pairing mode, bit 7 of first byte is 0
            if len(data) == 3 and (first_byte & 0x80) == 0:
                model_id = data.hex().upper()
                is_pairing_mode = True
                logger.debug(f"Device in PAIRING MODE: {address}, Model ID: {model_id}")

            # Check for Account Key Filter (idle mode) - check this before extended format
            # Bits 5-6 indicate filter type (0x60 = bits 5 and 6)
            elif (first_byte & 0x60) != 0:
                has_account_key_filter = True
                is_pairing_mode = False
                logger.debug(f"Device in IDLE mode (has account key filter): {address}")

            # Extended format with Model ID (bit 7 = 0, > 3 bytes, no account key filter)
            elif len(data) > 3 and (first_byte & 0x80) == 0:
                model_id = data[:3].hex().upper()
                is_pairing_mode = False
                logger.debug(f"Device with extended data: {address}, size={len(data)}, Model ID: {model_id}")

        return FastPairDevice(
            name=name,
            address=address,
            is_pairing_mode=is_pairing_mode,
            has_account_key_filter=has_account_key_filter,
            model_id=model_id,
            rssi=rssi,
            is_fast_pair=True
        )
