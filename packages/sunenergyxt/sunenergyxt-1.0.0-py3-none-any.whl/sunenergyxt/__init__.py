"""
SunEnergyXT Battery Storage Device Python API

A Python library for controlling and monitoring SunEnergyXT battery storage devices (BK215, B215, EV3600, etc.).
"""

from .client import SunEnergyXTClient
from .async_client import AsyncSunEnergyXTClient
from .discovery import discover_devices, SunEnergyXTDiscovery
from .exceptions import (
    SunEnergyXTError,
    SunEnergyXTConnectionError,
    SunEnergyXTCommandError,
    SunEnergyXTTimeoutError,
    SunEnergyXTValidationError,
)
from .models import (
    BatteryStatus,
    DeviceInfo,
    ChargingProfile,
    ModeStatus,
)
from .constants import (
    OperatingMode,
    DEFAULT_PORT,
    DEFAULT_TIMEOUT,
)

__version__ = "1.0.0"
__author__ = "Sonnenladen GmbH"
__license__ = "MIT"

__all__ = [
    # Main clients
    "SunEnergyXTClient",
    "AsyncSunEnergyXTClient",
    # Discovery
    "discover_devices",
    "SunEnergyXTDiscovery",
    # Exceptions
    "SunEnergyXTError",
    "SunEnergyXTConnectionError",
    "SunEnergyXTCommandError",
    "SunEnergyXTTimeoutError",
    "SunEnergyXTValidationError",
    # Models
    "BatteryStatus",
    "DeviceInfo",
    "ChargingProfile",
    "ModeStatus",
    # Constants
    "OperatingMode",
    "DEFAULT_PORT",
    "DEFAULT_TIMEOUT",
    # Version
    "__version__",
]
