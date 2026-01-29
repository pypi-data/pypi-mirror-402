# psj-lib

[![PyPI version](https://img.shields.io/pypi/v/psj-lib)](https://pypi.org/project/psj-lib/)
[![Python Version](https://img.shields.io/pypi/pyversions/psj-lib)](https://www.python.org/downloads/)
[![Docs](https://img.shields.io/badge/docs-online-success)](https://piezosystemjena.github.io/psj-lib/)

A comprehensive Python library for controlling piezoelectric amplifiers and control devices manufactured by [piezosystem jena GmbH](https://www.piezosystem.com).

## ✨ Features

- **Asynchronous Architecture** - Built on Python's `asyncio` for efficient, non-blocking device communication
- **Multi-Device Support** - Extensible framework supporting multiple device families (currently d-Drive and 30DV50/300)
- **Comprehensive Capabilities** - Full access to position control, PID tuning, waveform generation, data recording, and filtering
- **Multiple Transport Protocols** - Connect via Serial (USB) or Telnet (Ethernet)
- **Type-Safe API** - Complete type hints for excellent IDE autocomplete and type checking
- **Extensive Documentation** - Comprehensive docstrings, examples, and developer guides

## 🔧 Supported Devices

### d-Drive Modular Amplifier

The d-Drive series represents piezosystem jena's modular piezo amplifier family:

- **High Resolution**: 20-bit DAC/ADC for precision control
- **Fast Sampling**: 50 kHz (20 µs period) for responsive control
- **Modular Design**: 1-6 channel configurations in compact enclosure
- **Advanced Control**: Integrated PID controller with configurable filters
- **Waveform Generation**: Built-in function generator with scan modes
- **Data Acquisition**: 2-channel recorder with 500,000 samples per channel
- **Hardware Triggers**: Precise timing and synchronization

**Note**: For NV200 please use the [nv200-python-lib](https://github.com/piezosystemjena/nv200-python-lib).

### PSJ 30DV50/300 (Standalone Amplifier)

The **PSJ 30DV50/300** is a single-channel, d-Drive-compatible amplifier:

- **Single Channel**: Standalone unit with one channel (ID 0)
- **d-Drive Compatible**: Uses the same command set and capabilities
- **Full Feature Set**: PID control, waveform generation, data recorder, filters

## 📦 Installation

```bash
pip install psj-lib
```

### Requirements

- Python 3.12 or higher
- Windows 10/11, Linux, or macOS 10.15+

## 🚀 Quick Start

### Basic Position Control

```python
import asyncio
from psj_lib import DDriveDevice, TransportType

async def main():
    # Connect to device
    device = DDriveDevice(TransportType.SERIAL, "COM3")
    
    async with device:
        # Get first channel
        channel = device.channels[0]
        
        # Enable closed-loop control
        await channel.closed_loop_controller.set(True)
        
        # Move to target position
        await channel.setpoint.set(50.0)
        
        # Read actual position
        position = await channel.position.get()
        print(f"Position: {position:.2f} µm")

if __name__ == "__main__":
    asyncio.run(main())
```

### Device Discovery

```python
from psj_lib import PiezoDevice, DiscoverFlags

# Discover all devices on Serial and Telnet
devices = await PiezoDevice.discover_devices(
    flags=DiscoverFlags.ALL_INTERFACES
)

for device in devices:
    info = device.device_info
    print(f"Found: {info.device_id} on {info.transport_info.identifier}")
```

### PID Control Configuration

```python
# Configure PID parameters for closed-loop control
await channel.pid_controller.set(
    p=10.0,      # Proportional gain
    i=5.0,       # Integral gain
    d=0.5,       # Derivative gain
    diff_filter=100.0  # Derivative filter
)

# Enable notch filter to suppress resonance
await channel.notch.set(
    enabled=True,
    frequency=500.0,
    bandwidth=50.0
)
```

### Waveform Generation

```python
from psj_lib import DDriveWaveformType

# Generate 10 Hz sine wave for scanning
await channel.waveform_generator.sine.set(
    amplitude=20.0,
    offset=50.0,
    frequency=10.0
)
await channel.waveform_generator.set_waveform_type(DDriveWaveformType.SINE)
```

### Data Recording

```python
from psj_lib import DDriveDataRecorderChannel

# Configure data recorder for 1 second capture at 50 kHz
await channel.data_recorder.set(
    memory_length=50000,  # 50k samples
    stride=1              # No decimation
)

# Start recording
await channel.data_recorder.start()

# ... perform motion ...

# Retrieve data
position_data = await channel.data_recorder.get_all_data(
    DDriveDataRecorderChannel.POSITION
)
voltage_data = await channel.data_recorder.get_all_data(
    DDriveDataRecorderChannel.VOLTAGE
)
```

## 📖 Documentation

Full documentation is available at: [GitHub Repository](https://github.com/piezosystemjena/psj-lib)

- **Getting Started** - Tutorials and basic usage
- **API Reference** - Complete API documentation
- **Device Documentation** - Device-specific guides (d-Drive)
- **Base Capabilities** - Common capabilities across all devices
- **Examples** - Practical usage examples
- **Developer Guide** - Extending the library

## 💡 Examples

Check out the [examples directory](https://github.com/piezosystemjena/psj-lib/tree/main/examples) for more practical examples:

1. Device Discovery and Connection
2. Simple Position Control
3. PID Configuration
4. Data Recorder Capture
5. Waveform Generation Basics
6. Filter Configuration
7. Backup and Restore Configuration

## 🏗️ Architecture

psj-lib uses a three-layer hierarchical architecture:

```
PiezoDevice (e.g., DDriveDevice)
  ├─ Transport protocol (Serial/Telnet) with command caching
  └─ PiezoChannels (e.g., DDriveChannel)
      └─ Capabilities (Position, PID, WaveformGenerator, etc.)
```

### Key Design Patterns

- **Capability-Based Architecture**: Features are modular `PiezoCapability` subclasses
- **Async/Await**: All I/O operations use Python's asyncio
- **Command Caching**: Reduces latency for frequently read values
- **Type Safety**: Full type hints for IDE support and type checking

## 🤝 Contributing

Contributions are welcome! Please visit the [GitHub repository](https://github.com/piezosystemjena/psj-lib) for more information.

## 💬 Support

- **Documentation**: [GitHub Pages](https://piezosystemjena.github.io/psj-lib)
- **Issues**: [GitHub Issues](https://github.com/piezosystemjena/psj-lib/issues)
- **Website**: [piezosystem jena GmbH](https://www.piezosystem.com)

## 📄 License

See LICENSE file in the [GitHub repository](https://github.com/piezosystemjena/psj-lib).

---

Made with ❤️ by [piezosystem jena GmbH](https://www.piezosystem.com)