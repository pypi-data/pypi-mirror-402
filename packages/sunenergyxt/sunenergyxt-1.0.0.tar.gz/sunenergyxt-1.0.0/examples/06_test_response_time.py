#!/usr/bin/env python3
"""
Response time test for set_max_charge_soc(90) command.

Simple script to measure the latency of setting the max charge SOC to 90%.
"""

import time
import statistics
from sunenergyxt import SunEnergyXTClient
from sunenergyxt.exceptions import SunEnergyXTError


# Configuration
DEVICE_IP = "192.168.178.137"  # Change this to your device IP
TARGET_SOC = 90
ITERATIONS = 1


def main():
    print(f"Testing set_max_charge_soc({TARGET_SOC}) response time")
    print(f"Device: {DEVICE_IP}")
    print(f"Iterations: {ITERATIONS}")
    print("=" * 60)

    latencies = []

    try:
        with SunEnergyXTClient(DEVICE_IP, timeout=5.0) as client:
            print("✓ Connected to device\n")

            for i in range(ITERATIONS):
                print(f"Test {i+1}/{ITERATIONS}... ", end="", flush=True)

                # Measure command latency
                start_time = time.perf_counter()
                success = client.set_max_charge_soc(TARGET_SOC)
                end_time = time.perf_counter()

                latency_ms = (end_time - start_time) * 1000

                if success:
                    latencies.append(latency_ms)
                    print(f"✓ {latency_ms:.2f}ms")
                else:
                    print(f"✗ Failed")

                # Small delay between tests
                if i < ITERATIONS - 1:
                    time.sleep(3)

            # Print statistics
            print("\n" + "=" * 60)
            print("RESPONSE TIME STATISTICS")
            print("=" * 60)
            print(f"Command:         set_max_charge_soc({TARGET_SOC})")
            print(f"Total tests:     {len(latencies)}/{ITERATIONS}")
            print(f"Successful:      {len(latencies)}")
            print(f"Failed:          {ITERATIONS - len(latencies)}")

            if latencies:
                print(f"\nAverage latency: {statistics.mean(latencies):.2f}ms")
                print(f"Minimum latency: {min(latencies):.2f}ms")
                print(f"Maximum latency: {max(latencies):.2f}ms")
                print(f"Median latency:  {statistics.median(latencies):.2f}ms")

                if len(latencies) > 1:
                    print(f"Std deviation:   {statistics.stdev(latencies):.2f}ms")

                # Performance rating
                avg = statistics.mean(latencies)
                print(f"\nPerformance rating: ", end="")
                if avg < 50:
                    print("⚡ Excellent (< 50ms)")
                elif avg < 100:
                    print("✓ Good (50-100ms)")
                elif avg < 200:
                    print("○ Average (100-200ms)")
                else:
                    print("⚠ Slow (> 200ms)")
            else:
                print("\n✗ No successful tests")

            print("=" * 60)

    except SunEnergyXTError as e:
        print(f"\n✗ Error: {e}")
        return 1

    return 0


if __name__ == "__main__":
    exit(main())
