"""
Data models for SunEnergyXT API.
"""

from dataclasses import dataclass, field
from typing import Optional, Dict, List
from datetime import datetime


@dataclass
class DeviceInfo:
    """Information about a discovered SunEnergyXT device."""

    host: str
    port: int
    serial_number: Optional[str] = None
    firmware_version: Optional[str] = None
    hardware_model: Optional[str] = None
    hostname: Optional[str] = None

    def __str__(self) -> str:
        return f"SunEnergyXT Device (SN: {self.serial_number or 'Unknown'}) at {self.host}:{self.port}"


@dataclass
class BatteryModule:
    """Information about a single battery module."""

    name: str
    soc: Optional[int] = None  # State of Charge in %
    bms_min_limit: Optional[int] = None  # BMS minimum SOC limit
    bms_max_limit: Optional[int] = None  # BMS maximum SOC limit
    available: bool = True

    @property
    def is_available(self) -> bool:
        """Check if battery module is available (not 0xFFFF)."""
        return self.available and self.soc is not None


@dataclass
class BatteryStatus:
    """Complete battery status information with all device data."""

    # Battery Levels (Read-Only)
    overall_soc: Optional[int] = None  # t211 - Overall battery level
    main_battery: Optional[BatteryModule] = None  # t592 - Head storage
    slave_batteries: List[BatteryModule] = field(default_factory=list)  # t593-t595, t1001-t1004

    # System Configuration (Read/Write)
    system_discharge_limit: Optional[int] = None  # t362 - Min discharge SOC (1-20%)
    system_charge_limit: Optional[int] = None  # t363 - Max charge SOC (70-100%)
    system_charging_power: Optional[int] = None  # t590 - Charging power (0-3600W)

    # Mode-Specific Configuration (Read/Write)
    home_discharge_cutoff: Optional[int] = None  # t720 - Home appliance mode cutoff (5-20%)
    car_discharge_cutoff: Optional[int] = None  # t721 - Car charging mode cutoff (5-40%)
    battery_charge_cutoff: Optional[int] = None  # t727 - Battery charging mode cutoff (80-100%)

    # Timeout Configuration (Read/Write)
    idle_shutdown_time: Optional[int] = None  # t596 - Idle auto-shutdown (15-1440 min)
    low_battery_shutdown_time: Optional[int] = None  # t597 - Low battery auto-shutdown (5-1440 min)

    # Operating Modes (Read/Write)
    local_mode: Optional[bool] = None  # t598 - Local mode enabled
    battery_charging_mode: Optional[bool] = None  # t700_1 - Battery charging mode
    car_charging_mode: Optional[bool] = None  # t701_1 - Car charging mode
    home_appliance_mode: Optional[bool] = None  # t702_1 - Home appliance mode
    ac_active_mode: Optional[bool] = None  # t728 - AC active mode

    timestamp: datetime = field(default_factory=datetime.now)

    @property
    def total_batteries(self) -> int:
        """Count of available battery modules."""
        count = 1 if self.main_battery and self.main_battery.is_available else 0
        count += sum(1 for b in self.slave_batteries if b.is_available)
        return count

    @property
    def all_batteries(self) -> List[BatteryModule]:
        """Get all battery modules (main + slaves)."""
        batteries = []
        if self.main_battery:
            batteries.append(self.main_battery)
        batteries.extend(self.slave_batteries)
        return batteries

    def to_dict(self) -> Dict:
        """Convert battery status to dictionary with all fields."""
        result = {
            # Battery Levels
            "overall_soc": self.overall_soc,
            "total_batteries": self.total_batteries,

            # System Configuration
            "system_discharge_limit": self.system_discharge_limit,
            "system_charge_limit": self.system_charge_limit,
            "system_charging_power": self.system_charging_power,

            # Mode-Specific Configuration
            "home_discharge_cutoff": self.home_discharge_cutoff,
            "car_discharge_cutoff": self.car_discharge_cutoff,
            "battery_charge_cutoff": self.battery_charge_cutoff,

            # Timeout Configuration
            "idle_shutdown_time": self.idle_shutdown_time,
            "low_battery_shutdown_time": self.low_battery_shutdown_time,

            # Operating Modes
            "local_mode": self.local_mode,
            "battery_charging_mode": self.battery_charging_mode,
            "car_charging_mode": self.car_charging_mode,
            "home_appliance_mode": self.home_appliance_mode,
            "ac_active_mode": self.ac_active_mode,

            # Battery Modules
            "main_battery": {
                "soc": self.main_battery.soc,
                "bms_min_limit": self.main_battery.bms_min_limit,
                "bms_max_limit": self.main_battery.bms_max_limit,
            } if self.main_battery else None,

            "expansion_batteries": [
                {
                    "name": bat.name,
                    "soc": bat.soc,
                    "bms_min_limit": bat.bms_min_limit,
                    "bms_max_limit": bat.bms_max_limit,
                }
                for bat in self.slave_batteries if bat.is_available
            ],

            "timestamp": self.timestamp.isoformat(),
        }
        return result

    def __str__(self) -> str:
        available = self.total_batteries
        return f"Battery Status: {self.overall_soc}% overall, {available} modules available"


@dataclass
class ModeStatus:
    """Operating mode status."""

    local_communication: bool = False
    charging_mode: bool = False
    car_charging_mode: bool = False
    home_appliance_mode: bool = False
    ev_ac_mixed_power: bool = False

    def active_modes(self) -> List[str]:
        """Get list of active mode names."""
        modes = []
        if self.local_communication:
            modes.append("Local Communication")
        if self.charging_mode:
            modes.append("Charging")
        if self.car_charging_mode:
            modes.append("Car Charging")
        if self.home_appliance_mode:
            modes.append("Home Appliance")
        if self.ev_ac_mixed_power:
            modes.append("EV/AC Mixed Power")
        return modes

    def __str__(self) -> str:
        active = self.active_modes()
        if not active:
            return "No active modes"
        return f"Active modes: {', '.join(active)}"


@dataclass
class ChargingProfile:
    """Charging configuration profile."""

    min_discharge_soc: int = 10  # Minimum discharge SOC (1-20%)
    max_charge_soc: int = 90  # Maximum charge SOC (70-100%)
    charging_power: int = 3600  # System charging power in Watts (0-3600W)
    home_appliance_min_soc: int = 10  # Home appliance DOD min (5-20%)
    ev_charging_min_soc: int = 20  # EV charging DOD min (5-40%)
    charging_max_soc: int = 95  # Charging mode DOD max (80-100%)
    no_io_shutdown_timeout: int = 60  # Auto-shutdown timeout in minutes (15-1440)
    dod_shutdown_timeout: int = 30  # DOD limit shutdown timeout in minutes (5-1440)

    def validate(self) -> None:
        """Validate all parameters are within acceptable ranges."""
        from .constants import Limits
        from .exceptions import SunEnergyXTValidationError

        if not Limits.MIN_DISCHARGE_SOC_MIN <= self.min_discharge_soc <= Limits.MIN_DISCHARGE_SOC_MAX:
            raise SunEnergyXTValidationError(
                f"min_discharge_soc must be between {Limits.MIN_DISCHARGE_SOC_MIN} and {Limits.MIN_DISCHARGE_SOC_MAX}"
            )

        if not Limits.MAX_CHARGE_SOC_MIN <= self.max_charge_soc <= Limits.MAX_CHARGE_SOC_MAX:
            raise SunEnergyXTValidationError(
                f"max_charge_soc must be between {Limits.MAX_CHARGE_SOC_MIN} and {Limits.MAX_CHARGE_SOC_MAX}"
            )

        if not Limits.SYSTEM_CHARGING_POWER_MIN <= self.charging_power <= Limits.SYSTEM_CHARGING_POWER_MAX:
            raise SunEnergyXTValidationError(
                f"charging_power must be between {Limits.SYSTEM_CHARGING_POWER_MIN} and {Limits.SYSTEM_CHARGING_POWER_MAX}"
            )

        if not Limits.HOME_APPLIANCE_MIN_SOC_MIN <= self.home_appliance_min_soc <= Limits.HOME_APPLIANCE_MIN_SOC_MAX:
            raise SunEnergyXTValidationError(
                f"home_appliance_min_soc must be between {Limits.HOME_APPLIANCE_MIN_SOC_MIN} and {Limits.HOME_APPLIANCE_MIN_SOC_MAX}"
            )

        if not Limits.EV_CHARGING_MIN_SOC_MIN <= self.ev_charging_min_soc <= Limits.EV_CHARGING_MIN_SOC_MAX:
            raise SunEnergyXTValidationError(
                f"ev_charging_min_soc must be between {Limits.EV_CHARGING_MIN_SOC_MIN} and {Limits.EV_CHARGING_MIN_SOC_MAX}"
            )

        if not Limits.CHARGING_MAX_SOC_MIN <= self.charging_max_soc <= Limits.CHARGING_MAX_SOC_MAX:
            raise SunEnergyXTValidationError(
                f"charging_max_soc must be between {Limits.CHARGING_MAX_SOC_MIN} and {Limits.CHARGING_MAX_SOC_MAX}"
            )

        if not Limits.NO_IO_SHUTDOWN_TIMEOUT_MIN <= self.no_io_shutdown_timeout <= Limits.NO_IO_SHUTDOWN_TIMEOUT_MAX:
            raise SunEnergyXTValidationError(
                f"no_io_shutdown_timeout must be between {Limits.NO_IO_SHUTDOWN_TIMEOUT_MIN} and {Limits.NO_IO_SHUTDOWN_TIMEOUT_MAX}"
            )

        if not Limits.DOD_SHUTDOWN_TIMEOUT_MIN <= self.dod_shutdown_timeout <= Limits.DOD_SHUTDOWN_TIMEOUT_MAX:
            raise SunEnergyXTValidationError(
                f"dod_shutdown_timeout must be between {Limits.DOD_SHUTDOWN_TIMEOUT_MIN} and {Limits.DOD_SHUTDOWN_TIMEOUT_MAX}"
            )

    def __str__(self) -> str:
        return (
            f"Charging Profile: SOC {self.min_discharge_soc}-{self.max_charge_soc}%, "
            f"Power: {self.charging_power}W"
        )


@dataclass
class DeviceStatus:
    """Complete device status."""

    battery: BatteryStatus
    modes: ModeStatus
    timestamp: datetime = field(default_factory=datetime.now)

    def __str__(self) -> str:
        return f"{self.battery} | {self.modes}"
