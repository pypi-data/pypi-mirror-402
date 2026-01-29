import logging
from abc import ABC, abstractmethod
from typing import Awaitable, Callable

from .transport_types import DetectedDevice, TransportProtocolInfo, TransportType

# Global module locker
logger = logging.getLogger(__name__)

# Async function to enrich discovered device with device information
type DiscoveryCallback = Callable[
    [TransportProtocol, DetectedDevice],
    Awaitable[bool]
]

# Registry for transport protocol implementations
TRANSPORT_REGISTRY: dict[TransportType, type["TransportProtocol"]] = {}


class TransportProtocol(ABC):
    """Abstract base class for device communication transport protocols.
    
    This class defines the interface for low-level communication with piezo devices
    over different physical transports (serial, Telnet/TCP). Concrete implementations
    handle protocol-specific details while presenting a uniform async API.
    
    Transport Protocol Responsibilities:
        - Establishing and managing physical connections
        - Sending commands and receiving responses
        - Device discovery on the transport medium
        - Protocol-specific framing and delimiters
        - Timeout and error handling
    
    Supported Transports:
        - Serial: RS-232/USB connections (serial_protocol.py)
        - Telnet: TCP/IP network connections (telnet_protocol.py)
    
    Class Attributes:
        XON (bytes): Flow control XON character (0x11)
        XOFF (bytes): Flow control XOFF character (0x13)
        LF (bytes): Line feed character (0x0A)
        CR (bytes): Carriage return character (0x0D)
        CRLF (bytes): Carriage return + line feed (0x0D0A)
        DEFAULT_TIMEOUT_SECS (float): Default command timeout (0.6 seconds)
        TRANSPORT_TYPE (TransportType | None): Type identifier (set by subclasses)
    
    Instance Attributes:
        rx_delimiter (bytes): Expected delimiter at end of device responses.
            Default is XON, but devices may use CRLF or other delimiters.
    
    Auto-Registration:
        Subclasses automatically register themselves in TRANSPORT_REGISTRY when
        they define a TRANSPORT_TYPE class attribute. This enables factory-based
        transport creation and discovery.
    
    Example:
        >>> # Typically not instantiated directly - use TransportFactory
        >>> transport = TransportFactory.from_transport_type(
        ...     TransportType.SERIAL,
        ...     identifier='/dev/ttyUSB0'
        ... )
        >>> await transport.connect()
        >>> await transport.write('identify' + transport.CRLF)
        >>> response = await transport.read_message()
        >>> await transport.close()
    
    Note:
        - Subclasses must implement all abstract methods
        - Subclasses must set TRANSPORT_TYPE for auto-registration
        - All methods should be async for consistency
        - Use read_message() for complete responses, read_until() for custom delimiters
    """
    XON = b'\x11'
    XOFF = b'\x13'
    LF = b'\x0A'
    CR = b'\x0D'
    CRLF = b'\x0D\x0A'
    DEFAULT_TIMEOUT_SECS = 0.6

    TRANSPORT_TYPE: TransportType | None = None  # To be set in subclasses

    def __init__(
        self,
        identifier: str
    ):
        """Initialize the transport protocol base.

        Args:
            identifier: Connection identifier specific to transport type:
                - Serial: Port name (e.g., 'COM3', '/dev/ttyUSB0', '/dev/tty.usbserial')
                - Telnet: IP address or hostname (e.g., '192.168.1.100', 'device.local')
        
        Note:
            Subclasses should call super().__init__(identifier) and then initialize
            their transport-specific state.
        """
        self.rx_delimiter = TransportProtocol.XON  # Default delimiter for reading messages

    def __init_subclass__(cls, **kwargs):
        super().__init_subclass__(**kwargs)

        if cls.TRANSPORT_TYPE:
            TRANSPORT_REGISTRY[cls.TRANSPORT_TYPE] = cls

    @abstractmethod
    async def discover_devices(self, discovery_cb: DiscoveryCallback) -> list[DetectedDevice]:
        """Discover devices accessible via this transport protocol.

        Scans the transport medium for connected devices and returns a list of
        detected devices with connection information. The discovery callback is
        used to identify and filter specific device types.
        
        Implementation Guidelines:
        - Serial: Enumerate available serial ports, attempt communication on each
        - Telnet: Scan network and attempt connections on Port 23
        - Test basic communication to verify device presence
        - Call discovery_cb to identify and filter device types
        - Handle timeouts gracefully (skip unresponsive devices)

        Args:
            discovery_cb: Async callback function that receives a TransportProtocol
                and DetectedDevice, returns True if device should be included in results.
                Used for device type identification and filtering.

        Returns:
            List of DetectedDevice objects representing found devices. Each includes:
            - device_id: Identified device model
            - transport: TransportType for this protocol
            - identifier: Connection string for the device
            - extended_info: Optional additional device information

        Example (subclass implementation):
            >>> async def discover_devices(self, discovery_cb):
            ...     devices = []
            ...     for port in enumerate_serial_ports():
            ...         try:
            ...             temp_transport = SerialProtocol(port)
            ...             await temp_transport.connect()
            ...             detected = DetectedDevice(
            ...                 transport=TransportType.SERIAL,
            ...                 identifier=port
            ...             )
            ...             if await discovery_cb(temp_transport, detected):
            ...                 devices.append(detected)
            ...         finally:
            ...             await temp_transport.close()
            ...     return devices
        
        Note:
            - Discovery can be slow (multiple connection attempts)
            - Should not raise exceptions for individual device failures
            - Temporary connections are created and closed during discovery
        """

    @abstractmethod
    async def connect(self, auto_adjust_comm_params: bool = True):
        """Establish connection to the device via this transport.

        Opens the physical connection (serial port, TCP socket) and performs
        any necessary initialization. For Telnet transport, can automatically
        configure the Lantronix XPORT module for optimal communication.

        Args:
            auto_adjust_comm_params: For Telnet transport only, automatically
                configure the XPORT ethernet module communication parameters.
                Sets flow control to XON_XOFF_PASS_TO_HOST mode. Ignored for
                serial transport. Default: True (recommended for Telnet)

        Raises:
            DeviceUnavailableException: If connection cannot be established
            TransportException: For transport-specific connection errors
            TimeoutException: If connection attempt times out
        
        Example (subclass implementation):
            >>> async def connect(self, auto_adjust_comm_params=True):
            ...     # Open serial port
            ...     self._serial = Serial(self._port, baudrate=115200)
            ...     await self._serial.open()
            ...     
            ...     # Flush any pending data
            ...     await self.flush_input()
        """

    async def read_message(self, timeout: float = DEFAULT_TIMEOUT_SECS) -> str:
        """Read a complete delimited message from the device.
        
        This convenience method reads until the configured rx_delimiter is
        encountered, then returns the complete message. The delimiter is
        determined by the device's response format (typically XON or CRLF).

        Args:
            timeout: Maximum time to wait for complete message in seconds.
                Default: 0.6 seconds

        Returns:
            Complete message string from device (delimiter may or may not be included
            depending on read_until implementation)

        Raises:
            TimeoutException: If complete message not received within timeout
            DeviceUnavailableException: If transport connection is lost
        
        Example:
            >>> # With XON delimiter (0x11)
            >>> transport.rx_delimiter = TransportProtocol.XON
            >>> response = await transport.read_message()
            >>> # response = 'voltage,10.5' (XON terminator read and stripped)
            >>> 
            >>> # With CRLF delimiter
            >>> transport.rx_delimiter = TransportProtocol.CRLF
            >>> response = await transport.read_message()
            >>> # response = 'identify,d-drive,v1.0\r\n' or 'identify,d-drive,v1.0'
        
        Note:
            - Uses rx_delimiter instance attribute (set by device or user)
            - Delegates to read_until() for actual reading
            - Device class sets rx_delimiter based on device requirements
        """
        return await self.read_until(self.rx_delimiter, timeout)

    @abstractmethod
    async def read_until(self, expected: bytes = XON, timeout: float = DEFAULT_TIMEOUT_SECS) -> str:
        """Read from transport until expected byte sequence is encountered.

        Reads data byte-by-byte or in chunks until the expected delimiter sequence
        is found or timeout occurs. This is the low-level read primitive used by
        read_message().

        Args:
            expected: Byte sequence to read until. Common values:
                - TransportProtocol.XON (0x11): Flow control character
                - TransportProtocol.CRLF (0x0D0A): Windows-style line ending
                - TransportProtocol.LF (0x0A): Unix-style line ending
                Default: XON
            timeout: Maximum time to wait in seconds. Default: 0.6

        Returns:
            Data read as decoded string. Delimiter may or may not be included
            depending on implementation (typically stripped).

        Raises:
            TimeoutException: If expected sequence not found within timeout
            DeviceUnavailableException: If connection is lost during read
        
        Example (subclass implementation):
            >>> async def read_until(self, expected=XON, timeout=0.6):
            ...     buffer = bytearray()
            ...     deadline = time.time() + timeout
            ...     
            ...     while time.time() < deadline:
            ...         byte = await self._read_byte()
            ...         buffer.append(byte)
            ...         if buffer.endswith(expected):
            ...             return buffer[:-len(expected)].decode('utf-8')
            ...     
            ...     raise TimeoutException("Read timeout")
        
        Note:
            - Core transport read method - must be efficiently implemented
            - Should handle partial reads and buffering
            - Encoding is typically UTF-8 or ASCII
            - Consider including delimiter in return for debugging
        """

    @abstractmethod
    def get_info(self) -> TransportProtocolInfo:
        """Get metadata about this transport connection.
        
        Returns information about the transport protocol and connection,
        useful for logging, diagnostics, and displaying connection status
        to users.

        Returns:
            TransportProtocolInfo object containing:
                - transport_type: SERIAL or TELNET
                - identifier: Port name or IP address
                - Additional protocol-specific information

        Example:
            >>> info = transport.get_info()
            >>> print(f"Connected via {info.transport_type.name} on {info.identifier}")
            >>> # Output: "Connected via SERIAL on COM3"
            >>> # or: "Connected via TELNET on 192.168.1.100"
        
        Note:
            - Can be called whether connected or not
            - Information is static (doesn't query device)
            - Subclasses may include additional fields in extended_info
        """

    @abstractmethod
    async def flush_input(self):
        """Clear any pending data in the input buffer.
        
        Discards any data that has been received but not yet read from the
        transport. This is important for:
        - Initial connection setup (clear power-on messages)
        - Error recovery (discard partial/corrupt data)
        - Synchronizing command/response sequences

        Raises:
            May raise transport-specific exceptions if flush fails
        
        Example (subclass implementation):
            >>> async def flush_input(self):
            ...     # Serial: clear OS and library buffers
            ...     self._serial.reset_input_buffer()
            ...     
            ...     # Or for async: read and discard all pending data
            ...     while self._serial.in_waiting > 0:
            ...         await self._serial.read(self._serial.in_waiting)
        
        Note:
            - Should be called after connect() before first command
            - Important before device identification during discovery
            - Non-blocking operation (completes immediately)
            - Does not affect data in transit or device output buffers
        """

    @abstractmethod
    async def write(self, cmd: str):
        """Send a command string to the device.
        
        Transmits the command to the device via the physical transport.
        The command should include any necessary framing or delimiters
        (typically CRLF) before calling this method.

        Args:
            cmd: Complete command string including any delimiters.
                Example: 'voltage,0,10.5\r\n' or 'identify\r\n'

        Raises:
            DeviceUnavailableException: If not connected or connection lost
            TransportException: For transport-specific write errors
        
        Example (subclass implementation):
            >>> async def write(self, cmd: str):
            ...     # Convert string to bytes
            ...     data = cmd.encode('utf-8')
            ...     
            ...     # Send via serial port
            ...     await self._serial.write(data)
            ...     
            ...     # Ensure transmission complete
            ...     await self._serial.drain()
        
        Note:
            - Caller responsible for adding frame delimiters (CRLF, etc.)
            - Should not wait for response (that's read_message's job)
            - Encoding is typically UTF-8 or ASCII
            - May need to handle flow control (XON/XOFF)
        """

    @abstractmethod
    async def close(self):
        """Close the transport connection and release resources.
        
        Properly shuts down the connection and releases any system resources
        (serial ports, sockets, etc.). Should be called when done communicating
        with the device.

        Raises:
            May raise transport-specific exceptions if close fails
        
        Example (subclass implementation):
            >>> async def close(self):
            ...     if self._serial and self._serial.is_open:
            ...         await self._serial.close()
            ...     self._serial = None
        
        Note:
            - Should be idempotent (safe to call multiple times)
            - Should set is_connected to False
            - May want to flush output before closing
            - Use in finally blocks or async context managers
        """

    @property
    @abstractmethod
    def is_connected(self) -> bool:
        """Check if the transport is currently connected.
        
        Returns connection status without attempting communication.
        Useful for checking before operations or for status displays.

        Returns:
            True if connected and ready for communication, False otherwise

        Example:
            >>> if not transport.is_connected:
            ...     await transport.connect()
            >>> 
            >>> await transport.write('command\r\n')
        
        Note:
            - This is a quick local check, does not verify device responsiveness
            - Connection may be lost between check and use
            - Actual communication may still fail even if True
            - Should be updated by connect() and close() methods
        """
