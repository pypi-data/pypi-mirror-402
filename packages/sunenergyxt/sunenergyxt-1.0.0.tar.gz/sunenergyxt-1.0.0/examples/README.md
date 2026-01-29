# SunEnergyXT Python API Examples

This directory contains example scripts demonstrating various features of the SunEnergyXT Python API.

## Examples

### 01_basic_usage.py
Basic usage example showing how to:
- Connect to a device
- Enable/disable operating modes
- Set charging parameters
- Get battery status

```bash
python 01_basic_usage.py
```

### 02_device_discovery.py
Device discovery example showing how to:
- Discover SunEnergyXT devices on the network using mDNS
- Display device information
- Connect to discovered devices

```bash
python 02_device_discovery.py
```

### 03_monitoring.py
Real-time monitoring example showing how to:
- Monitor device status updates
- Use callbacks for status changes
- Display battery information continuously

```bash
python 03_monitoring.py
```

### 04_charging_profile.py
Charging profile example showing how to:
- Create predefined charging profiles
- Apply profiles to devices
- Switch between different configurations

```bash
python 04_charging_profile.py
```

### 05_async_example.py
Asynchronous client example showing how to:
- Use the async client
- Control multiple devices concurrently
- Monitor devices asynchronously

```bash
python 05_async_example.py
```

### 06_test_response_time.py
Response time testing example showing how to:
- Test device response times
- Measure command execution latency
- Verify connection performance

```bash
python 06_test_response_time.py
```

### 07_all_data_dict.py
Complete data output example showing how to:
- Get all battery data as a dictionary
- Print formatted JSON with all 26+ fields
- Access system configuration, modes, and battery modules

```bash
python 07_all_data_dict.py
```

### 08_all_data_json.py
Single-line JSON output example (simplest method):
- Get ALL device data with a single method call
- Returns formatted JSON string ready for printing/logging/APIs
- Easiest way to access complete device status

```bash
python 08_all_data_json.py
```

## Configuration

Before running the examples, update the `DEVICE_IP` variable in each script with your device's IP address:

```python
DEVICE_IP = "192.168.1.100"  # Replace with your device IP
```

You can find your device IP using the discovery example or by checking your router's DHCP table.

## Requirements

All examples require the sunenergyxt package to be installed:

```bash
# From source (for development)
pip install -e ..

# Or from PyPI
pip install sunenergyxt
```

## Tips

- Run the discovery example first to find your device
- Use monitoring example to understand device behavior
- Test profile changes carefully
- Monitor battery status when making configuration changes

## Troubleshooting

If examples fail to connect:
1. Verify device IP address
2. Check network connectivity
3. Ensure device is powered on
4. Check firewall settings
5. Try increasing timeout in client initialization
