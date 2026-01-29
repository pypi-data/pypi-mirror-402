from dataclasses import dataclass, field
from enum import Enum
from typing import Dict, Optional

from ..transport_protocol import TransportProtocolInfo


class SensorType(Enum):
    """
    Enumeration of position sensor types used in piezoelectric actuators.
    
    Different actuator models use different sensor technologies for position feedback
    in closed-loop control systems. The sensor type affects measurement accuracy,
    resolution, and environmental sensitivity.
    
    Attributes:
        NONE (0): No position sensor present.
            Actuator operates in open-loop mode only. Position control relies solely
            on the voltage-displacement relationship of the piezo stack.
            
        STRAIN_GAUGE (1): Strain gauge based position sensor.
            Measures mechanical deformation. Good for compact designs but can be
            less accurate and more environmentally sensitive than other sensor types.
            
        CAPACITIVE (2): Capacitive position sensor.
            Non-contact measurement with high resolution and excellent linearity.
            Common in high-precision nanopositioning actuators.
            
        INDUCTIVE (3): Inductive position sensor.
            Measures position through electromagnetic induction. Robust against
            environmental disturbances but typically lower resolution than capacitive.
            
        UNKNOWN (99): Sensor type could not be determined.
            Fallback value when sensor information is unavailable or unrecognized.
    """
    NONE = 0
    STRAIN_GAUGE = 1
    CAPACITIVE = 2
    INDUCTIVE = 3
    UNKNOWN = 99


class ActorType(Enum):
    """
    Enumeration of piezoelectric actuator connection types and geometries.
    
    Different actuator designs require different electrical driving schemes and have
    different characteristics in terms of stroke, force, and response time.
    
    Attributes:
        NANOX (0): piezosystem jena nanoX® actuators.
            
        PSH (1): PSH style piezo actuators (not used anymore).
            
        PARALLEL (2): Normal piezo actuators with parallel output stage configuration.
            
        UNKNOWN (99): Actuator type could not be determined.
            Fallback value when actuator information is unavailable or unrecognized.
    """
    NANOX = 0
    PSH = 1
    PARALLEL = 2
    UNKNOWN = 99


@dataclass
class DeviceInfo:
    """
    Complete information about a connected piezoelectric device.
    
    This dataclass aggregates all identification and configuration information for a
    connected device. It combines transport-layer information with device-specific
    metadata, providing a complete picture of the device's identity and capabilities.
    
    This information is typically populated during device discovery or initial connection
    and is used throughout the device's lifecycle for logging, identification, and
    configuration management.

    Attributes:
        transport_info (TransportProtocolInfo): Transport layer connection details.
            Contains the transport type (SERIAL/TELNET), connection identifier
            (COM port or IP address), and MAC address if applicable.
            
        device_id (Optional[str]): Device model or family identifier.
            Examples:
            - "d-Drive": Modular d-Drive piezo amplifier
            - "NV200/D_NET": Network-enabled NV200 compact amplifier  
            - "SPI Controller Box": Multi-channel SPI controller
            This field is None if device identification has not been performed.
            
        extended_info (Dict[str, str]): Device-specific metadata dictionary.
            Additional information that varies by device type. Common keys include:
            - "actuator_name": Model name of connected actuator (e.g., "PSH15SG_Y")
            - "actuator_serial": Serial number of connected actuator
            - "firmware_version": Device firmware version string
            - "channels": Number of available channels
            - "capabilities": List of supported features
            Empty dict if extended information was not requested during discovery.
    
    Example:
        >>> device = await DDriveDevice.discover_devices()[0]
        >>> info = device.device_info
        >>> print(f"Connected to {info.device_id} on {info.transport_info}")
        >>> print(f"Actuator: {info.extended_info.get('actuator_name', 'Unknown')}")
    """
    transport_info: TransportProtocolInfo
    device_id: Optional[str] = None  # Unique identifier for the device, if available
    extended_info: Dict[str, str] = field(default_factory=dict)

    def __str__(self):
        """
        Returns a string representation of the transport type, capitalized.
        """
        device_info = f"{self.transport_info}"
        if self.device_id:
            device_info += f" - {self.device_id}"
        if self.extended_info:
            return f"{device_info} - {self.extended_info}"
        else:
            return device_info