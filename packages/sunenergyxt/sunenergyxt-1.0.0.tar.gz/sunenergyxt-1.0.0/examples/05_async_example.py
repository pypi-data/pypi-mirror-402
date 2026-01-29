#!/usr/bin/env python3
"""
Asynchronous client example.

This example shows how to:
- Use the async client
- Monitor multiple devices concurrently
- Handle async operations
"""

import asyncio
from sunenergyxt import AsyncSunEnergyXTClient
from sunenergyxt.exceptions import SunEnergyXTError


async def control_device(host: str):
    """Control a single device asynchronously."""
    print(f"[{host}] Connecting...")

    try:
        async with AsyncSunEnergyXTClient(host) as client:
            print(f"[{host}] Connected!")

            # Enable home appliance mode
            await client.enable_home_appliance_mode()
            print(f"[{host}] Home appliance mode enabled")

            # Set charging limits
            await client.set_max_charge_soc(90)
            await client.set_min_discharge_soc(10)
            print(f"[{host}] Charging limits configured")

            # Set charging power
            await client.set_charging_power(2000)
            print(f"[{host}] Charging power set to 2000W")

            # Get status
            status = client.get_battery_status()
            if status:
                print(f"[{host}] Battery: {status.overall_soc}%")
            else:
                print(f"[{host}] No status available")

            print(f"[{host}] ✓ Complete")

    except SunEnergyXTError as e:
        print(f"[{host}] ✗ Error: {e}")


async def monitor_device(host: str, duration: int = 10):
    """Monitor a device asynchronously."""
    print(f"[{host}] Starting monitoring for {duration}s...")

    async def on_data(data):
        soc = data.get("t211")
        if soc:
            print(f"[{host}] SOC: {soc}%")

    try:
        async with AsyncSunEnergyXTClient(host) as client:
            await client.start_monitoring(callback=on_data)

            # Monitor for duration
            await asyncio.sleep(duration)

            await client.stop_monitoring()
            print(f"[{host}] Monitoring complete")

    except SunEnergyXTError as e:
        print(f"[{host}] Error: {e}")


async def main():
    # Example 1: Control single device
    print("Example 1: Controlling single device")
    print("=" * 60)
    await control_device("192.168.1.100")

    print("\n" + "=" * 60)
    print()

    # Example 2: Control multiple devices concurrently
    print("Example 2: Controlling multiple devices concurrently")
    print("=" * 60)

    devices = [
        "192.168.1.100",
        # "192.168.1.101",  # Add more devices here
    ]

    # Control all devices concurrently
    tasks = [control_device(device) for device in devices]
    await asyncio.gather(*tasks)

    print("\n" + "=" * 60)
    print()

    # Example 3: Monitor device
    print("Example 3: Async monitoring")
    print("=" * 60)
    await monitor_device("192.168.1.100", duration=10)

    print("\n✓ All examples complete")


if __name__ == "__main__":
    asyncio.run(main())
