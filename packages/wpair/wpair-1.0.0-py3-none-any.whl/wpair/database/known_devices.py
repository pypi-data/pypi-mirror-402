"""Database of known Fast Pair devices from CVE-2025-36911 research."""

from dataclasses import dataclass
from typing import Optional


@dataclass
class DeviceInfo:
    """Information about a known Fast Pair device."""
    name: str
    manufacturer: str
    known_vulnerable: bool = True


class KnownDevices:
    """Database of known Fast Pair devices from CVE-2025-36911 research."""

    DEVICES = {
        # Google
        "30018E": DeviceInfo("Pixel Buds Pro 2", "Google"),

        # Sony
        "CD8256": DeviceInfo("WF-1000XM4", "Sony"),
        "0E30C3": DeviceInfo("WH-1000XM5", "Sony"),
        "D5BC6B": DeviceInfo("WH-1000XM6", "Sony"),
        "821F66": DeviceInfo("LinkBuds S", "Sony"),

        # JBL
        "F52494": DeviceInfo("Tune Buds", "JBL"),
        "718FA4": DeviceInfo("Live Pro 2", "JBL"),
        "D446A7": DeviceInfo("Tune Beam", "JBL"),

        # Anker/Soundcore
        "9D3F8A": DeviceInfo("Soundcore Liberty 4", "Anker"),
        "F0B77F": DeviceInfo("Soundcore Liberty 4 NC", "Anker"),

        # Nothing
        "D0A72C": DeviceInfo("Ear (a)", "Nothing"),

        # OnePlus
        "D97EBA": DeviceInfo("Nord Buds 3 Pro", "OnePlus"),

        # Xiaomi
        "AE3989": DeviceInfo("Redmi Buds 5 Pro", "Xiaomi"),

        # Jabra
        "D446F9": DeviceInfo("Elite 8 Active", "Jabra"),

        # Samsung (generally patched)
        "0082DA": DeviceInfo("Galaxy Buds2 Pro", "Samsung", known_vulnerable=False),
        "00FA72": DeviceInfo("Galaxy Buds FE", "Samsung", known_vulnerable=False),

        # Bose
        "F00002": DeviceInfo("QuietComfort Earbuds II", "Bose"),

        # Beats
        "000006": DeviceInfo("Beats Studio Buds +", "Beats"),
    }

    @classmethod
    def get_device_info(cls, model_id: Optional[str]) -> Optional[DeviceInfo]:
        """Get device info by Model ID."""
        if model_id is None:
            return None
        return cls.DEVICES.get(model_id.upper())

    @classmethod
    def get_device_name(cls, model_id: Optional[str]) -> Optional[str]:
        """Get device name by Model ID."""
        info = cls.get_device_info(model_id)
        return info.name if info else None

    @classmethod
    def get_manufacturer(cls, model_id: Optional[str]) -> Optional[str]:
        """Get manufacturer by Model ID."""
        info = cls.get_device_info(model_id)
        return info.manufacturer if info else None

    @classmethod
    def is_known_vulnerable(cls, model_id: Optional[str]) -> bool:
        """Check if device is in known vulnerable list."""
        info = cls.get_device_info(model_id)
        return info.known_vulnerable if info else False
