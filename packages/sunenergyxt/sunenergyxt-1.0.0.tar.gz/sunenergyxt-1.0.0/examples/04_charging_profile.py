#!/usr/bin/env python3
"""
Charging profile example.

This example shows how to:
- Create a charging profile
- Apply it to the device
- Define different profiles for different scenarios
"""

from sunenergyxt import SunEnergyXTClient, ChargingProfile
from sunenergyxt.exceptions import SunEnergyXTError


# Define different charging profiles
PROFILES = {
    "balanced": ChargingProfile(
        min_discharge_soc=10,
        max_charge_soc=90,
        charging_power=2500,
        home_appliance_min_soc=10,
        ev_charging_min_soc=20,
        charging_max_soc=95,
        no_io_shutdown_timeout=60,
        dod_shutdown_timeout=30
    ),
    "battery_saver": ChargingProfile(
        min_discharge_soc=20,
        max_charge_soc=80,
        charging_power=1500,
        home_appliance_min_soc=20,
        ev_charging_min_soc=25,
        charging_max_soc=85,
        no_io_shutdown_timeout=30,
        dod_shutdown_timeout=15
    ),
    "max_performance": ChargingProfile(
        min_discharge_soc=5,
        max_charge_soc=100,
        charging_power=3600,
        home_appliance_min_soc=5,
        ev_charging_min_soc=10,
        charging_max_soc=100,
        no_io_shutdown_timeout=120,
        dod_shutdown_timeout=60
    ),
}


def display_profile(name: str, profile: ChargingProfile):
    """Display profile information."""
    print(f"\n{name.upper()} Profile:")
    print(f"  Discharge Range:     {profile.min_discharge_soc}% - {profile.max_charge_soc}%")
    print(f"  Charging Power:      {profile.charging_power}W")
    print(f"  Home Appliance Min:  {profile.home_appliance_min_soc}%")
    print(f"  EV Charging Min:     {profile.ev_charging_min_soc}%")
    print(f"  Charging Max:        {profile.charging_max_soc}%")
    print(f"  No I/O Timeout:      {profile.no_io_shutdown_timeout} min")
    print(f"  DOD Timeout:         {profile.dod_shutdown_timeout} min")


def main():
    # Replace with your device IP
    DEVICE_IP = "192.168.1.100"

    print("SunEnergyXT Charging Profile Manager")
    print("=" * 60)

    # Display available profiles
    print("\nAvailable Profiles:")
    for name, profile in PROFILES.items():
        display_profile(name, profile)

    # Select profile
    print("\n" + "=" * 60)
    profile_name = input("Enter profile name to apply (balanced/battery_saver/max_performance): ").strip().lower()

    if profile_name not in PROFILES:
        print(f"Invalid profile: {profile_name}")
        return 1

    selected_profile = PROFILES[profile_name]

    print(f"\nApplying {profile_name} profile to device...")

    try:
        with SunEnergyXTClient(DEVICE_IP) as client:
            print("✓ Connected to device")

            # Apply profile
            client.apply_charging_profile(selected_profile)
            print(f"✓ {profile_name.capitalize()} profile applied successfully!")

            # Verify settings (if monitoring available)
            print("\nProfile active. Monitor your device to verify changes.")

    except SunEnergyXTError as e:
        print(f"\n✗ Error applying profile: {e}")
        return 1

    return 0


if __name__ == "__main__":
    exit(main())
