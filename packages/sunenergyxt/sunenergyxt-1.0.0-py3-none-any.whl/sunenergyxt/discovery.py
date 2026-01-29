"""
Device discovery using mDNS/Zeroconf.
"""

import socket
from typing import List, Optional, Callable
from zeroconf import ServiceBrowser, ServiceListener, Zeroconf, ServiceInfo

from .models import DeviceInfo
from .constants import (
    MDNS_SERVICE_TYPE,
    MDNS_DEVICE_IDENTIFIER,
    PROP_ID,
    PROP_PORT,
    PROP_FW_VERSION,
    PROP_MODEL,
)
from .exceptions import SunEnergyXTDiscoveryError


class P200ServiceListener(ServiceListener):
    """Listener for SunEnergyXT device mDNS announcements."""

    def __init__(self, callback: Optional[Callable[[DeviceInfo], None]] = None):
        """
        Initialize listener.

        Args:
            callback: Optional callback function called when device is discovered
        """
        self.devices: List[DeviceInfo] = []
        self.callback = callback
        self.zeroconf: Optional[Zeroconf] = None

    def add_service(self, zc: Zeroconf, type_: str, name: str) -> None:
        """Called when a service is discovered."""
        if MDNS_DEVICE_IDENTIFIER in name.lower():
            info = zc.get_service_info(type_, name)
            if info:
                device = self._parse_service_info(info)
                if device:
                    self.devices.append(device)
                    if self.callback:
                        self.callback(device)

    def update_service(self, zc: Zeroconf, type_: str, name: str) -> None:
        """Called when a service is updated."""
        # For now, treat updates as new discoveries
        self.add_service(zc, type_, name)

    def remove_service(self, zc: Zeroconf, type_: str, name: str) -> None:
        """Called when a service is removed."""
        # Remove device from list if it matches
        self.devices = [
            d for d in self.devices
            if d.hostname and name and d.hostname not in name
        ]

    def _parse_service_info(self, info: ServiceInfo) -> Optional[DeviceInfo]:
        """Parse ServiceInfo into DeviceInfo."""
        try:
            # Get IP address
            if not info.addresses:
                return None

            host = socket.inet_ntoa(info.addresses[0])

            # Get port
            port = info.port

            # Get properties
            props = info.properties or {}

            serial_number = props.get(PROP_ID.encode(), b"").decode("utf-8")
            firmware_version = props.get(PROP_FW_VERSION.encode(), b"").decode("utf-8")
            hardware_model = props.get(PROP_MODEL.encode(), b"").decode("utf-8")
            hostname = info.server if info.server else None

            return DeviceInfo(
                host=host,
                port=port,
                serial_number=serial_number or None,
                firmware_version=firmware_version or None,
                hardware_model=hardware_model or None,
                hostname=hostname,
            )

        except Exception as e:
            print(f"Error parsing service info: {e}")
            return None


class SunEnergyXTDiscovery:
    """
    SunEnergyXT device discovery manager.

    Example:
        discovery = SunEnergyXTDiscovery()
        discovery.start()
        # Wait for devices...
        devices = discovery.get_devices()
        discovery.stop()
    """

    def __init__(self, callback: Optional[Callable[[DeviceInfo], None]] = None):
        """
        Initialize discovery manager.

        Args:
            callback: Optional callback function called when device is discovered
        """
        self.listener = P200ServiceListener(callback)
        self.zeroconf: Optional[Zeroconf] = None
        self.browser: Optional[ServiceBrowser] = None
        self._running = False

    def start(self) -> None:
        """Start device discovery."""
        if self._running:
            return

        try:
            self.zeroconf = Zeroconf()
            self.browser = ServiceBrowser(
                self.zeroconf,
                MDNS_SERVICE_TYPE,
                self.listener
            )
            self._running = True
        except Exception as e:
            raise SunEnergyXTDiscoveryError(f"Failed to start discovery: {e}")

    def stop(self) -> None:
        """Stop device discovery."""
        if not self._running:
            return

        try:
            if self.browser:
                self.browser.cancel()
                self.browser = None

            if self.zeroconf:
                self.zeroconf.close()
                self.zeroconf = None

            self._running = False
        except Exception as e:
            raise SunEnergyXTDiscoveryError(f"Failed to stop discovery: {e}")

    def get_devices(self) -> List[DeviceInfo]:
        """
        Get list of discovered devices.

        Returns:
            List of DeviceInfo objects
        """
        return self.listener.devices.copy()

    def is_running(self) -> bool:
        """Check if discovery is running."""
        return self._running

    def __enter__(self):
        """Context manager entry."""
        self.start()
        return self

    def __exit__(self, *args):
        """Context manager exit."""
        self.stop()


def discover_devices(timeout: float = 5.0) -> List[DeviceInfo]:
    """
    Discover SunEnergyXT devices on the network.

    Args:
        timeout: Discovery timeout in seconds (default: 5.0)

    Returns:
        List of discovered DeviceInfo objects

    Example:
        devices = discover_devices(timeout=10.0)
        for device in devices:
            print(f"Found: {device}")
    """
    import time

    discovery = SunEnergyXTDiscovery()
    discovery.start()

    try:
        time.sleep(timeout)
        return discovery.get_devices()
    finally:
        discovery.stop()
