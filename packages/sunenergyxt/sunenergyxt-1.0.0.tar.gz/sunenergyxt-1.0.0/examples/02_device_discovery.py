#!/usr/bin/env python3
"""
Device discovery example.

This example shows how to:
- Discover SunEnergyXT devices on the network
- Display device information
- Connect to discovered device
"""

from sunenergyxt import discover_devices, SunEnergyXTClient


def main():
    print("Discovering SunEnergyXT devices on network...")
    print("(This will take 5 seconds)\n")

    # Discover devices
    devices = discover_devices(timeout=5.0)

    if not devices:
        print("No devices found!")
        print("\nTroubleshooting:")
        print("- Ensure device is powered on")
        print("- Check device is on same network")
        print("- Verify mDNS/Bonjour is enabled")
        return 1

    print(f"Found {len(devices)} device(s):\n")

    # Display discovered devices
    for i, device in enumerate(devices, 1):
        print(f"Device {i}:")
        print(f"  IP Address:       {device.host}")
        print(f"  Port:             {device.port}")
        print(f"  Serial Number:    {device.serial_number or 'Unknown'}")
        print(f"  Firmware Version: {device.firmware_version or 'Unknown'}")
        print(f"  Hardware Model:   {device.hardware_model or 'Unknown'}")
        print(f"  Hostname:         {device.hostname or 'Unknown'}")
        print()

    # Connect to first device
    first_device = devices[0]
    print(f"Connecting to first device ({first_device.host})...")

    try:
        with SunEnergyXTClient(first_device.host, first_device.port) as client:
            print("✓ Connected successfully!")

            # Wait for initial data from device
            print("Waiting for device status...")
            if client.wait_for_data(timeout=5.0):
                # Get status
                status = client.get_battery_status()
                if status:
                    print(status)
                    print(f"\nBattery Status:")
                    print(f"  Overall SOC: {status.overall_soc}%")
                    print(f"  Available modules: {status.total_batteries}")
                else:
                    print("\nNo status data available")
            else:
                print("\n✗ Timeout waiting for device data")

    except Exception as e:
        print(f"✗ Connection failed: {e}")
        return 1

    return 0


if __name__ == "__main__":
    exit(main())
