"""
Asynchronous SunEnergyXT client implementation.
"""

import asyncio
import json
from typing import Optional, Dict, Any, Callable

from .constants import (
    Field,
    MessageCode,
    RESPONSE_SUCCESS,
    UNAVAILABLE_VALUE,
    DEFAULT_PORT,
    DEFAULT_TIMEOUT,
    IDLE_TIMEOUT,
    MAX_MESSAGE_SIZE,
    Limits,
)
from .exceptions import (
    SunEnergyXTConnectionError,
    SunEnergyXTTimeoutError,
    SunEnergyXTCommandError,
    SunEnergyXTValidationError,
)
from .models import (
    BatteryStatus,
    BatteryModule,
    ModeStatus,
    ChargingProfile,
)


class AsyncSunEnergyXTClient:
    """
    Asynchronous client for SunEnergyXT/BK215 battery storage device.

    Example:
        async with AsyncSunEnergyXTClient("192.168.1.100") as client:
            await client.enable_home_appliance_mode()
            status = await client.get_battery_status()
            print(f"Battery: {status.overall_soc}%")
    """

    def __init__(
        self,
        host: str,
        port: int = DEFAULT_PORT,
        timeout: float = DEFAULT_TIMEOUT,
    ):
        """
        Initialize async SunEnergyXT client.

        Args:
            host: Device IP address
            port: TCP port (default: 8000)
            timeout: Connection timeout in seconds (default: 2.0)
        """
        self.host = host
        self.port = port
        self.timeout = timeout

        self._reader: Optional[asyncio.StreamReader] = None
        self._writer: Optional[asyncio.StreamWriter] = None
        self._connected = False
        self._lock = asyncio.Lock()

        # Monitoring
        self._monitor_task: Optional[asyncio.Task] = None
        self._data_callback: Optional[Callable[[Dict[str, Any]], None]] = None
        self._last_data: Dict[str, Any] = {}

    async def connect(self) -> None:
        """
        Establish connection to the device.

        Raises:
            SunEnergyXTConnectionError: If connection fails
        """
        async with self._lock:
            if self._connected:
                return

            try:
                self._reader, self._writer = await asyncio.wait_for(
                    asyncio.open_connection(self.host, self.port),
                    timeout=self.timeout
                )
                self._connected = True

                # Send initial handshake message to trigger device responses
                # The device requires this to start sending status updates
                handshake = {"code": MessageCode.DATA_REPORT, "data": {}}
                handshake_str = json.dumps(handshake) + "\r\n"
                self._writer.write(handshake_str.encode('ascii'))
                await self._writer.drain()

                # Receive and discard the initial ACK response
                # Device sends {"code":0,"data":{}} immediately after handshake
                ack_data = await self._reader.read(MAX_MESSAGE_SIZE)
                # We don't need to parse it, just consume it so monitoring task gets real data

            except asyncio.TimeoutError:
                raise SunEnergyXTConnectionError(f"Connection timeout after {self.timeout}s")
            except Exception as e:
                raise SunEnergyXTConnectionError(f"Connection failed: {e}")

    async def disconnect(self) -> None:
        """Close connection to the device."""
        async with self._lock:
            await self.stop_monitoring()

            if self._writer:
                try:
                    self._writer.close()
                    await self._writer.wait_closed()
                except:
                    pass
                self._writer = None
                self._reader = None

            self._connected = False

    def is_connected(self) -> bool:
        """Check if connected to device."""
        return self._connected

    async def _send_command(self, data: Dict[str, Any]) -> Dict[str, Any]:
        """
        Send command to device and return response.

        Args:
            data: Command data dictionary

        Returns:
            Response data dictionary

        Raises:
            SunEnergyXTConnectionError: If not connected
            SunEnergyXTTimeoutError: If response timeout
            SunEnergyXTCommandError: If command fails
        """
        if not self._connected:
            raise SunEnergyXTConnectionError("Not connected to device")

        async with self._lock:
            try:
                # Prepare request
                request = {
                    "code": MessageCode.COMMAND_SET,
                    "data": data
                }

                # Send request
                request_json = json.dumps(request)
                self._writer.write(request_json.encode('ascii'))
                await self._writer.drain()

                # Receive response
                response_data = await asyncio.wait_for(
                    self._reader.read(MAX_MESSAGE_SIZE),
                    timeout=self.timeout
                )

                if not response_data:
                    raise SunEnergyXTConnectionError("Connection closed by device")

                # Parse response
                response_str = response_data.decode('ascii').strip()
                response = json.loads(response_str)

                # Validate response code
                if response.get("code") != MessageCode.RESPONSE_ACK:
                    raise SunEnergyXTCommandError(
                        f"Unexpected response code: {response.get('code')}"
                    )

                return response

            except asyncio.TimeoutError:
                raise SunEnergyXTTimeoutError(f"Response timeout after {self.timeout}s")
            except json.JSONDecodeError as e:
                raise SunEnergyXTCommandError(f"Failed to parse response: {e}")
            except Exception as e:
                self._connected = False
                raise SunEnergyXTConnectionError(f"Communication error: {e}")

    async def _set_field(self, field: str, value: Any) -> bool:
        """Set a field value on the device."""
        response = await self._send_command({field: value})

        response_value = response.get("data", {}).get(field, -1)

        if response_value != RESPONSE_SUCCESS:
            raise SunEnergyXTCommandError(
                f"Command failed for {field}",
                error_code=response_value
            )

        return True

    def _validate_range(self, value: int, min_val: int, max_val: int, name: str) -> None:
        """Validate value is within range."""
        if not isinstance(value, int):
            raise SunEnergyXTValidationError(f"{name} must be an integer")
        if not min_val <= value <= max_val:
            raise SunEnergyXTValidationError(
                f"{name} must be between {min_val} and {max_val}, got {value}"
            )

    # ========================================
    # Switch Control Methods
    # ========================================

    async def enable_local_communication(self) -> bool:
        """Enable local communication with the device."""
        return await self._set_field(Field.LOCAL_COMM_ENABLE, 1)

    async def disable_local_communication(self) -> bool:
        """Disable local communication with the device."""
        return await self._set_field(Field.LOCAL_COMM_ENABLE, 0)

    async def enable_charging_mode(self) -> bool:
        """Enable charging mode."""
        return await self._set_field(Field.CHARGING_MODE, 1)

    async def disable_charging_mode(self) -> bool:
        """Disable charging mode."""
        return await self._set_field(Field.CHARGING_MODE, 0)

    async def enable_car_charging_mode(self) -> bool:
        """Enable car (EV) charging mode."""
        return await self._set_field(Field.CAR_CHARGING_MODE, 1)

    async def disable_car_charging_mode(self) -> bool:
        """Disable car (EV) charging mode."""
        return await self._set_field(Field.CAR_CHARGING_MODE, 0)

    async def enable_home_appliance_mode(self) -> bool:
        """Enable home appliance power supply mode."""
        return await self._set_field(Field.HOME_APPLIANCE_MODE, 1)

    async def disable_home_appliance_mode(self) -> bool:
        """Disable home appliance power supply mode."""
        return await self._set_field(Field.HOME_APPLIANCE_MODE, 0)

    async def enable_ev_ac_mixed_power(self) -> bool:
        """Enable EV/AC mixed power supply mode."""
        return await self._set_field(Field.EV_AC_MIXED_POWER, 1)

    async def disable_ev_ac_mixed_power(self) -> bool:
        """Disable EV/AC mixed power supply mode."""
        return await self._set_field(Field.EV_AC_MIXED_POWER, 0)

    # ========================================
    # SOC Configuration Methods
    # ========================================

    async def set_min_discharge_soc(self, soc: int) -> bool:
        """Set minimum discharge State of Charge (1-20%)."""
        self._validate_range(
            soc,
            Limits.MIN_DISCHARGE_SOC_MIN,
            Limits.MIN_DISCHARGE_SOC_MAX,
            "Minimum discharge SOC"
        )
        return await self._set_field(Field.MIN_DISCHARGE_SOC, soc)

    async def set_max_charge_soc(self, soc: int) -> bool:
        """Set maximum charge State of Charge (70-100%)."""
        self._validate_range(
            soc,
            Limits.MAX_CHARGE_SOC_MIN,
            Limits.MAX_CHARGE_SOC_MAX,
            "Maximum charge SOC"
        )
        return await self._set_field(Field.MAX_CHARGE_SOC, soc)

    async def set_home_appliance_min_soc(self, soc: int) -> bool:
        """Set minimum SOC for home appliance mode (5-20%)."""
        self._validate_range(
            soc,
            Limits.HOME_APPLIANCE_MIN_SOC_MIN,
            Limits.HOME_APPLIANCE_MIN_SOC_MAX,
            "Home appliance minimum SOC"
        )
        return await self._set_field(Field.HOME_APPLIANCE_MIN_SOC, soc)

    async def set_ev_charging_min_soc(self, soc: int) -> bool:
        """Set minimum SOC for EV charging mode (5-40%)."""
        self._validate_range(
            soc,
            Limits.EV_CHARGING_MIN_SOC_MIN,
            Limits.EV_CHARGING_MIN_SOC_MAX,
            "EV charging minimum SOC"
        )
        return await self._set_field(Field.EV_CHARGING_MIN_SOC, soc)

    async def set_charging_max_soc(self, soc: int) -> bool:
        """Set maximum SOC for charging mode (80-100%)."""
        self._validate_range(
            soc,
            Limits.CHARGING_MAX_SOC_MIN,
            Limits.CHARGING_MAX_SOC_MAX,
            "Charging maximum SOC"
        )
        return await self._set_field(Field.CHARGING_MAX_SOC, soc)

    # ========================================
    # Power & Timeout Configuration Methods
    # ========================================

    async def set_charging_power(self, watts: int) -> bool:
        """Set system charging power limit (0-3600W)."""
        self._validate_range(
            watts,
            Limits.SYSTEM_CHARGING_POWER_MIN,
            Limits.SYSTEM_CHARGING_POWER_MAX,
            "Charging power"
        )
        return await self._set_field(Field.SYSTEM_CHARGING_POWER, watts)

    async def set_no_io_shutdown_timeout(self, minutes: int) -> bool:
        """Set auto-shutdown timeout when no I/O detected (15-1440 min)."""
        self._validate_range(
            minutes,
            Limits.NO_IO_SHUTDOWN_TIMEOUT_MIN,
            Limits.NO_IO_SHUTDOWN_TIMEOUT_MAX,
            "No I/O shutdown timeout"
        )
        return await self._set_field(Field.NO_IO_SHUTDOWN_TIMEOUT, minutes)

    async def set_dod_shutdown_timeout(self, minutes: int) -> bool:
        """Set auto-shutdown timeout when DOD limit reached (5-1440 min)."""
        self._validate_range(
            minutes,
            Limits.DOD_SHUTDOWN_TIMEOUT_MIN,
            Limits.DOD_SHUTDOWN_TIMEOUT_MAX,
            "DOD shutdown timeout"
        )
        return await self._set_field(Field.DOD_SHUTDOWN_TIMEOUT, minutes)

    # ========================================
    # Profile Management Methods
    # ========================================

    async def apply_charging_profile(self, profile: ChargingProfile) -> bool:
        """Apply a complete charging profile to the device."""
        profile.validate()

        data = {
            Field.MIN_DISCHARGE_SOC: profile.min_discharge_soc,
            Field.MAX_CHARGE_SOC: profile.max_charge_soc,
            Field.SYSTEM_CHARGING_POWER: profile.charging_power,
            Field.HOME_APPLIANCE_MIN_SOC: profile.home_appliance_min_soc,
            Field.EV_CHARGING_MIN_SOC: profile.ev_charging_min_soc,
            Field.CHARGING_MAX_SOC: profile.charging_max_soc,
            Field.NO_IO_SHUTDOWN_TIMEOUT: profile.no_io_shutdown_timeout,
            Field.DOD_SHUTDOWN_TIMEOUT: profile.dod_shutdown_timeout,
        }

        response = await self._send_command(data)

        response_data = response.get("data", {})
        for field in data.keys():
            if response_data.get(field, -1) != RESPONSE_SUCCESS:
                raise SunEnergyXTCommandError(
                    f"Profile application failed at field {field}",
                    error_code=response_data.get(field)
                )

        return True

    # ========================================
    # Status Reading Methods
    # ========================================

    def get_battery_status(self) -> Optional[BatteryStatus]:
        """Get current battery status from last received data."""
        if not self._last_data:
            return None

        data = self._last_data

        # Helper function to check if value is available
        def is_available(value):
            return value is not None and value != UNAVAILABLE_VALUE and value >= 0

        # Parse main battery
        main_soc = data.get(Field.MAIN_BATTERY_SOC)
        main_battery = None
        if is_available(main_soc):
            bms_min = data.get(Field.MAIN_BMS_MIN_SOC)
            bms_max = data.get(Field.MAIN_BMS_MAX_SOC)
            main_battery = BatteryModule(
                name="Main",
                soc=main_soc,
                bms_min_limit=bms_min if is_available(bms_min) else None,
                bms_max_limit=bms_max if is_available(bms_max) else None,
                available=True
            )

        # Parse slave batteries
        slave_configs = [
            (Field.SLAVE_1_SOC, Field.SLAVE_1_BMS_MIN_SOC, Field.SLAVE_1_BMS_MAX_SOC, "Slave 1"),
            (Field.SLAVE_2_SOC, Field.SLAVE_2_BMS_MIN_SOC, Field.SLAVE_2_BMS_MAX_SOC, "Slave 2"),
            (Field.SLAVE_3_SOC, Field.SLAVE_3_BMS_MIN_SOC, Field.SLAVE_3_BMS_MAX_SOC, "Slave 3"),
            (Field.SLAVE_4_SOC, Field.SLAVE_4_BMS_MIN_SOC, Field.SLAVE_4_BMS_MAX_SOC, "Slave 4"),
            (Field.SLAVE_5_SOC, Field.SLAVE_5_BMS_MIN_SOC, Field.SLAVE_5_BMS_MAX_SOC, "Slave 5"),
            (Field.SLAVE_6_SOC, Field.SLAVE_6_BMS_MIN_SOC, Field.SLAVE_6_BMS_MAX_SOC, "Slave 6"),
            (Field.SLAVE_7_SOC, Field.SLAVE_7_BMS_MIN_SOC, Field.SLAVE_7_BMS_MAX_SOC, "Slave 7"),
        ]

        slave_batteries = []
        for soc_field, min_field, max_field, name in slave_configs:
            soc = data.get(soc_field)
            if is_available(soc):
                bms_min = data.get(min_field) if min_field else None
                bms_max = data.get(max_field) if max_field else None
                slave = BatteryModule(
                    name=name,
                    soc=soc,
                    bms_min_limit=bms_min if is_available(bms_min) else None,
                    bms_max_limit=bms_max if is_available(bms_max) else None,
                    available=True
                )
                slave_batteries.append(slave)

        # Get overall SOC (filter out -1)
        overall_soc = data.get(Field.OVERALL_SOC)
        if not is_available(overall_soc):
            overall_soc = None

        # Helper to convert mode value to boolean
        def mode_to_bool(value):
            return value == 1 if value is not None else None

        # Get system configuration fields
        system_discharge_limit = data.get(Field.SYSTEM_DISCHARGE_LIMIT)
        if not is_available(system_discharge_limit):
            system_discharge_limit = None

        system_charge_limit = data.get(Field.SYSTEM_CHARGE_LIMIT)
        if not is_available(system_charge_limit):
            system_charge_limit = None

        system_charging_power = data.get(Field.SYSTEM_CHARGING_POWER)
        if not is_available(system_charging_power):
            system_charging_power = None

        # Get mode-specific cutoff configuration
        home_discharge_cutoff = data.get(Field.HOME_DISCHARGE_CUTOFF)
        if not is_available(home_discharge_cutoff):
            home_discharge_cutoff = None

        car_discharge_cutoff = data.get(Field.CAR_DISCHARGE_CUTOFF)
        if not is_available(car_discharge_cutoff):
            car_discharge_cutoff = None

        battery_charge_cutoff = data.get(Field.BATTERY_CHARGE_CUTOFF)
        if not is_available(battery_charge_cutoff):
            battery_charge_cutoff = None

        # Get timeout configuration
        idle_shutdown_time = data.get(Field.IDLE_SHUTDOWN_TIME)
        if not is_available(idle_shutdown_time):
            idle_shutdown_time = None

        low_battery_shutdown_time = data.get(Field.LOW_BATTERY_SHUTDOWN_TIME)
        if not is_available(low_battery_shutdown_time):
            low_battery_shutdown_time = None

        # Get operating modes
        local_mode = mode_to_bool(data.get(Field.LOCAL_MODE))
        battery_charging_mode = mode_to_bool(data.get(Field.BATTERY_CHARGING_MODE))
        car_charging_mode = mode_to_bool(data.get(Field.CAR_CHARGING_MODE))
        home_appliance_mode = mode_to_bool(data.get(Field.HOME_APPLIANCE_MODE))
        ac_active_mode = mode_to_bool(data.get(Field.AC_ACTIVE_MODE))

        # Create status object with all fields
        status = BatteryStatus(
            # Battery levels
            overall_soc=overall_soc,
            main_battery=main_battery,
            slave_batteries=slave_batteries,
            # System configuration
            system_discharge_limit=system_discharge_limit,
            system_charge_limit=system_charge_limit,
            system_charging_power=system_charging_power,
            # Mode-specific configuration
            home_discharge_cutoff=home_discharge_cutoff,
            car_discharge_cutoff=car_discharge_cutoff,
            battery_charge_cutoff=battery_charge_cutoff,
            # Timeout configuration
            idle_shutdown_time=idle_shutdown_time,
            low_battery_shutdown_time=low_battery_shutdown_time,
            # Operating modes
            local_mode=local_mode,
            battery_charging_mode=battery_charging_mode,
            car_charging_mode=car_charging_mode,
            home_appliance_mode=home_appliance_mode,
            ac_active_mode=ac_active_mode,
        )

        return status

    def get_mode_status(self) -> Optional[ModeStatus]:
        """Get current operating mode status from last received data."""
        if not self._last_data:
            return None

        data = self._last_data

        # Helper to convert mode value to boolean (-1 or 0 = False, 1 = True)
        def mode_to_bool(value):
            return value == 1 if value is not None else False

        return ModeStatus(
            local_communication=mode_to_bool(data.get(Field.LOCAL_COMM_ENABLE)),
            charging_mode=mode_to_bool(data.get(Field.CHARGING_MODE)),
            car_charging_mode=mode_to_bool(data.get(Field.CAR_CHARGING_MODE)),
            home_appliance_mode=mode_to_bool(data.get(Field.HOME_APPLIANCE_MODE)),
            ev_ac_mixed_power=mode_to_bool(data.get(Field.EV_AC_MIXED_POWER)),
        )

    def get_status_json(self, indent: int = 2) -> str:
        """
        Get complete battery status as formatted JSON string.

        Args:
            indent: Number of spaces for JSON indentation (default: 2)

        Returns:
            JSON string with all battery status data, or empty dict if no data

        Example:
            async with AsyncSunEnergyXTClient("192.168.178.137") as client:
                if await client.wait_for_data():
                    print(client.get_status_json())
        """
        status = self.get_battery_status()
        if status:
            return json.dumps(status.to_dict(), indent=indent)
        return "{}"

    # ========================================
    # Monitoring Methods
    # ========================================

    async def start_monitoring(self, callback: Optional[Callable[[Dict[str, Any]], None]] = None) -> None:
        """
        Start monitoring device status updates.

        Args:
            callback: Optional callback function called when data received
        """
        if self._monitor_task and not self._monitor_task.done():
            return

        self._data_callback = callback
        self._monitor_task = asyncio.create_task(self._monitor_loop())

    async def stop_monitoring(self) -> None:
        """Stop monitoring device status updates."""
        if self._monitor_task and not self._monitor_task.done():
            self._monitor_task.cancel()
            try:
                await self._monitor_task
            except asyncio.CancelledError:
                pass
            self._monitor_task = None

    async def wait_for_data(self, timeout: float = 5.0) -> bool:
        """
        Wait for initial data from device.

        Args:
            timeout: Maximum time to wait in seconds (default: 5.0)

        Returns:
            True if data received, False if timeout

        Example:
            async with AsyncSunEnergyXTClient("192.168.1.100") as client:
                if await client.wait_for_data():
                    status = client.get_battery_status()
                    print(f"Battery: {status.overall_soc}%")
        """
        start_time = time.time()
        while time.time() - start_time < timeout:
            if self._last_data:
                return True
            await asyncio.sleep(0.1)
        return False

    async def _monitor_loop(self) -> None:
        """Background monitoring loop."""
        while self._connected:
            try:
                # Receive data with idle timeout
                data = await asyncio.wait_for(
                    self._reader.read(MAX_MESSAGE_SIZE),
                    timeout=IDLE_TIMEOUT
                )

                if not data:
                    break

                # Parse message
                message_str = data.decode('ascii').strip()
                message = json.loads(message_str)

                # Check if it's a data report
                if message.get("code") in [MessageCode.DATA_REPORT, MessageCode.DATA_REPORT_ALT]:
                    data_dict = message.get("data", {})
                    self._last_data.update(data_dict)

                    # Call user callback
                    if self._data_callback:
                        try:
                            if asyncio.iscoroutinefunction(self._data_callback):
                                await self._data_callback(data_dict)
                            else:
                                self._data_callback(data_dict)
                        except Exception as e:
                            print(f"Error in data callback: {e}")

            except asyncio.TimeoutError:
                continue
            except asyncio.CancelledError:
                break
            except Exception as e:
                print(f"Monitor loop error: {e}")
                break

    # ========================================
    # Context Manager Methods
    # ========================================

    async def __aenter__(self):
        """Async context manager entry."""
        await self.connect()
        self.start_monitoring()  # Auto-start monitoring
        return self

    async def __aexit__(self, *args):
        """Async context manager exit."""
        await self.disconnect()

    def __repr__(self) -> str:
        status = "connected" if self._connected else "disconnected"
        return f"AsyncSunEnergyXTClient(host='{self.host}', port={self.port}, status='{status}')"
