#!/usr/bin/env python3
"""
Real-time monitoring example.

This example shows how to:
- Monitor device status in real-time
- Handle status updates with callbacks
- Display battery information
"""

import time
from datetime import datetime
from sunenergyxt import SunEnergyXTClient


def on_status_update(data):
    """Callback function for status updates."""
    timestamp = datetime.now().strftime("%H:%M:%S")
    soc = data.get("t211")  # Overall SOC

    if soc is not None:
        print(f"[{timestamp}] Battery SOC: {soc}%")

    # Display other interesting data
    main_soc = data.get("t592")
    if main_soc is not None:
        print(f"             Main Battery: {main_soc}%")


def main():
    # Replace with your device IP
    DEVICE_IP = "192.168.1.100"
    MONITOR_DURATION = 60  # seconds

    print("SunEnergyXT Real-Time Monitoring")
    print("=" * 50)
    print(f"Device: {DEVICE_IP}")
    print(f"Duration: {MONITOR_DURATION} seconds")
    print("=" * 50)
    print()

    try:
        with SunEnergyXTClient(DEVICE_IP) as client:
            print("✓ Connected to device")
            print("\nStarting monitoring (press Ctrl+C to stop)...\n")

            # Start monitoring with callback
            client.start_monitoring(callback=on_status_update)

            # Monitor for specified duration
            try:
                time.sleep(MONITOR_DURATION)
            except KeyboardInterrupt:
                print("\n\nMonitoring interrupted by user")

            # Stop monitoring
            print("\nStopping monitoring...")
            client.stop_monitoring()

            # Display final status
            print("\n" + "=" * 50)
            print("Final Battery Status:")
            print("=" * 50)

            status = client.get_battery_status()
            if status:
                print(f"Overall SOC: {status.overall_soc}%")
                print(f"Total batteries: {status.total_batteries}")
                print()

                for battery in status.all_batteries:
                    if battery.is_available:
                        print(f"{battery.name:12} : {battery.soc:3}%", end="")

                        if battery.bms_min_limit is not None:
                            print(f"  (BMS limits: {battery.bms_min_limit}-{battery.bms_max_limit}%)", end="")

                        print()
            else:
                print("No status data available")

            print("\n✓ Monitoring complete")

    except Exception as e:
        print(f"\n✗ Error: {e}")
        return 1

    return 0


if __name__ == "__main__":
    exit(main())
