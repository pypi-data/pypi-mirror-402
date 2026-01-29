#!/usr/bin/env python3
"""
Example: Get all battery data as JSON with a single line.

This example shows the simplest possible way to get all device data
as formatted JSON - just one method call after connecting!
"""

from sunenergyxt import SunEnergyXTClient


def main():
    # Configuration
    DEVICE_IP = "192.168.178.137"  # Change this to your device IP

    with SunEnergyXTClient(DEVICE_IP) as client:
        if client.wait_for_data(timeout=5.0):
            # Get ALL data as JSON with a single line!
            print(client.get_status_json())
        else:
            print("No data received")


if __name__ == "__main__":
    main()
