"""
Constants and enumerations for SunEnergyXT API.
"""

from enum import Enum, IntEnum


# Protocol constants
DEFAULT_PORT = 8000
DEFAULT_TIMEOUT = 2.0
IDLE_TIMEOUT = 60.0
RECONNECT_DELAY = 5.0
MAX_MESSAGE_SIZE = 1024

# Protocol codes
class MessageCode(IntEnum):
    """Message codes used in SunEnergyXT protocol."""
    COMMAND_SET = 0x6056  # 24662 - Send command to device
    RESPONSE_ACK = 0x6057  # 24663 - Device acknowledgment
    DATA_REPORT = 0x6052  # 24658 - Device status report
    DATA_REPORT_ALT = 0x6055  # 24661 - Alternate status report


# Response codes
RESPONSE_SUCCESS = 0
UNAVAILABLE_VALUE = -1  # -1 indicates sensor not available or not configured


# Field names (t-codes) - Official SunEnergyXT API Fields
class Field:
    """Field identifiers used in SunEnergyXT protocol.

    Based on official SunEnergyXT Battery Local API documentation.
    """

    # Switches (bool: 0=OFF, 1=ON)
    LOCAL_MODE = "t598"                    # Local Mode (enable local control)
    BATTERY_CHARGING_MODE = "t700_1"       # Battery Charging Mode
    CAR_CHARGING_MODE = "t701_1"           # Car Charging Mode (EV charging)
    HOME_APPLIANCE_MODE = "t702_1"         # Home Appliance Mode
    AC_ACTIVE_MODE = "t728"                # AC Active Mode

    # Numbers - SOC limits (%)
    SYSTEM_DISCHARGE_LIMIT = "t362"        # System Discharge Limit (1-20%)
    SYSTEM_CHARGE_LIMIT = "t363"           # System Charge Limit (70-100%)
    HOME_DISCHARGE_CUTOFF = "t720"         # Discharge Cutoff SOC (Home Appliance Mode, 5-20%)
    CAR_DISCHARGE_CUTOFF = "t721"          # Discharge Cutoff SOC (Car Charging Mode, 5-40%)
    BATTERY_CHARGE_CUTOFF = "t727"         # Charge Cutoff SOC (Battery Charging Mode, 80-100%)

    # Numbers - Power and timeouts
    SYSTEM_CHARGING_POWER = "t590"         # System Charging Power (W, 0-3600)
    IDLE_SHUTDOWN_TIME = "t596"            # Idle Auto-Shutdown Time (minutes, 15-1440)
    LOW_BATTERY_SHUTDOWN_TIME = "t597"     # Low Battery Auto-Shutdown Time (minutes, 5-1440)

    # Read-Only Sensors - Battery Levels (%)
    BATTERY_LEVEL = "t211"                 # Overall battery level (%)
    HEAD_STORAGE = "t592"                  # Head storage (main battery)
    EXPANSION_1 = "t593"                   # Expansion storage 1
    EXPANSION_2 = "t594"                   # Expansion storage 2
    EXPANSION_3 = "t595"                   # Expansion storage 3
    EXPANSION_4 = "t1001"                  # Expansion storage 4
    EXPANSION_5 = "t1002"                  # Expansion storage 5
    EXPANSION_6 = "t1003"                  # Expansion storage 6
    EXPANSION_7 = "t1004"                  # Expansion storage 7

    # Read-Only Sensors - Hardware Limits (%)
    HEAD_HW_DISCHARGE_LIMIT = "t507"       # Head HW discharge limit
    HEAD_HW_CHARGE_LIMIT = "t508"          # Head HW charge limit
    EXPANSION_1_HW_DISCHARGE = "t509"      # Expansion 1 HW discharge limit
    EXPANSION_1_HW_CHARGE = "t510"         # Expansion 1 HW charge limit
    EXPANSION_2_HW_DISCHARGE = "t511"      # Expansion 2 HW discharge limit
    EXPANSION_2_HW_CHARGE = "t512"         # Expansion 2 HW charge limit
    EXPANSION_3_HW_DISCHARGE = "t513"      # Expansion 3 HW discharge limit
    EXPANSION_3_HW_CHARGE = "t514"         # Expansion 3 HW charge limit
    EXPANSION_4_HW_DISCHARGE = "t948"      # Expansion 4 HW discharge limit
    EXPANSION_4_HW_CHARGE = "t949"         # Expansion 4 HW charge limit
    EXPANSION_5_HW_DISCHARGE = "t950"      # Expansion 5 HW discharge limit
    EXPANSION_5_HW_CHARGE = "t951"         # Expansion 5 HW charge limit
    EXPANSION_6_HW_DISCHARGE = "t952"      # Expansion 6 HW discharge limit
    EXPANSION_6_HW_CHARGE = "t953"         # Expansion 6 HW charge limit
    EXPANSION_7_HW_DISCHARGE = "t954"      # Expansion 7 HW discharge limit
    EXPANSION_7_HW_CHARGE = "t955"         # Expansion 7 HW charge limit

    # Legacy aliases for backward compatibility
    LOCAL_COMM_ENABLE = "t598"             # Alias for LOCAL_MODE
    CHARGING_MODE = "t700_1"               # Alias for BATTERY_CHARGING_MODE
    EV_AC_MIXED_POWER = "t728"            # Alias for AC_ACTIVE_MODE
    MIN_DISCHARGE_SOC = "t362"             # Alias for SYSTEM_DISCHARGE_LIMIT
    MAX_CHARGE_SOC = "t363"                # Alias for SYSTEM_CHARGE_LIMIT
    HOME_APPLIANCE_MIN_SOC = "t720"        # Alias for HOME_DISCHARGE_CUTOFF
    EV_CHARGING_MIN_SOC = "t721"           # Alias for CAR_DISCHARGE_CUTOFF
    CHARGING_MAX_SOC = "t727"              # Alias for BATTERY_CHARGE_CUTOFF
    NO_IO_SHUTDOWN_TIMEOUT = "t596"        # Alias for IDLE_SHUTDOWN_TIME
    DOD_SHUTDOWN_TIMEOUT = "t597"          # Alias for LOW_BATTERY_SHUTDOWN_TIME
    OVERALL_SOC = "t211"                   # Alias for BATTERY_LEVEL
    MAIN_BATTERY_SOC = "t592"              # Alias for HEAD_STORAGE
    SLAVE_1_SOC = "t593"                   # Alias for EXPANSION_1
    SLAVE_2_SOC = "t594"                   # Alias for EXPANSION_2
    SLAVE_3_SOC = "t595"                   # Alias for EXPANSION_3
    SLAVE_4_SOC = "t1001"                  # Alias for EXPANSION_4
    SLAVE_5_SOC = "t1002"                  # Alias for EXPANSION_5
    SLAVE_6_SOC = "t1003"                  # Alias for EXPANSION_6
    SLAVE_7_SOC = "t1004"                  # Alias for EXPANSION_7
    MAIN_BMS_MIN_SOC = "t507"              # Alias for HEAD_HW_DISCHARGE_LIMIT
    MAIN_BMS_MAX_SOC = "t508"              # Alias for HEAD_HW_CHARGE_LIMIT
    SLAVE_1_BMS_MIN_SOC = "t509"           # Alias for EXPANSION_1_HW_DISCHARGE
    SLAVE_1_BMS_MAX_SOC = "t510"           # Alias for EXPANSION_1_HW_CHARGE
    SLAVE_2_BMS_MIN_SOC = "t511"           # Alias for EXPANSION_2_HW_DISCHARGE
    SLAVE_2_BMS_MAX_SOC = "t512"           # Alias for EXPANSION_2_HW_CHARGE
    SLAVE_3_BMS_MIN_SOC = "t513"           # Alias for EXPANSION_3_HW_DISCHARGE
    SLAVE_3_BMS_MAX_SOC = "t514"           # Alias for EXPANSION_3_HW_CHARGE
    SLAVE_4_BMS_MIN_SOC = "t948"           # Alias for EXPANSION_4_HW_DISCHARGE
    SLAVE_4_BMS_MAX_SOC = "t949"           # Alias for EXPANSION_4_HW_CHARGE
    SLAVE_5_BMS_MIN_SOC = "t950"           # Alias for EXPANSION_5_HW_DISCHARGE
    SLAVE_5_BMS_MAX_SOC = "t951"           # Alias for EXPANSION_5_HW_CHARGE
    SLAVE_6_BMS_MIN_SOC = "t952"           # Alias for EXPANSION_6_HW_DISCHARGE
    SLAVE_6_BMS_MAX_SOC = "t953"           # Alias for EXPANSION_6_HW_CHARGE
    SLAVE_7_BMS_MIN_SOC = "t954"           # Alias for EXPANSION_7_HW_DISCHARGE
    SLAVE_7_BMS_MAX_SOC = "t955"           # Alias for EXPANSION_7_HW_CHARGE


class OperatingMode(str, Enum):
    """Operating modes for the SunEnergyXT device.

    Based on official SunEnergyXT API documentation.
    """
    BATTERY_CHARGING = "battery_charging"     # Battery Charging Mode (t700_1)
    CAR_CHARGING = "car_charging"             # Car Charging Mode / EV Charging (t701_1)
    HOME_APPLIANCE = "home_appliance"         # Home Appliance Mode (t702_1)
    AC_ACTIVE = "ac_active"                   # AC Active Mode (t728)


# Value ranges and constraints
class Limits:
    """Value limits for configurable parameters."""

    # SOC percentage limits
    MIN_DISCHARGE_SOC_MIN = 1
    MIN_DISCHARGE_SOC_MAX = 20

    MAX_CHARGE_SOC_MIN = 70
    MAX_CHARGE_SOC_MAX = 100

    HOME_APPLIANCE_MIN_SOC_MIN = 5
    HOME_APPLIANCE_MIN_SOC_MAX = 20

    EV_CHARGING_MIN_SOC_MIN = 5
    EV_CHARGING_MIN_SOC_MAX = 40

    CHARGING_MAX_SOC_MIN = 80
    CHARGING_MAX_SOC_MAX = 100

    # Power limits
    SYSTEM_CHARGING_POWER_MIN = 0
    SYSTEM_CHARGING_POWER_MAX = 3600

    # Timeout limits (minutes)
    NO_IO_SHUTDOWN_TIMEOUT_MIN = 15
    NO_IO_SHUTDOWN_TIMEOUT_MAX = 1440

    DOD_SHUTDOWN_TIMEOUT_MIN = 5
    DOD_SHUTDOWN_TIMEOUT_MAX = 1440


# mDNS discovery constants
MDNS_SERVICE_TYPE = "_http._tcp.local."
MDNS_DEVICE_IDENTIFIER = "hp-bk215"

# Device info property keys
PROP_ID = "id"
PROP_PORT = "port"
PROP_FW_VERSION = "fw_ver"
PROP_MODEL = "model"
