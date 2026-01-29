"""Fast Pair device data models."""

from dataclasses import dataclass, field
from enum import Enum
from typing import Optional
from datetime import datetime


class DeviceStatus(Enum):
    """Enumeration of device vulnerability states."""
    NOT_TESTED = "not_tested"
    TESTING = "testing"
    VULNERABLE = "vulnerable"
    PATCHED = "patched"
    ERROR = "error"


class SignalStrength(Enum):
    """Signal strength classification based on RSSI."""
    EXCELLENT = "excellent"  # >= -50 dBm
    GOOD = "good"            # >= -60 dBm
    FAIR = "fair"            # >= -70 dBm
    WEAK = "weak"            # >= -80 dBm
    VERY_WEAK = "very_weak"  # < -80 dBm


@dataclass
class FastPairDevice:
    """
    Represents a Fast Pair capable Bluetooth device.

    Attributes:
        name: Device name from BLE advertisement
        address: MAC address (format: "XX:XX:XX:XX:XX:XX")
        is_pairing_mode: True if device is in pairing mode
        has_account_key_filter: True if device has account key filter
        model_id: 3-byte Fast Pair Model ID (hex string)
        rssi: Signal strength in dBm
        last_seen: Timestamp of last advertisement
        status: Vulnerability test status
        is_fast_pair: True if device advertises Fast Pair service
    """
    name: Optional[str]
    address: str
    is_pairing_mode: bool
    has_account_key_filter: bool
    model_id: Optional[str] = None
    rssi: int = -100
    last_seen: datetime = field(default_factory=datetime.now)
    status: DeviceStatus = DeviceStatus.NOT_TESTED
    is_fast_pair: bool = True

    @property
    def display_name(self) -> str:
        """Get friendly display name for device."""
        from wpair.database.known_devices import KnownDevices

        if self.name:
            return self.name

        known_name = KnownDevices.get_device_name(self.model_id)
        if known_name:
            return known_name

        return "Unknown Fast Pair Device" if self.is_fast_pair else "BLE Device"

    @property
    def manufacturer(self) -> Optional[str]:
        """Get manufacturer name from known devices database."""
        from wpair.database.known_devices import KnownDevices
        return KnownDevices.get_manufacturer(self.model_id)

    @property
    def is_known_vulnerable(self) -> bool:
        """Check if device is in known vulnerable devices list."""
        from wpair.database.known_devices import KnownDevices
        return KnownDevices.is_known_vulnerable(self.model_id)

    @property
    def signal_strength(self) -> SignalStrength:
        """Calculate signal strength category from RSSI."""
        if self.rssi >= -50:
            return SignalStrength.EXCELLENT
        elif self.rssi >= -60:
            return SignalStrength.GOOD
        elif self.rssi >= -70:
            return SignalStrength.FAIR
        elif self.rssi >= -80:
            return SignalStrength.WEAK
        else:
            return SignalStrength.VERY_WEAK
