#!/usr/bin/env python3
"""
Example: Print all battery status data in one line.

This example shows how to print all available device data
with a single print() statement using the to_dict() method.
"""

import json
from sunenergyxt import SunEnergyXTClient


def main():
    # Configuration
    DEVICE_IP = "192.168.178.137"  # Change this to your device IP

    print(f"Connecting to {DEVICE_IP}...")

    try:
        with SunEnergyXTClient(DEVICE_IP) as client:
            print("✓ Connected, waiting for data...")

            # Wait for initial data from device
            if client.wait_for_data(timeout=5.0):
                print("✓ Data received!\n")
                print("=" * 70)
                print("COMPLETE BATTERY STATUS - ALL FIELDS")
                print("=" * 70)

                status = client.get_battery_status()

                # Print ALL data with a single print() statement!
                print(json.dumps(status.to_dict(), indent=2))

                print("=" * 70)
                print(f"✓ Total fields shown: {len(status.to_dict())}")

            else:
                print("✗ Timeout waiting for device data")
                return 1

    except Exception as e:
        print(f"✗ Error: {e}")
        return 1

    return 0


if __name__ == "__main__":
    exit(main())
