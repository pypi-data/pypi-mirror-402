# SunEnergyXT Python API

A Python library for controlling and monitoring SunEnergyXT battery storage devices (BK215, BK215 Plus, B215, B215 Plus, EV3600, etc.).

[![Python Version](https://img.shields.io/badge/python-3.8+-blue.svg)](https://www.python.org/downloads/)
[![License](https://img.shields.io/badge/license-MIT-green.svg)](LICENSE)

---

## About Sonnenladen GmbH

**This library is proudly published, maintained, and developed by Sonnenladen GmbH. Our collaboration with the SunEnergyXT R&D Team has been instrumental in making this API a reality. At Sonnenladen GmbH, we are committed to providing top-notch solar energy solutions and are excited to offer this library to enhance the experience of using SunEnergyXT storage systems.**

## Purchase SunEnergyXT BK215 (Plus), B215 (Plus), EV3600 etc.

For those interested in purchasing SunEnergyXT products, please visit our German online shop at [**Sonnenladen**](https://www.sonnenladen.de/). We offer all SunEnergyXT products, backed by our expertise in solar energy solutions. Your purchase helps to maintain projects like this!

---

## Features

- **Easy to Use**: Simple, intuitive API for controlling SunEnergyXT devices
- **Async Support**: Both synchronous and asynchronous client implementations
- **Device Discovery**: Automatic device discovery using mDNS/Zeroconf
- **Type Safe**: Full type hints for better IDE support
- **Comprehensive**: All device endpoints exposed with descriptive method names
- **Monitoring**: Real-time device status monitoring with callbacks
- **Validation**: Built-in parameter validation with helpful error messages

## Installation

Install from PyPI:

```bash
pip install sunenergyxt
```

Or install from source:

```bash
git clone https://github.com/SonnenladenGmbH/sunenergyxt-api.git
cd sunenergyxt-api
pip install -e .
```

## Quick Start

### Get All Data as JSON (Simplest)

```python
from sunenergyxt import SunEnergyXTClient

with SunEnergyXTClient("192.168.1.100") as client:
    if client.wait_for_data():
        # Get ALL device data as formatted JSON with one line!
        print(client.get_status_json())
```

**Output:**
```json
{
  "overall_soc": 53,
  "total_batteries": 2,
  "system_discharge_limit": 10,
  "system_charge_limit": 85,
  "system_charging_power": 300,
  "home_discharge_cutoff": 5,
  "car_discharge_cutoff": 5,
  "battery_charge_cutoff": 85,
  "idle_shutdown_time": 15,
  "low_battery_shutdown_time": 5,
  "local_mode": true,
  "battery_charging_mode": true,
  "main_battery": {
    "soc": 64,
    "bms_min_limit": 10,
    "bms_max_limit": 90
  },
  "expansion_batteries": [...],
  ...
}
```

### Control Device

```python
from sunenergyxt import SunEnergyXTClient

# Connect to device
with SunEnergyXTClient("192.168.1.100") as client:
    # Enable home appliance mode
    client.enable_home_appliance_mode()

    # Set charging limits
    client.set_max_charge_soc(90)  # Charge to 90%
    client.set_min_discharge_soc(10)  # Discharge to 10%

    # Set charging power
    client.set_charging_power(2000)  # 2000W

    # Get battery status
    status = client.get_battery_status()
    print(f"Battery: {status.overall_soc}%")
    print(f"Available modules: {status.total_batteries}")
```

### Asynchronous Client

```python
import asyncio
from sunenergyxt import AsyncSunEnergyXTClient

async def main():
    async with AsyncSunEnergyXTClient("192.168.1.100") as client:
        # Enable charging mode
        await client.enable_charging_mode()

        # Get battery status
        status = client.get_battery_status()
        if status:
            print(f"Battery: {status.overall_soc}%")

asyncio.run(main())
```

### Device Discovery

```python
from sunenergyxt import discover_devices

# Discover devices on network
devices = discover_devices(timeout=5.0)

for device in devices:
    print(f"Found: {device.serial_number} at {device.host}:{device.port}")

# Connect to first discovered device
if devices:
    with SunEnergyXTClient(devices[0].host, devices[0].port) as client:
        print("Connected!")
```

## Usage Examples

### Control Operating Modes

```python
from sunenergyxt import SunEnergyXTClient

with SunEnergyXTClient("192.168.1.100") as client:
    # Enable different modes
    client.enable_charging_mode()
    client.enable_home_appliance_mode()
    client.enable_car_charging_mode()
    client.enable_ev_ac_mixed_power()

    # Disable modes
    client.disable_charging_mode()
```

### Configure Battery Limits

```python
from sunenergyxt import SunEnergyXTClient

with SunEnergyXTClient("192.168.1.100") as client:
    # Set overall SOC limits
    client.set_min_discharge_soc(10)  # Min 10%
    client.set_max_charge_soc(90)     # Max 90%

    # Set mode-specific limits
    client.set_home_appliance_min_soc(15)  # 15% for home appliances
    client.set_ev_charging_min_soc(20)     # 20% for EV charging
    client.set_charging_max_soc(95)        # 95% max when charging
```

### Apply Complete Charging Profile

```python
from sunenergyxt import SunEnergyXTClient, ChargingProfile

# Create profile
profile = ChargingProfile(
    min_discharge_soc=10,
    max_charge_soc=90,
    charging_power=2500,
    home_appliance_min_soc=15,
    ev_charging_min_soc=20,
    charging_max_soc=95,
    no_io_shutdown_timeout=60,
    dod_shutdown_timeout=30
)

# Apply to device
with SunEnergyXTClient("192.168.1.100") as client:
    client.apply_charging_profile(profile)
    print("Profile applied successfully!")
```

### Monitor Battery Status

```python
from sunenergyxt import SunEnergyXTClient
import time

def on_update(data):
    print(f"SOC: {data.get('t211')}%")

with SunEnergyXTClient("192.168.1.100") as client:
    # Start monitoring with callback
    client.start_monitoring(callback=on_update)

    # Keep running
    time.sleep(60)

    # Get latest status
    status = client.get_battery_status()
    if status:
        print(f"\nFinal status: {status}")
        for battery in status.all_batteries:
            if battery.is_available:
                print(f"  {battery.name}: {battery.soc}%")
```

### Async Monitoring

```python
import asyncio
from sunenergyxt import AsyncSunEnergyXTClient

async def monitor_device():
    async def on_data(data):
        print(f"Update: SOC={data.get('t211')}%")

    async with AsyncSunEnergyXTClient("192.168.1.100") as client:
        await client.start_monitoring(callback=on_data)

        # Monitor for 60 seconds
        await asyncio.sleep(60)

        # Get status
        status = client.get_battery_status()
        print(f"Status: {status}")

asyncio.run(monitor_device())
```

### Handle Errors

```python
from sunenergyxt import SunEnergyXTClient
from sunenergyxt.exceptions import (
    SunEnergyXTConnectionError,
    SunEnergyXTCommandError,
    SunEnergyXTValidationError,
    SunEnergyXTTimeoutError
)

try:
    with SunEnergyXTClient("192.168.1.100", timeout=5.0) as client:
        # Try to set invalid value
        client.set_max_charge_soc(150)  # Out of range!

except SunEnergyXTValidationError as e:
    print(f"Validation error: {e}")
except SunEnergyXTConnectionError as e:
    print(f"Connection error: {e}")
except SunEnergyXTCommandError as e:
    print(f"Command error: {e} (code: {e.error_code})")
except SunEnergyXTTimeoutError as e:
    print(f"Timeout: {e}")
```

## API Reference

### Client Methods

#### Mode Control
- `enable_local_communication()` / `disable_local_communication()`
- `enable_charging_mode()` / `disable_charging_mode()`
- `enable_car_charging_mode()` / `disable_car_charging_mode()`
- `enable_home_appliance_mode()` / `disable_home_appliance_mode()`
- `enable_ev_ac_mixed_power()` / `disable_ev_ac_mixed_power()`

#### SOC Configuration
- `set_min_discharge_soc(soc: int)` - Set minimum discharge level (1-20%)
- `set_max_charge_soc(soc: int)` - Set maximum charge level (70-100%)
- `set_home_appliance_min_soc(soc: int)` - Set home appliance minimum (5-20%)
- `set_ev_charging_min_soc(soc: int)` - Set EV charging minimum (5-40%)
- `set_charging_max_soc(soc: int)` - Set charging maximum (80-100%)

#### Power & Timeouts
- `set_charging_power(watts: int)` - Set charging power (0-3600W)
- `set_no_io_shutdown_timeout(minutes: int)` - Set idle shutdown (15-1440 min)
- `set_dod_shutdown_timeout(minutes: int)` - Set DOD shutdown (5-1440 min)

#### Profile Management
- `apply_charging_profile(profile: ChargingProfile)` - Apply complete profile

#### Status & Monitoring
- `get_battery_status() -> BatteryStatus` - Get complete battery status
- `get_status_json(indent: int = 2) -> str` - Get all data as formatted JSON string
- `get_mode_status() -> ModeStatus` - Get operating mode status
- `wait_for_data(timeout: float = 5.0) -> bool` - Wait for initial data from device
- `start_monitoring(callback)` - Start monitoring updates
- `stop_monitoring()` - Stop monitoring

#### Connection
- `connect()` - Establish connection
- `disconnect()` - Close connection
- `is_connected() -> bool` - Check connection status

### Data Models

#### BatteryStatus
```python
@dataclass
class BatteryStatus:
    # Battery Levels (Read-Only)
    overall_soc: Optional[int]                    # Overall state of charge %
    main_battery: Optional[BatteryModule]         # Main battery module
    slave_batteries: List[BatteryModule]          # Expansion battery modules

    # System Configuration (Read/Write)
    system_discharge_limit: Optional[int]         # Min discharge SOC (1-20%)
    system_charge_limit: Optional[int]            # Max charge SOC (70-100%)
    system_charging_power: Optional[int]          # Charging power (0-3600W)

    # Mode-Specific Configuration (Read/Write)
    home_discharge_cutoff: Optional[int]          # Home appliance mode (5-20%)
    car_discharge_cutoff: Optional[int]           # Car charging mode (5-40%)
    battery_charge_cutoff: Optional[int]          # Battery charging mode (80-100%)

    # Timeout Configuration (Read/Write)
    idle_shutdown_time: Optional[int]             # Idle auto-shutdown (15-1440 min)
    low_battery_shutdown_time: Optional[int]      # Low battery shutdown (5-1440 min)

    # Operating Modes (Read/Write)
    local_mode: Optional[bool]                    # Local mode enabled
    battery_charging_mode: Optional[bool]         # Battery charging mode
    car_charging_mode: Optional[bool]             # Car charging mode
    home_appliance_mode: Optional[bool]           # Home appliance mode
    ac_active_mode: Optional[bool]                # AC active mode

    timestamp: datetime                           # Last update timestamp

    @property
    def total_batteries(self) -> int              # Count of available batteries

    @property
    def all_batteries(self) -> List[BatteryModule]  # All battery modules

    def to_dict(self) -> Dict                     # Convert to dictionary
```

#### BatteryModule
```python
@dataclass
class BatteryModule:
    name: str
    soc: Optional[int]              # State of charge %
    bms_min_limit: Optional[int]    # BMS minimum limit %
    bms_max_limit: Optional[int]    # BMS maximum limit %
    available: bool

    @property
    def is_available(self) -> bool
```

#### ModeStatus
```python
@dataclass
class ModeStatus:
    local_communication: bool
    charging_mode: bool
    car_charging_mode: bool
    home_appliance_mode: bool
    ev_ac_mixed_power: bool

    def active_modes(self) -> List[str]
```

#### ChargingProfile
```python
@dataclass
class ChargingProfile:
    min_discharge_soc: int = 10
    max_charge_soc: int = 90
    charging_power: int = 3600
    home_appliance_min_soc: int = 10
    ev_charging_min_soc: int = 20
    charging_max_soc: int = 95
    no_io_shutdown_timeout: int = 60
    dod_shutdown_timeout: int = 30

    def validate(self) -> None
```

#### DeviceInfo
```python
@dataclass
class DeviceInfo:
    host: str
    port: int
    serial_number: Optional[str]
    firmware_version: Optional[str]
    hardware_model: Optional[str]
    hostname: Optional[str]
```

### Exceptions

All exceptions inherit from `SunEnergyXTError`:

- `SunEnergyXTConnectionError` - Connection failures
- `SunEnergyXTTimeoutError` - Operation timeouts
- `SunEnergyXTCommandError` - Command execution failures (has `error_code` attribute)
- `SunEnergyXTValidationError` - Parameter validation failures
- `SunEnergyXTDiscoveryError` - Device discovery failures

## Advanced Usage

### Custom Timeout

```python
from sunenergyxt import SunEnergyXTClient

# 10 second timeout for slow networks
client = SunEnergyXTClient("192.168.1.100", timeout=10.0)
client.connect()
```

### Manual Device Discovery

```python
from sunenergyxt import SunEnergyXTDiscovery
import time

def on_device_found(device):
    print(f"Discovered: {device}")

discovery = SunEnergyXTDiscovery(callback=on_device_found)
discovery.start()

time.sleep(10)

devices = discovery.get_devices()
print(f"Found {len(devices)} devices")

discovery.stop()
```

### Context Manager for Discovery

```python
from sunenergyxt import SunEnergyXTDiscovery

with SunEnergyXTDiscovery() as discovery:
    import time
    time.sleep(5)
    devices = discovery.get_devices()
    print(f"Found {len(devices)} devices")
```

## Protocol Details

The SunEnergyXT device uses a TCP-based JSON protocol:

- **Protocol**: TCP/IP with JSON payloads
- **Default Port**: 8000
- **Encoding**: ASCII
- **Message Format**: `{"code": <int>, "data": {<fields>}}`
- **Discovery**: mDNS service type `_http._tcp.local.`

### Message Codes

- `0x6056` (24662) - Command to set values
- `0x6057` (24663) - Command acknowledgment
- `0x6052` (24658) - Device status report
- `0x6055` (24661) - Alternate status report

## Supported Devices

This library supports all SunEnergyXT battery storage systems:
- **BK215** / BK215 Plus
- **B215** / B215 Plus
- **EV3600**
- And other compatible SunEnergyXT models

## Troubleshooting

### Device Not Discovered

1. Ensure device is on same network
2. Check mDNS/Bonjour is enabled on your system
3. Try manual connection with IP address

### Connection Timeout

1. Verify IP address is correct
2. Check firewall settings
3. Increase timeout parameter
4. Ensure device is powered on

### Command Fails

1. Check parameter ranges
2. Verify device is in correct mode
3. Check BMS hardware limits
4. Review error code in exception

### No Data Reports

1. Enable local communication: `client.enable_local_communication()`
2. Start monitoring: `client.start_monitoring()`
3. Keep connection alive
4. Check device configuration

## License

This project is licensed under the MIT License - see the [LICENSE](LICENSE) file for details.

Copyright (c) 2026 Sonnenladen GmbH - www.sonnenladen.de

## Acknowledgments

- Developed in collaboration with SunEnergyXT R&D Team
- Protocol documentation based on device analysis & docs
- Maintained by Sonnenladen GmbH

## Links

- **Sonnenladen Shop**: https://www.sonnenladen.de/

---

**Proudly developed and maintained by Sonnenladen GmbH** ☀️🔋
