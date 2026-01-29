# Adding New Piezo Amplifier Devices to psj-lib

This guide walks you through the process of adding support for a new Piezosystem Jena piezo amplifier to the psj-lib library. We'll use the d-Drive implementation as a reference example.

## Table of Contents

- [Overview](#overview)
- [Prerequisites](#prerequisites)
- [Project Structure](#project-structure)
- [Step-by-Step Implementation](#step-by-step-implementation)
  - [Step 1: Create Device Directory Structure](#step-1-create-device-directory-structure)
  - [Step 2: Implement Device-Specific Capabilities](#step-2-implement-device-specific-capabilities)
  - [Step 3: Implement the Channel Class](#step-3-implement-the-channel-class)
  - [Step 4: Implement the Device Class](#step-4-implement-the-device-class)
  - [Step 5: Export Public API](#step-5-export-public-api)
  - [Step 6: Testing](#step-6-testing)
- [Best Practices](#best-practices)
- [Common Patterns](#common-patterns)
- [Troubleshooting](#troubleshooting)

---

## Overview

The psj-lib library uses an object-oriented architecture with the following hierarchy:

```
PiezoDevice (base)
    ├─ Handles transport communication (serial/Telnet)
    ├─ Manages command caching and locking
    └─ Contains one or more PiezoChannels

PiezoChannel (base)
    ├─ Represents a single amplifier channel
    └─ Exposes capabilities via CapabilityDescriptors

PiezoCapability (base)
    └─ Individual feature (setpoint, position, PID, waveform generator, etc.)
```

When adding a new device:
1. **Extend base capabilities** if the device has unique features
2. **Create a device-specific channel class** with CapabilityDescriptors
3. **Create a device class** that discovers and initializes channels
4. **Register the device** via DEVICE_ID for automatic discovery

---

## Prerequisites

Before implementing a new device, you should have:

1. **Device documentation**: Command reference, protocol specifications, hardware manual
2. **Physical device**: For testing the implementation
3. **Communication details**: Serial port settings, Telnet port, command format
4. **Understanding of device features**: Capabilities, channel count, special features

---

## Project Structure

Create a new directory under `psj_lib/devices/` for your device:

```
psj_lib/devices/
├── base/                           # Base classes (DO NOT MODIFY)
├── transport_protocol/             # Transport layer (DO NOT MODIFY)
├── d_drive/                        # Example reference implementation
│   ├── __init__.py                # Public API exports
│   ├── d_drive_device.py          # Device class
│   ├── d_drive_channel.py         # Channel class
│   └── capabilities/              # Device-specific capabilities
│       ├── d_drive_status_register.py
│       ├── d_drive_waveform_generator.py
│       └── ...
└── your_device/                    # Your new device
    ├── __init__.py
    ├── your_device_device.py
    ├── your_device_channel.py
    └── capabilities/
        └── ...
```

---

## Step-by-Step Implementation

### Step 1: Create Device Directory Structure

Create the basic directory structure for your device:

```bash
mkdir -p psj_lib/devices/your_device/capabilities
touch psj_lib/devices/your_device/__init__.py
touch psj_lib/devices/your_device/your_device_device.py
touch psj_lib/devices/your_device/your_device_channel.py
```

### Step 2: Implement Device-Specific Capabilities

If your device extends or modifies standard capabilities, create device-specific implementations. 

If your device supports capabilties currently not defined by the base classes and they might be used by other devices as well, think about making your new capability a base class and add them to the ``base/capabilities`` directory.

#### Example: Custom Status Register

Many devices have hardware status registers with device-specific bit layouts.

**File: `your_device/capabilities/your_device_status_register.py`**

```python
from enum import Enum
from ...base.capabilities import StatusRegister
from ...base.piezo_types import SensorType


class YourDeviceOperationMode(Enum):
    """Device-specific operation modes."""
    OPEN_LOOP = 0
    CLOSED_LOOP = 1
    TRACKING = 2


class YourDeviceStatusRegister(StatusRegister):
    """Hardware status register for YourDevice amplifier.
    
    Decodes the device's status word into individual properties.
    Each property extracts specific bits from the raw status value.
    """

    @property
    def actuator_connected(self) -> bool:
        """Check if actuator is connected (bit 0)."""
        val = int(self._raw[0])
        return bool(val & 0x0001)

    @property
    def sensor_type(self) -> SensorType:
        """Position sensor type (bits 1-2)."""
        val = int(self._raw[0])
        return SensorType((val & 0x0006) >> 1)

    @property
    def operation_mode(self) -> YourDeviceOperationMode:
        """Current operation mode (bits 4-5)."""
        val = int(self._raw[0])
        mode_bits = (val & 0x0030) >> 4
        return YourDeviceOperationMode(mode_bits)

    @property
    def error_state(self) -> bool:
        """Error condition present (bit 7)."""
        val = int(self._raw[0])
        return bool(val & 0x0080)
```

**Key Points:**
- Extend `StatusRegister` from base capabilities
- Use bit masking to extract individual flags
- Document bit positions in docstrings
- Return typed values (bool, Enum, int)

#### Example: Device-Specific Enum

If your device has specific options for capabilities (e.g., monitor output sources):

**File: `your_device/capabilities/your_device_monitor_output.py`**

```python
from ...base.capabilities import MonitorOutputSource


class YourDeviceMonitorOutputSource(MonitorOutputSource):
    """Available analog monitor output sources.
    
    These values are passed to the monitor output capability
    to select which internal signal is routed to the analog output.
    """
    POSITION = 0
    SETPOINT = 1
    ERROR_SIGNAL = 2
    CONTROLLER_OUTPUT = 3
    SENSOR_RAW = 4
```

#### Example: Extended Capability

If your device adds features beyond the base implementation:

**File: `your_device/capabilities/your_device_waveform_generator.py`**

```python
from enum import Enum
from ...base.capabilities import PiezoCapability


class YourDeviceWaveformType(Enum):
    """Supported waveform types."""
    OFF = 0
    SINE = 1
    TRIANGLE = 2
    SQUARE = 3
    CUSTOM = 4  # Device-specific feature


class YourDeviceWaveformGenerator(PiezoCapability):
    """Waveform generator with custom waveform support.
    
    Extends standard waveform generation with device-specific
    custom waveform loading capability.
    """
    
    CMD_WFG_TYPE = "WFG_TYPE"
    CMD_WFG_AMPLITUDE = "WFG_AMPLITUDE"
    CMD_WFG_FREQUENCY = "WFG_FREQUENCY"
    CMD_CUSTOM_WAVEFORM_DATA = "CUSTOM_WFG_DATA"  # Device-specific

    async def set_waveform_type(self, waveform_type: YourDeviceWaveformType) -> None:
        """Activate specific waveform type."""
        await self._write(self.CMD_WFG_TYPE, [waveform_type.value])

    async def get_waveform_type(self) -> YourDeviceWaveformType:
        """Get currently active waveform type."""
        result = await self._write(self.CMD_WFG_TYPE)
        return YourDeviceWaveformType(int(result[0]))

    async def load_custom_waveform(self, data: list[float]) -> None:
        """Load custom waveform data (device-specific feature).
        
        Args:
            data: List of normalized waveform samples (-1.0 to +1.0)
        
        Example:
            >>> import numpy as np
            >>> # Create custom waveform
            >>> samples = np.sin(np.linspace(0, 4*np.pi, 256))
            >>> await wfg.load_custom_waveform(samples.tolist())
            >>> await wfg.set_waveform_type(YourDeviceWaveformType.CUSTOM)
        """
        if len(data) > 1024:
            raise ValueError("Waveform data limited to 1024 samples")
        
        # Send data in chunks if needed
        chunk_size = 64
        for i in range(0, len(data), chunk_size):
            chunk = data[i:i + chunk_size]
            await self._write(self.CMD_CUSTOM_WAVEFORM_DATA, chunk)
```

### Step 3: Implement the Channel Class

The channel class represents a single amplifier channel and exposes its capabilities via `CapabilityDescriptor` properties.

**File: `your_device/your_device_channel.py`**

```python
"""YourDevice amplifier channel implementation."""

from ..base.capabilities import (
    ActuatorDescription,
    CapabilityDescriptor,
    ClosedLoopController,
    DataRecorder,
    PIDController,
    Position,
    Setpoint,
    SlewRate,
    Status,
    Temperature,
)
from ..base.piezo_channel import PiezoChannel
from .capabilities.your_device_status_register import YourDeviceStatusRegister
from .capabilities.your_device_monitor_output import YourDeviceMonitorOutputSource
from .capabilities.your_device_waveform_generator import (
    YourDeviceWaveformGenerator,
    YourDeviceWaveformType,
)


class YourDeviceChannel(PiezoChannel):
    """Amplifier channel for YourDevice system.
    
    Represents a single channel with all control capabilities including
    position control, PID tuning, waveform generation, and data recording.
    
    Hardware specifications:
    - Resolution: 16-bit (or whatever your device has)
    - Sample rate: 20 kHz (50µs control loop period)
    
    Key capabilities accessible as properties:
    - status_register: Hardware status with bit-mapped flags
    - setpoint: Target position control
    - position: Actual position readback
    - closed_loop_controller: Enable/disable feedback control
    - pid_controller: PID parameter configuration
    - waveform_generator: Built-in waveform generation
    - data_recorder: Signal recording
    
    Example:
        >>> channel = device.channels[0]
        >>> # Enable closed-loop and move to position
        >>> await channel.closed_loop_controller.set(True)
        >>> await channel.setpoint.set(50.0)
        >>> # Read actual position
        >>> pos = await channel.position.get()
        >>> print(f"Position: {pos:.2f} µm")
    """

    SAMPLE_PERIOD: int = 50  # Control loop period in microseconds
    """Control loop sample period in microseconds (20 kHz for YourDevice)."""

    BACKUP_COMMANDS: set[str] = {
        "set",
        "cl",
        "kp",
        "ki",
        "kd",
        "sr",
        "wfg_type",
        # Add all commands that should be backed up
    }
    """Per channel commands to include in backup operations."""

    # ========================================================================
    # Capability Descriptors
    # ========================================================================
    # Each descriptor maps a capability to its device commands
    
    status_register: Status = CapabilityDescriptor(
        Status,
        {
            Status.CMD_STATUS: "stat"  # Replace with your device's command
        },
        register_type=YourDeviceStatusRegister  # Your custom status register class
    )
    """Hardware status register with device state information."""

    actuator_description: ActuatorDescription = CapabilityDescriptor(
        ActuatorDescription,
        {
            ActuatorDescription.CMD_DESCRIPTION: "acdescr"
        }
    )
    """Actuator identification string."""

    setpoint: Setpoint = CapabilityDescriptor(
        Setpoint,
        {
            Setpoint.CMD_SETPOINT: "set"
        }
    )
    """Target position control (commanded position)."""

    position: Position = CapabilityDescriptor(
        Position,
        {
            Position.CMD_POSITION: "pos"  # Your device's position read command
        }
    )
    """Actual position readback from sensor."""

    temperature: Temperature = CapabilityDescriptor(
        Temperature,
        {
            Temperature.CMD_TEMPERATURE: "temp"
        }
    )
    """Channel electronics temperature."""

    closed_loop_controller: ClosedLoopController = CapabilityDescriptor(
        ClosedLoopController,
        {
            ClosedLoopController.CMD_ENABLE: "cl"
        },
        sample_period=SAMPLE_PERIOD
    )
    """Closed-loop position control enable/disable."""

    slew_rate: SlewRate = CapabilityDescriptor(
        SlewRate,
        {
            SlewRate.CMD_RATE: "sr"
        }
    )
    """Maximum rate of change limiting."""

    pid_controller: PIDController = CapabilityDescriptor(
        PIDController,
        {
            PIDController.CMD_P: "kp",
            PIDController.CMD_I: "ki",
            PIDController.CMD_D: "kd",
            PIDController.CMD_TF: "tf",
        }
    )
    """PID controller parameter configuration."""

    waveform_generator: YourDeviceWaveformGenerator = CapabilityDescriptor(
        YourDeviceWaveformGenerator,  # Your custom implementation
        {
            YourDeviceWaveformGenerator.CMD_WFG_TYPE: "wfg_type",
            YourDeviceWaveformGenerator.CMD_WFG_AMPLITUDE: "wfg_amp",
            YourDeviceWaveformGenerator.CMD_WFG_FREQUENCY: "wfg_freq",
            YourDeviceWaveformGenerator.CMD_CUSTOM_WAVEFORM_DATA: "wfg_data",
        }
    )
    """Multi-waveform generator with custom waveform support."""

    data_recorder: DataRecorder = CapabilityDescriptor(
        DataRecorder,
        {
            DataRecorder.CMD_START_RECORDING: "rec_start",
            DataRecorder.CMD_STRIDE: "rec_stride",
            DataRecorder.CMD_MEMORY_LENGTH: "rec_len",
            DataRecorder.CMD_PTR: "rec_ptr",
            DataRecorder.CMD_GET_DATA_1: "rec_ch1",
            DataRecorder.CMD_GET_DATA_2: "rec_ch2",
        },
        sample_period=SAMPLE_PERIOD  # Pass sample period for time calculations
    )
    """Two-channel data recorder for signal capture."""

    # Add more capabilities as needed for your device
```

**Key Points:**
- Inherit from `PiezoChannel`
- Define `SAMPLE_PERIOD` for your device's control loop rate
- Define `BACKUP_COMMANDS` with commands to save/restore
- Each capability gets a `CapabilityDescriptor` that maps:
  - Capability class (base or custom)
  - Command dictionary (maps capability constants to device commands)
  - Optional additional parameters (types for status registers, sample period, etc.)
- Add comprehensive docstrings for IDE autocomplete

### Step 4: Implement the Device Class

The device class manages the overall device, discovers channels, and handles device-level operations.

**File: `your_device/your_device_device.py`**

```python
"""YourDevice piezo amplifier device implementation."""

from ..base.piezo_device import PiezoDevice
from ..transport_protocol import TransportProtocol
from .your_device_channel import YourDeviceChannel


class YourDeviceDevice(PiezoDevice):
    """YourDevice piezo amplifier system.
    
    Represents a complete YourDevice system with 1-4 amplifier channels.
    Each channel provides independent control of a piezoelectric actuator.
    
    Hardware features:
    - 16-bit resolution
    - 20 kHz sampling rate (50µs control loop period)
    - Digital PID controllers
    - Integrated waveform generator
    - Two-channel data recorder
    - RS-232/USB connectivity
    
    Example:
        >>> from psj_lib import YourDeviceDevice, TransportType
        >>> # Connect via serial port
        >>> device = YourDeviceDevice(TransportType.SERIAL, 'COM3')
        >>> await device.connect()
        >>> print(f"Found {len(device.channels)} channels")
        >>> 
        >>> # Access first channel
        >>> channel = device.channels[0]
        >>> await channel.closed_loop_controller.set(True)
        >>> await channel.setpoint.set(75.0)
    
    Note:
        - Channels are numbered 0-3 (or whatever your device supports)
        - Use device.channels dict to access available channels
    """

    DEVICE_ID = "YourDevice"  # CRITICAL: Unique identifier for device discovery
    """Device type identifier used for device discovery and type checking."""

    BACKUP_COMMANDS = set()
    """Global device commands to include in backup operations."""
    
    CACHEABLE_COMMANDS = {
        "acdescr",
        "set",
        "cl",
        "kp",
        "ki",
        "kd",
        "sr",
        "wfg_type",
        "wfg_amp",
        "wfg_freq",
        # Add all commands whose responses don't change frequently
    }
    """Commands whose responses can be cached for performance optimization."""

    @classmethod
    async def _is_device_type(cls, tp: TransportProtocol) -> str | None:
        """Check if connected device is a YourDevice amplifier.
        
        Sends a probe command and checks the response for device identification.
        This is used during device discovery to identify YourDevice systems.

        Args:
            tp: Transport protocol instance connected to device

        Returns:
            Device ID string if device responds as YourDevice, None otherwise
        
        Example response format:
            "YourDevice V2.0 S/N:12345"
        """
        try:
            # Send identification query command (adjust for your device)
            response = await tp.write("version", None)
            
            # Check if response contains your device identifier
            if response and len(response) > 0:
                device_string = response[0].upper()
                # Adjust this check for your device's response
                if "YOURDEVICE" in device_string:
                    return cls.DEVICE_ID
                
        except Exception:
            pass
        
        return None
        
    async def _discover_channels(self) -> None:
        """Discover and initialize all available amplifier channels.
        
        Queries the device to determine how many channels are present
        and creates YourDeviceChannel instances for each.
        
        Note:
            This is called automatically during device connection.
        """
        self._channels = {}
        
        # Method 1: If device has a command to query channel count
        try:
            response = await self.write("numch", None)  # Adjust command
            num_channels = int(response[0])
        except Exception:
            # Method 2: Probe each potential channel
            num_channels = 0
            for ch_id in range(4):  # Max possible channels
                try:
                    # Try to read something from the channel
                    await self.write(f"{ch_id}stat", None)
                    num_channels += 1
                except Exception:
                    break
        
        # Create channel objects
        for channel_id in range(num_channels):
            self._channels[channel_id] = YourDeviceChannel(
                device=self,
                channel_number=channel_id
            )

    async def some_device_level_method(self) -> str:
        """Example of a device-level method (not channel-specific).
        
        If your device has global settings or commands that don't
        belong to a specific channel, implement them here.
        """
        return
```

**Key Points:**
- Inherit from `PiezoDevice`
- **CRITICAL**: Set `DEVICE_ID` to a unique string - this enables automatic discovery
- Define `CACHEABLE_COMMANDS` for performance (read-heavy operations)
- Implement `_is_device_type()` to identify your device during discovery
- Implement `_discover_channels()` to find and initialize channels
- (Optional) Add device-level CapabilityDescriptors (same syntax as channels)
- (Optional) Add device-level methods

### Step 5: Export Public API

Make your device classes easily importable by users.

**File: `your_device/__init__.py`**

```python
"""YourDevice piezo amplifier implementation.

This module provides complete support for YourDevice piezo amplifiers
including device discovery, channel control, and all capabilities.
"""

from .capabilities.your_device_status_register import (
    YourDeviceOperationMode,
    YourDeviceStatusRegister,
)
from .capabilities.your_device_monitor_output import YourDeviceMonitorOutputSource
from .capabilities.your_device_waveform_generator import (
    YourDeviceWaveformGenerator,
    YourDeviceWaveformType,
)
from .your_device_channel import YourDeviceChannel
from .your_device_device import YourDeviceDevice

__all__ = [
    # Main classes
    "YourDeviceDevice",
    "YourDeviceChannel",
    
    # Device-specific capabilities
    "YourDeviceStatusRegister",
    "YourDeviceOperationMode",
    "YourDeviceMonitorOutputSource",
    "YourDeviceWaveformGenerator",
    "YourDeviceWaveformType",
]
```

**Update the main package** (`psj_lib/__init__.py`) to expose your device:

```python
# Add to existing imports
from .devices.your_device import (
    YourDeviceDevice,
    YourDeviceChannel,
    YourDeviceWaveformType,
    # ... other exports
)

__all__ = [
    # ... existing exports ...
    "YourDeviceDevice",
    "YourDeviceChannel",
    "YourDeviceWaveformType",
]
```

### Step 6: Testing

Verify your implementation using a physical device.

**Manual testing checklist:**
- [ ] Device connects successfully
- [ ] All channels discovered correctly
- [ ] Status register reads correctly
- [ ] Position control works
- [ ] PID controller parameters can be set/read
- [ ] Waveform generator functions
- [ ] Data recorder captures data
- [ ] Device discovery finds your device
- [ ] Command caching improves performance
- [ ] Backup/restore preserves settings

---

## Best Practices

### 1. Error Handling

**Implement robust error handling in device-specific methods:**

```python
async def load_custom_waveform(self, data: list[float]) -> None:
    """Load custom waveform with validation."""
    # Validate input
    if not data:
        raise ValueError("Waveform data cannot be empty")
    
    if len(data) > self.MAX_WAVEFORM_SAMPLES:
        raise ValueError(
            f"Waveform data exceeds maximum length "
            f"({self.MAX_WAVEFORM_SAMPLES} samples)"
        )
    
    # Validate range
    if any(abs(x) > 1.0 for x in data):
        raise ValueError("Waveform samples must be in range [-1.0, 1.0]")
    
    # Send to device
    try:
        await self._write(self.CMD_CUSTOM_WAVEFORM_DATA, data)
    except Exception as e:
        raise RuntimeError(f"Failed to load waveform: {e}")
```

### 3. Documentation

**Write comprehensive docstrings for all public APIs:**

```python
async def complex_operation(self, param1: float, param2: int) -> dict:
    """Perform complex device operation.
    
    This method does X, Y, and Z with the provided parameters.
    It's useful for ABC use case.
    
    Args:
        param1: Description of param1. Valid range: 0.0 to 100.0
        param2: Description of param2. Valid values: 0-3
            0 = Mode A
            1 = Mode B
            2 = Mode C
            3 = Mode D
    
    Returns:
        Dictionary containing:
            'status': Operation status code (0=success)
            'result': Result value
            'timestamp': Operation timestamp
    
    Raises:
        ValueError: If parameters are out of range
        RuntimeError: If device is not in correct state
    
    Example:
        >>> result = await channel.complex_operation(50.0, 1)
        >>> print(f"Status: {result['status']}")
        >>> print(f"Result: {result['result']}")
    
    Note:
        - Device must be in closed-loop mode
        - Operation takes approximately 100ms
        - Temporary disables waveform generator
    """
    # Implementation
```

### 3. Type Hints

**Use type hints consistently:**

```python
async def get_position(self) -> float:
    """Get current position."""
    result = await self._write(self.CMD_POSITION)
    return float(result[0])

async def set_mode(self, mode: YourDeviceOperationMode) -> None:
    """Set operation mode."""
    await self._write(self.CMD_MODE, [mode.value])

def calculate_something(
    self,
    value: float,
    optional_param: int | None = None
) -> float | None:
    """Calculate something with optional parameter."""
    # Implementation
```

### 5. Constants

**Define constants for magic numbers:**

```python
class YourDeviceChannel(PiezoChannel):
    """Channel implementation."""
    
    # Hardware constants
    SAMPLE_PERIOD: int = 100  # µs
    MAX_POSITION: float = 200.0  # µm
    MIN_POSITION: float = 0.0  # µm
    MAX_VOLTAGE: float = 150.0  # V
    DEFAULT_PID_P: float = 10.0
    DEFAULT_PID_I: float = 5.0
    DEFAULT_PID_D: float = 1.0
    
    # Command timeouts
    STANDARD_TIMEOUT: float = 0.5  # seconds
    LONG_OPERATION_TIMEOUT: float = 5.0  # seconds
```

---

## Common Patterns

### Pattern 1: Bit-Mapped Status Register

Many devices have status registers where each bit represents a flag:

```python
class YourDeviceStatusRegister(StatusRegister):
    """Decode bit-mapped status register."""
    
    @property
    def some_flag(self) -> bool:
        """Extract bit 3."""
        val = int(self._raw[0])
        return bool(val & 0x0008)  # Bit 3 = 0x0008
    
    @property
    def multi_bit_value(self) -> int:
        """Extract bits 4-6 (3-bit value)."""
        val = int(self._raw[0])
        return (val & 0x0070) >> 4  # Mask bits 4-6, shift right
    
    @property
    def enum_from_bits(self) -> YourDeviceMode:
        """Extract bits 7-8 as enum."""
        val = int(self._raw[0])
        mode_bits = (val & 0x0180) >> 7
        return YourDeviceMode(mode_bits)
```

**Bit mask reference:**
```
Bit:  15 14 13 12 11 10  9  8  7  6  5  4  3  2  1  0
Hex:  -- -- -- -- -- -- -- -- 80 40 20 10 08 04 02 01
```

### Pattern 2: Enum-Based Configuration

For discrete options, use Enums:

```python
class FilterType(Enum):
    """Available filter types."""
    NONE = 0
    BUTTERWORTH = 1
    BESSEL = 2
    CHEBYSHEV = 3

async def set_filter(self, filter_type: FilterType, cutoff: float) -> None:
    """Configure filter with type and cutoff frequency."""
    await self._write(self.CMD_FILTER_TYPE, [filter_type.value])
    await self._write(self.CMD_FILTER_CUTOFF, [cutoff])

async def get_filter(self) -> tuple[FilterType, float]:
    """Get current filter configuration."""
    type_result = await self._write(self.CMD_FILTER_TYPE)
    cutoff_result = await self._write(self.CMD_FILTER_CUTOFF)
    return FilterType(int(type_result[0])), float(cutoff_result[0])
```

### Pattern 3: Multi-Parameter Configuration

When a feature needs multiple related parameters:

```python
async def configure_trigger(
    self,
    start: float,
    stop: float,
    interval: float,
    pulse_width: int,
    enabled: bool = True
) -> None:
    """Configure trigger output with all parameters.
    
    Args:
        start: Start position for trigger window (µm)
        stop: Stop position for trigger window (µm)
        interval: Spacing between triggers (µm)
        pulse_width: Pulse width in microseconds
        enabled: Enable trigger output after configuration
    
    Example:
        >>> # Trigger every 10µm from 20-80µm
        >>> await channel.configure_trigger(
        ...     start=20.0,
        ...     stop=80.0,
        ...     interval=10.0,
        ...     pulse_width=1000  # 1ms pulses
        ... )
    """
    await self._write(self.CMD_TRIG_START, [start])
    await self._write(self.CMD_TRIG_STOP, [stop])
    await self._write(self.CMD_TRIG_INTERVAL, [interval])
    await self._write(self.CMD_TRIG_WIDTH, [pulse_width])
    
    if enabled:
        await self._write(self.CMD_TRIG_ENABLE, [1])
```

### Pattern 4: Sub-Capability Organization

For complex capabilities with multiple sub-features:

```python
class YourDeviceWaveformGenerator(PiezoCapability):
    """Waveform generator with multiple waveform types."""
    
    def __init__(self, write_cb, device_commands) -> None:
        super().__init__(write_cb, device_commands)
        
        # Create sub-generators for each waveform type
        self._sine = SineWaveformConfig(
            self._write_cb,
            {
                'amplitude': self._device_commands[self.CMD_SINE_AMP],
                'frequency': self._device_commands[self.CMD_SINE_FREQ],
                'offset': self._device_commands[self.CMD_SINE_OFFSET],
            }
        )
        
        self._triangle = TriangleWaveformConfig(
            self._write_cb,
            {
                'amplitude': self._device_commands[self.CMD_TRI_AMP],
                'frequency': self._device_commands[self.CMD_TRI_FREQ],
                'duty_cycle': self._device_commands[self.CMD_TRI_DUTY],
            }
        )
    
    @property
    def sine(self) -> SineWaveformConfig:
        """Access sine waveform configuration."""
        return self._sine
    
    @property
    def triangle(self) -> TriangleWaveformConfig:
        """Access triangle waveform configuration."""
        return self._triangle
```

---

## Troubleshooting

### Issue: Device Not Discovered

**Problem:** `PiezoDevice.discover_devices()` doesn't find your device.

**Solutions:**
1. **Check DEVICE_ID is set:**
   ```python
   class YourDeviceDevice(PiezoDevice):
       DEVICE_ID = "YourDevice"  # Must be defined!
   ```

2. **Verify `_is_device_type()` works:**
   ```python
   @classmethod
   async def _is_device_type(cls, tp: TransportProtocol) -> str | None:
       try:
           response = await tp.write("*IDN?", None)
           print(f"Device response: {response}")  # Debug output
           if "YOURDEVICE" in response[0].upper():
               return cls.DEVICE_ID
           return None
       except Exception as e:
           print(f"Error: {e}")
           return None
   ```

3. **Check device is imported:**
   Make sure to import your device module so it registers:
   ```python
   # In psj_lib/__init__.py
   from .devices.your_device import YourDeviceDevice  # This triggers registration
   ```

### Issue: Commands Not Working

**Problem:** Commands sent to device don't have expected effect.

**Solutions:**
1. **Check command strings match device protocol:**
   ```python
   # Verify in device documentation
   setpoint: Setpoint = CapabilityDescriptor(
       Setpoint,
       {
           Setpoint.CMD_SETPOINT: "set"  # Ensure this is correct!
       }
   )
   ```

2. **Check frame delimiters:**
   ```python
   class YourDeviceDevice(PiezoDevice):
       # If your device uses different line endings
       FRAME_DELIMITER_WRITE = b'\n'  # LF instead of CRLF
       FRAME_DELIMITER_READ = b'\n'
   ```

3. **Test commands manually:**
   ```python
   device = YourDeviceDevice(TransportType.SERIAL, 'COM3')
   await device.connect()
   
   # Send raw command to test
   response = await device.write("set", [50.0])
   print(f"Response: {response}")
   ```

### Issue: Caching Problems

**Problem:** Cached values are stale or incorrect.

**Solutions:**
1. **Don't cache frequently changing values:**
   ```python
   CACHEABLE_COMMANDS = {
       "kp",  # PID P gain - rarely changes
       "ki",  # PID I gain - rarely changes
       # "pos",  # DON'T cache position - changes constantly!
       # "temp",  # DON'T cache temperature - changes over time
   }
   ```

2. **Disable caching if multiple apps access device:**
   ```python
   device = YourDeviceDevice(TransportType.SERIAL, 'COM3')
   await device.connect()
   device.enable_cmd_cache(False)  # Disable if other apps might modify device
   ```

3. **Clear cache after writes:**
   Cache is automatically cleared on writes to cacheable commands, but verify:
   ```python
   # Write invalidates cache automatically
   await device.write("kp", [15.0])  # Clears "kp" from cache
   value = await device.write("kp", None)  # Fresh read from device
   ```

---

## Additional Resources

- **Base Classes Documentation**: See docstrings in `psj_lib/devices/base/`
- **d-Drive Reference**: Complete implementation in `psj_lib/devices/d_drive/`
- **Capability Reference**: All base capabilities in `psj_lib/devices/base/capabilities/`
- **Transport Protocol**: Details in `psj_lib/devices/transport_protocol/`

---

## Summary Checklist

When adding a new device, ensure you:

- [ ] Created device directory structure under `psj_lib/devices/your_device/`
- [ ] Implemented device-specific capabilities (if needed) in `capabilities/` subdirectory
- [ ] Created channel class inheriting from `PiezoChannel`
  - [ ] Defined `BACKUP_COMMANDS`
  - [ ] Added all `CapabilityDescriptor` properties with correct command mappings
- [ ] Created device class inheriting from `PiezoDevice`
  - [ ] Set unique `DEVICE_ID`
  - [ ] Defined `CACHEABLE_COMMANDS`
  - [ ] Implemented `_is_device_type()` for device identification
  - [ ] Implemented `_discover_channels()` to find and initialize channels
- [ ] Exported public API in `__init__.py`
- [ ] Updated main package exports
- [ ] Added comprehensive docstrings to all classes and methods
- [ ] Tested device discovery
- [ ] Tested all capabilities
- [ ] Verified command caching works correctly
- [ ] Documented device-specific features and limitations

---
