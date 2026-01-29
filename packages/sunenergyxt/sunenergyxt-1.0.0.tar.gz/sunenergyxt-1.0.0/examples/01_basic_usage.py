#!/usr/bin/env python3
"""
Basic usage example for SunEnergyXT client.

This example shows how to:
- Connect to a device
- Enable/disable modes
- Set charging parameters
- Get battery status
"""

from sunenergyxt import SunEnergyXTClient
from sunenergyxt.exceptions import SunEnergyXTError


def main():
    # Replace with your device IP
    DEVICE_IP = "192.168.1.100"

    try:
        # Connect to device using context manager
        with SunEnergyXTClient(DEVICE_IP) as client:
            print(f"Connected to device at {DEVICE_IP}")

            # Enable home appliance mode
            print("\n1. Enabling home appliance mode...")
            client.enable_home_appliance_mode()
            print("   ✓ Home appliance mode enabled")

            # Set battery limits
            print("\n2. Configuring battery limits...")
            client.set_min_discharge_soc(10)  # Don't discharge below 10%
            client.set_max_charge_soc(90)     # Don't charge above 90%
            print("   ✓ Battery limits set (10%-90%)")

            # Set charging power
            print("\n3. Setting charging power...")
            client.set_charging_power(2000)  # 2000W
            print("   ✓ Charging power set to 2000W")

            # Get battery status (if monitoring data available)
            print("\n4. Getting battery status...")
            status = client.get_battery_status()
            if status:
                print(f"   Overall SOC: {status.overall_soc}%")
                print(f"   Available batteries: {status.total_batteries}")

                for battery in status.all_batteries:
                    if battery.is_available:
                        print(f"     - {battery.name}: {battery.soc}%")
            else:
                print("   No battery status available yet")
                print("   (Start monitoring to receive status updates)")

            print("\n✓ All operations completed successfully!")

    except SunEnergyXTError as e:
        print(f"\n✗ Error: {e}")
        return 1

    return 0


if __name__ == "__main__":
    exit(main())
