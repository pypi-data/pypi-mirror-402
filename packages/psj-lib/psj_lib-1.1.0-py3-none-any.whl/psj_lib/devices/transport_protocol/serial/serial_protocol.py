import asyncio
import logging
from typing import List

import aioserial
import serial.tools.list_ports

from ..transport_protocol import DiscoveryCallback, TransportProtocol
from ..transport_types import (
    DetectedDevice,
    DeviceUnavailableException,
    TransportProtocolInfo,
    TransportType,
)


# Global module locker
logger = logging.getLogger(__name__)

class SerialProtocol(TransportProtocol):
    """Serial/USB transport protocol implementation for piezo devices.
    
    Provides asynchronous communication with piezoelectric devices over RS-232
    serial ports or USB-to-serial adapters. Uses the aioserial library for
    async I/O operations.
    
    Connection Types Supported:
        - Direct RS-232 serial ports
        - USB-to-serial adapters
        - Virtual COM ports
    
    Communication Parameters:
        - Baud rate: 115200 (default, configurable)
        - Data bits: 8
        - Parity: None
        - Stop bits: 1
        - Flow control: Software (XON/XOFF)
    
    Discovery:
        Automatically discovers devices on USB-serial adapters by
        enumerating available serial ports and attempting communication.
    
    Attributes:
        TRANSPORT_TYPE: TransportType.SERIAL (for auto-registration)
    
    Note:
        - Requires appropriate permissions for serial port access
        - Port names are OS-specific:
          * Windows: 'COM1', 'COM3', etc.
          * Linux: '/dev/ttyUSB0', '/dev/ttyACM0', etc.
          * macOS: '/dev/cu.usbserial-*', etc.
    """   

    TRANSPORT_TYPE = TransportType.SERIAL

    def __init__(
        self,
        identifier: str,
        baudrate: int = 115200
    ):
        """Initialize serial transport protocol.

        Args:
            identifier: Serial port name/path. Must be a valid serial port
                identifier for the operating system:
                - Windows: 'COM1', 'COM3', etc.
                - Linux: '/dev/ttyUSB0', '/dev/ttyACM0', etc.
                - macOS: '/dev/cu.usbserial-XXXXXXXX', etc.
            baudrate: Communication speed in bits per second. Default: 115200.
                Most piezo devices use 115200 baud. Only change if device
                specifically requires a different rate.
        
        Example:
            >>> # Windows
            >>> protocol = SerialProtocol('COM3')
            >>> 
            >>> # Linux
            >>> protocol = SerialProtocol('/dev/ttyUSB0')
            >>> 
            >>> # Custom baud rate (rare)
            >>> protocol = SerialProtocol('COM3', baudrate=9600)
        
        Note:
            - Does not establish connection (call connect() separately)
            - Port must exist and be accessible
            - Baud rate must match device configuration
        """
        super().__init__(identifier)
        self.__serial: aioserial.AioSerial | None = None
        self.__port: str | None = identifier
        self.__baudrate: int = baudrate

    @property
    def serial(self) -> aioserial.AioSerial | None:
        """
        Provides access to the internal AioSerial interface.
        Returns:
            AioSerial: The internal AioSerial instance.
        """
        return self.__serial

    @staticmethod
    async def discover_devices(discovery_cb: DiscoveryCallback) -> List[DetectedDevice]:
        """Discover piezo devices connected via serial/USB ports.
        
        Enumerates all available serial ports, filters for FTDI USB-serial
        adapters, and attempts to communicate with each to identify devices.
        Discovery runs concurrently across all ports for efficiency.
        
        Process:
        1. Enumerate all serial ports on the system
        2. Attempt connection to each port
        3. Call discovery_cb to identify device type
        4. Return list of successfully identified devices

        Args:
            discovery_cb: Async callback for device identification.
                Receives (protocol, detected_device), returns True to include.
                Should send identification command and verify device type.

        Returns:
            List of DetectedDevice objects for identified devices. Each contains:
            - transport: TransportType.SERIAL
            - identifier: Port name (e.g., 'COM3', '/dev/ttyUSB0')
            - device_id: Populated by discovery_cb
            - extended_info: Optional additional data
        
        Example:
            >>> async def identify_d_drive(protocol, detected):
            ...     await protocol.write('identify\\r\\n')
            ...     response = await protocol.read_message(timeout=1.0)
            ...     if 'd-drive' in response.lower():
            ...         detected.device_id = 'd-drive'
            ...         return True
            ...     return False
            >>> 
            >>> devices = await SerialProtocol.discover_devices(identify_d_drive)
            >>> print(f"Found {len(devices)} devices")
        
        Note:
            - Requires serial port access permissions
            - Failed connections are logged but don't raise exceptions
            - Discovery can take multiple seconds depending on port count
            - Ports are tested concurrently for better performance
        """
        ports = serial.tools.list_ports.comports()
        valid_ports = [p.device for p in ports]

        async def detect_on_port(port_name: str) -> DetectedDevice | None:
            protocol = SerialProtocol(port_name)
            try:
                await protocol.connect()
                device_id = await discovery_cb(protocol)

                if device_id is None:
                    return None
                
                return DetectedDevice(
                    device_id=device_id,
                    transport=TransportType.SERIAL,
                    identifier=port_name
                )
            except Exception as e:
                # We do ignore the exception - if it is not possible to connect to the device, we just return None
                logger.info(f"Error on port {port_name}: {e.__class__.__name__} {e}")
                return None
            finally:
                await protocol.close()

        # Run all detections concurrently
        tasks = [detect_on_port(port) for port in valid_ports]
        results = await asyncio.gather(*tasks)
        # Filter out Nones
        return [dev for dev in results if dev]

    async def connect(self, auto_adjust_comm_params: bool = True):
        """Establish serial connection to the device.

        Opens the serial port with configured parameters (baud rate, flow control)
        and prepares for communication. The port must be accessible and not in
        use by another application.

        Args:
            auto_adjust_comm_params: Ignored for serial transport (no-op).
                Included for interface consistency with TelnetProtocol.

        Raises:
            DeviceUnavailableException: If no port identifier was provided during
                initialization, or if the port cannot be opened (permission denied,
                port in use, port doesn't exist, etc.)
        
        Example:
            >>> protocol = SerialProtocol('/dev/ttyUSB0')
            >>> await protocol.connect()
            >>> # Port is now open and ready for communication
        
        Note:
            - Idempotent: safe to call multiple times
            - Sets XON/XOFF flow control to False (software flow control disabled)
            - Uses aioserial for async I/O operations
            - Input buffers are NOT automatically flushed (call flush_input())
        """
        if self.__port is None:
            raise DeviceUnavailableException("No serial port specified for connection.")

        if self.is_connected:
            return  # Already connected

        self.__serial = aioserial.AioSerial(port=self.__port, xonxoff=False, baudrate=self.__baudrate)

    async def flush_input(self):
        """Discard all pending input data from the serial port.
        
        Clears the operating system and library input buffers, discarding any
        data that has been received but not yet read. Essential for:
        - Synchronizing command/response sequences
        - Clearing power-on or error messages
        - Recovering from communication errors
        
        Example:
            >>> await protocol.flush_input()  # Clear old data
            >>> await protocol.write('voltage\\r\\n')  # Send fresh command
            >>> response = await protocol.read_message()  # Get clean response
        
        Note:
            - Non-blocking operation (completes immediately)
            - Called automatically by write() method before sending commands
            - Does not affect output buffer or data in transit
        """
        self.__serial.reset_input_buffer()


    async def write(self, cmd: str):
        """Send a command string to the device via serial port.
        
        Flushes input buffer, then transmits the command. Data is encoded using
        latin1 (ISO-8859-1) encoding to preserve extended ASCII characters.

        Args:
            cmd: Complete command string including any delimiters (e.g., '\\r\\n')
        
        Example:
            >>> await protocol.write('identify\\r\\n')
            >>> await protocol.write('voltage,0,10.5\\r\\n')
        
        Note:
            - Automatically flushes input buffer before sending
            - Uses latin1 encoding (not UTF-8)
            - Does not read response (use read_message() separately)
        """
        await self.flush_input()
        await self.__serial.write_async(cmd.encode('latin1'))

    async def read_until(self, expected: bytes = TransportProtocol.XON, timeout: float = TransportProtocol.DEFAULT_TIMEOUT_SECS) -> str:
        """Read from serial port until delimiter is encountered.
        
        Reads data from the serial port until the expected byte sequence is
        found or timeout occurs. XON (0x11) and XOFF (0x13) flow control
        characters are automatically stripped from the response.

        Args:
            expected: Byte sequence to read until. Default: XON (0x11)
            timeout: Maximum time to wait in seconds. Default: 0.6

        Returns:
            Decoded string with flow control characters stripped

        Raises:
            asyncio.TimeoutError: If expected delimiter not received within timeout
        
        Example:
            >>> # Read until XON character
            >>> response = await protocol.read_until()
            >>> 
            >>> # Read until CRLF
            >>> response = await protocol.read_until(TransportProtocol.CRLF, timeout=1.0)
        
        Note:
            - Uses latin1 decoding to match write() encoding
            - Strips XON (0x11) and XOFF (0x13) characters automatically
            - Delimiter is not included in returned string
            - Timeout is enforced strictly
        """
        data = await asyncio.wait_for(self.__serial.read_until_async(expected), timeout)
        # return data.replace(TransportProtocol.XON, b'').replace(TransportProtocol.XOFF, b'') # strip XON and XOFF characters
        return data.decode('latin1').strip("\x11\x13")  # strip XON and XOFF characters

    async def close(self):
        """Close the serial port and release resources.
        
        Shuts down the serial connection and frees the port for use by other
        applications. Idempotent operation (safe to call multiple times).
        
        Example:
            >>> await protocol.close()
            >>> # Port is now available for other applications
        
        Note:
            - Always call when done with device to prevent port locking
            - Safe to call even if already closed
            - Does not flush output buffer before closing
        """
        if self.__serial:
            self.__serial.close()

    @property
    def port(self) -> str:
        """Get the serial port identifier.
        
        Returns:
            Port name/path as provided during initialization
            (e.g., 'COM3', '/dev/ttyUSB0')
        """
        return self.__port

    @property
    def is_connected(self) -> bool:
        """Check if serial port is open and ready for communication.
        
        Returns:
            True if port is open, False otherwise
        
        Note:
            This is a local check only - does not verify device responsiveness
        """
        return self.__serial is not None and self.__serial.is_open

    def get_info(self) -> TransportProtocolInfo:
        """Get transport protocol metadata.
        
        Returns:
            TransportProtocolInfo containing:
            - transport: TransportType.SERIAL
            - identifier: Port name (e.g., 'COM3')
        
        Example:
            >>> info = protocol.get_info()
            >>> print(f"Connected via {info.transport.name} on {info.identifier}")
        """
        return TransportProtocolInfo(
            transport=TransportType.SERIAL,
            identifier=self.__port,
        )