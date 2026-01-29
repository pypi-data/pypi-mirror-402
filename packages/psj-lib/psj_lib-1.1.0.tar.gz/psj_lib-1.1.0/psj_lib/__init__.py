"""
psj_lib - Python Library for Piezosystem Jena Devices

This library provides a comprehensive interface for controlling piezoelectric amplifiers
and control devices manufactured by piezosystem jena GmbH. It offers both low-level
transport protocol implementations and high-level device abstractions for easy integration
into automation and control systems.

The library currently supports the d-Drive modular piezo amplifier system, with a flexible
architecture designed to accommodate additional device types in the future.

Main Components:
    - Base device classes: Generic piezo device and channel abstractions
    - Transport protocols: Serial and Telnet communication interfaces
    - Capabilities: Modular features like PID control, waveform generation, data recording
    - d-Drive: Specific implementations for d-Drive modular amplifiers

Example:
    >>> from psj_lib import DDriveDevice, TransportType
    >>> # Connect to a d-Drive device via serial port
    >>> device = DDriveDevice(TransportType.SERIAL, "COM3")
    >>> await device.connect()
    >>> # Access a channel
    >>> channel = device.channel[0]
    >>> await channel.setpoint.set(50.0)  # Set to 50 µm or 50 mrad or 50 V (depending on actuator and closed-loop mode)
    >>> await device.close()

For detailed documentation and examples, visit:
https://github.com/piezosystemjena/psj-lib
"""

from .devices.base import (
    PiezoChannel,
    PiezoDevice,
    DeviceError,
    ErrorNotSpecified,
    UnknownCommand,
    ParameterMissing,
    AdmissibleParameterRangeExceeded,
    CommandParameterCountExceeded,
    ParameterLockedOrReadOnly,
    ParameterTooHigh,
    ParameterTooLow,
    Underload,
    Overload,
    UnknownChannel,
    ActuatorNotConnected,
)
from .devices.base.capabilities import (
    ActuatorDescription,
    CapabilityDescriptor,
    ClosedLoopController,
    DataRecorder,
    DataRecorderChannel,
    ErrorLowPassFilter,
    FactoryReset,
    Fan,
    LowPassFilter,
    ModulationSource,
    ModulationSourceTypes,
    MonitorOutput,
    MonitorOutputSource,
    NotchFilter,
    PIDController,
    PiezoCapability,
    Position,
    PreControlFactor,
    ProgressCallback,
    Setpoint,
    SlewRate,
    StaticWaveformGenerator,
    Status,
    StatusRegister,
    Temperature,
    TriggerDataSource,
    TriggerEdge,
    TriggerOut,
    Units
)
from .devices.base.piezo_types import (
    ActorType,
    DeviceInfo,
    SensorType,
)
from .devices.d_drive_family import (
    DDriveChannel,
    DDriveClosedLoopController,
    DDriveDataRecorder,
    DDriveDataRecorderChannel,
    DDriveDevice,
    DDriveModulationSourceTypes,
    DDriveMonitorOutputSource,
    DDriveStatusRegister,
    DDriveTriggerOut,
    DDriveWaveformGenerator,
    DDriveWaveformType,
    PSJ30DVChannel,
    PSJ30DVDevice,
)
from .devices.transport_protocol import (
    DiscoverFlags,
    TransportProtocolInfo,
    TransportType,
    DeviceUnavailableException,
    ProtocolException,
    TimeoutException
)

__all__ = [
    # Base Device Classes
    "PiezoChannel",
    "PiezoDevice",

    # Exceptions
    "DeviceError",
    "ErrorNotSpecified",
    "UnknownCommand",
    "ParameterMissing",
    "AdmissibleParameterRangeExceeded",
    "CommandParameterCountExceeded",
    "ParameterLockedOrReadOnly",
    "ParameterTooHigh",
    "ParameterTooLow",
    "Underload",
    "Overload",
    "UnknownChannel",
    "ActuatorNotConnected",

    # Base Capabilities
    "ActuatorDescription",
    "CapabilityDescriptor",
    "ClosedLoopController",
    "DataRecorder",
    "DataRecorderChannel",
    "ErrorLowPassFilter",
    "FactoryReset",
    "Fan",
    "LowPassFilter",
    "ModulationSource",
    "ModulationSourceTypes",
    "MonitorOutput",
    "MonitorOutputSource",
    "NotchFilter",
    "PIDController",
    "PiezoCapability",
    "Position",
    "PreControlFactor",
    "ProgressCallback",
    "Setpoint",
    "SlewRate",
    "StaticWaveformGenerator",
    "Status",
    "StatusRegister",
    "Temperature",
    "TriggerDataSource",
    "TriggerEdge",
    "TriggerOut",
    "Units",

    # Base Types
    "ActorType",
    "DeviceInfo",
    "SensorType",

    # DDrive Family Classes
    "DDriveChannel",
    "DDriveClosedLoopController",
    "DDriveDataRecorder",
    "DDriveDataRecorderChannel",
    "DDriveDevice",
    "DDriveModulationSourceTypes",
    "DDriveMonitorOutputSource",
    "DDriveStatusRegister",
    "DDriveTriggerOut",
    "DDriveWaveformGenerator",
    "DDriveWaveformType",
    "PSJ30DVChannel",
    "PSJ30DVDevice",

    # Transport Protocol
    "DiscoverFlags",
    "TransportProtocolInfo",
    "TransportType",
    "DeviceUnavailableException",
    "ProtocolException",
    "TimeoutException",
]

__version__ = "1.1.0"
