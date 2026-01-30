# secureproximity/utils.py
import asyncio
from bleak import BleakScanner
from typing import List, Tuple

async def sp_discover_nearby_devices(duration: int = 5) -> List[Tuple[str, str]]:
    """
    Discover nearby Bluetooth devices for SecureProximity using Bleak.
    Returns a list of tuples: (mac, name)
    """
    try:
        devices = await BleakScanner.discover(timeout=duration)
        normalized = []
        for device in devices:
            mac = device.address
            name = device.name or "Unknown"
            normalized.append((mac, name))
        return normalized
    except Exception as e:
        # If Bluetooth stack not available or error, return empty list
        return []
