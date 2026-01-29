from dataclasses import dataclass, field
from enum import Enum
from typing import Dict, Optional


class ProtocolException(Exception):
    """
    Base exception class for transport protocol communication errors.
    
    This exception serves as the parent class for all protocol-related exceptions,
    allowing users to catch any transport protocol error with a single except clause.
    
    Raised when there are general communication errors that don't fit into
    more specific exception categories.
    """

    pass


class DeviceUnavailableException(ProtocolException):
    """
    Exception raised when a device cannot be accessed or is unavailable.
    
    This exception is typically raised when:
    - A device cannot be found on the specified port or network address
    - A device is physically disconnected during operation
    - Network connectivity to a device is lost
    - A serial port cannot be opened due to permissions or other issues
    
    Example:
        >>> try:
        ...     device = DDriveDevice(TransportType.SERIAL, "COM99")
        ...     await device.connect()
        ... except DeviceUnavailableException:
        ...     print("Device not found on COM99")
    """

    pass


class TimeoutException(ProtocolException):
    """
    Exception raised when a communication operation times out.
    
    This exception occurs when a read or write operation does not complete
    within the specified timeout period. This typically indicates:
    - The device is not responding
    - The device is busy processing another command
    - Communication interference or hardware issues
    - Incorrect communication parameters
    
    The default timeout for most operations is 0.6 seconds, but this can be
    adjusted based on the specific operation and device response time.
    """

    pass


class TransportType(str, Enum):
    """
    Enumeration of supported transport layer protocols for device communication.
    
    This enum defines the available methods for communicating with piezosystem jena
    devices. Each transport type has its own characteristics, advantages, and use cases.

    Attributes:
        TELNET: Network communication via Telnet protocol (TCP/IP).
            - Used for Ethernet-connected devices
            - Supports remote operation over LAN/WAN
            - Typical identifier: IP address (e.g., "192.168.1.100")
            - Default port: 23
            
        SERIAL: Direct serial communication (RS-232/USB-Serial).
            - Used for USB or RS-232 connected devices
            - Lower latency than network communication
            - Typical identifier: COM port (Windows) or /dev/ttyUSB* (Linux)
            - Default baud rate: 115200
    
    Example:
        >>> # Connect via serial
        >>> device = DDriveDevice(TransportType.SERIAL, "COM3")
        >>> # Connect via network
        >>> device = DDriveDevice(TransportType.TELNET, "192.168.1.100")
    """
    TELNET = "telnet"
    SERIAL = "serial"

    def __str__(self):
        """
        Returns a string representation of the transport type, capitalized.
        """
        return self.name.capitalize()


@dataclass
class TransportProtocolInfo:
    """
    Container for transport protocol metadata and connection information.
    
    This class encapsulates the essential information needed to identify and
    describe a transport protocol connection to a device. It is used throughout
    the library to pass connection information between discovery, connection,
    and device management functions.
    
    Attributes:
        transport (TransportType): The type of transport protocol in use.
        identifier (str): The connection identifier specific to the transport type.
            - For SERIAL: COM port name (e.g., "COM3", "/dev/ttyUSB0")
            - For TELNET: IP address (e.g., "192.168.1.100")
        mac (Optional[str]): MAC address of the device, if available and applicable.
            Only relevant for network-connected devices (TELNET transport).
    
    Example:
        >>> info = TransportProtocolInfo(
        ...     transport=TransportType.TELNET,
        ...     identifier="192.168.1.100",
        ...     mac="00:80:A3:12:34:56"
        ... )
        >>> print(info)  # "Telnet @ 192.168.1.100"
    """
    transport: TransportType
    identifier: str  # e.g., IP or serial port
    mac: Optional[str] = None

    def __str__(self):
        """
        Returns a string representation of the TransportProtocolInfo.
        """
        return f"{self.transport} @ {self.identifier}"


@dataclass
class DetectedDevice:
    """
    Information about a device discovered during network or serial scanning.
    
    This class represents a device that has been found during the discovery process.
    It contains all the information needed to identify the device and establish a
    connection. After discovery, this information can be used to create a device
    instance and connect to it.

    Attributes:
        transport (TransportType): The transport protocol type for this device.
            Indicates whether the device was found via serial or network.
            
        identifier (str): Transport-specific connection identifier.
            - For SERIAL: COM port or device path (e.g., "COM3", "/dev/ttyUSB0")
            - For TELNET: IP address (e.g., "192.168.1.100")
            
        mac (Optional[str]): MAC address for network devices.
            Only populated for TELNET transport. Used for unique device identification
            in network environments. Format: "XX:XX:XX:XX:XX:XX"
            
        device_id (Optional[str]): Device model identifier if detected.
            Examples: "d-Drive", "SPI Controller Box"
            This is only available if device identification was requested during discovery.
            
        device_info (Dict[str, str]): Extended device information dictionary.
            May contain keys such as:
            - "actuator_name": Connected actuator model
            - "actuator_serial": Actuator serial number
            - "firmware_version": Device firmware version
            Only populated if DiscoverFlags.READ_DEVICE_INFO was used.
    
    Example:
        >>> from psj_lib import DDriveDevice
        >>> devices = await DDriveDevice.discover_devices()
        >>> if devices:
        ...     print(devices[0])  # "Serial @ COM3 - d-Drive - {...}"
        ...     device = DDriveDevice.from_detected_device(devices[0])
    """
    transport: TransportType
    identifier: str  # e.g., IP or serial port
    mac: Optional[str] = None
    device_id: Optional[str] = None  # Unique identifier for the device, if available

    def __str__(self):
        """
        Returns a string representation of the transport type, capitalized.
        """
        result = f"{self.transport} @ {self.identifier}"
        if self.mac:
            result += f" (MAC: {self.mac})"

        if self.device_id:
            result += f" - {self.device_id}"

        return result