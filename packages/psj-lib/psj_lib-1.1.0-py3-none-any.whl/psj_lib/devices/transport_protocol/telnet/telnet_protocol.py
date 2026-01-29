import asyncio
import logging
from typing import List, Optional

import telnetlib3

from . import lantronix_xport as xport
from ..transport_protocol import DiscoveryCallback, TransportProtocol
from ..transport_types import (
    DetectedDevice,
    DeviceUnavailableException,
    TransportProtocolInfo,
    TransportType,
)
from .eth_utils import is_valid_ip, is_valid_mac
from .lantronix_xport import NetworkEndpoint

# Global module locker
logger = logging.getLogger(__name__)


class TelnetProtocol(TransportProtocol):
    """Telnet/TCP network transport protocol for piezo devices.
    
    Provides asynchronous communication with piezo amplifiers over TCP/IP
    networks, typically via Lantronix XPORT serial-to-ethernet adapters. Uses
    the telnetlib3 library for async Telnet protocol handling.
    
    Network Connection Types:
        - Direct TCP/IP connections to network-enabled devices
        - Ethernet-to-serial converters
    
    Connection Methods:
        - By IP address: Direct connection to known IP
        - By MAC address: Automatic discovery via UDP broadcast
        - Auto-discovery: Scan network for all Lantronix devices
    
    Communication Parameters:
        - Port: 23 (Telnet default, configurable)
        - Protocol: Telnet over TCP/IP
        - Flow control: XON/XOFF (auto-configured via XPORT)
    
    XPORT Configuration:
        Automatically configures Lantronix XPORT adapters for optimal
        communication by setting flow control to XON_XOFF_PASS_TO_HOST mode.
        This ensures flow control characters are forwarded to the host.
    
    Attributes:
        TRANSPORT_TYPE: TransportType.TELNET (for auto-registration)
    
    Example:
        >>> # Connect by IP address
        >>> protocol = TelnetProtocol(identifier='192.168.1.100')
        >>> await protocol.connect()
        >>> 
        >>> # Connect by MAC address (auto-discovers IP)
        >>> protocol = TelnetProtocol(identifier='00:80:A3:12:34:56')
        >>> await protocol.connect()
        >>> 
        >>> # Send command and read response
        >>> await protocol.write('identify\\r\\n')
        >>> response = await protocol.read_message()
        >>> 
        >>> # Discover all network devices
        >>> async def identify(tp, dev):
        ...     # Identification logic
        ...     return True
        >>> devices = await TelnetProtocol.discover_devices(identify)
    
    Note:
        - Requires network access to device subnet
        - XPORT configuration requires access to config port (typically 30718/UDP)
        - Firewall may need to allow Telnet (port 23) and discovery (30718/UDP)
        - MAC addresses must have Lantronix prefix (00:80:A3:xx:xx:xx)
    """
    TRANSPORT_TYPE = TransportType.TELNET
    def __init__(
        self,
        identifier: str = "",
        port: int = 23,
    ):
        """Initialize Telnet transport protocol.

        Args:
            identifier: Connection identifier - either IP address or MAC address:
                - IP address: Direct connection (e.g., '192.168.1.100')
                - MAC address: Discovers IP via UDP broadcast (e.g., '00:80:A3:12:34:56')
                - Empty string: Must be set before connect() or will fail
            port: TCP port for Telnet connection. Default: 23 (standard Telnet port).
                Lantronix XPORT devices typically use port 23.
        
        Example:
            >>> # Connect by IP
            >>> protocol = TelnetProtocol(identifier='192.168.1.100')
            >>> 
            >>> # Connect by MAC (IP will be discovered)
            >>> protocol = TelnetProtocol(identifier='00:80:A3:AB:CD:EF')
            >>> 
            >>> # Custom port
            >>> protocol = TelnetProtocol(identifier='192.168.1.100', port=9999)
        
        Note:
            - Does not establish connection (call connect() separately)
            - Identifier is validated on connect, not during init
            - MAC addresses must have Lantronix prefix (00:80:A3)
        """
        super().__init__(identifier=identifier)
        self.__host: str = is_valid_ip(identifier) or ""
        self.__port: int = port
        self.__MAC: str = is_valid_mac(identifier) or ""
        self.__reader = None
        self.__writer = None


    async def __connect_telnetlib(self):
        """
        Connect to telnetlib3 library
        """
        self.__reader, self.__writer = await asyncio.wait_for(
            telnetlib3.open_connection(self.__host, self.__port),
            timeout=5
        )

    async def is_xon_xoff_forwared_to_host(self) -> bool:
        """Check if XPORT is configured to forward XON/XOFF to host.
        
        Tests whether the Lantronix XPORT adapter is configured with
        XON_XOFF_PASS_TO_HOST flow control mode. This is required for
        proper library operation.
        
        The test sends a carriage return and checks if the response starts
        with XOFF (0x13), which indicates flow control characters are being
        forwarded.

        Returns:
            True if XON/XOFF forwarding is enabled, False otherwise
        
        Example:
            >>> await protocol.connect(auto_adjust_comm_params=False)
            >>> if not await protocol.is_xon_xoff_forwared_to_host():
            ...     print("Warning: XPORT not configured correctly")
        
        Note:
            - Only relevant for Lantronix XPORT adapters
            - Connection must be established before calling
            - Used internally to verify configuration
        """
        await self.write('\r\n')
        await asyncio.sleep(0.1)
        response = await self.__reader.read(1024)
        return response.startswith('\x13')

    @staticmethod
    async def configure_flow_control_mode(host: str) -> bool:
        """Configure Lantronix XPORT flow control for device communication.
        
        Sets the XPORT adapter's flow control mode to XON_XOFF_PASS_TO_HOST,
        which forwards XON/XOFF characters to the host instead of handling
        them internally. This is required for proper device communication.
        
        The configuration is done via the XPORT's setup port (30718/UDP).

        Args:
            host: IP address of the Lantronix XPORT device to configure

        Returns:
            True if configuration successful, False otherwise
        
        Example:
            >>> # Configure device before connecting
            >>> success = await TelnetProtocol.configure_flow_control_mode('192.168.1.100')
            >>> if success:
            ...     protocol = TelnetProtocol('192.168.1.100')
            ...     await protocol.connect(auto_adjust_comm_params=False)
        
        Note:
            - Requires network access to XPORT configuration port (30718/UDP)
            - Called automatically by connect() if auto_adjust_comm_params=True
            - Only needed for Lantronix XPORT adapters
        """
        return await xport.configure_flow_control(host)

    async def connect(self, auto_adjust_comm_params: bool = True):
        """Establish Telnet connection to the device.
        
        Connects to the device via TCP/IP, optionally configuring Lantronix
        XPORT communication parameters for optimal operation. If a MAC address
        was provided instead of IP, performs network discovery first.
        
        Connection Process:
        1. Validate identifier (IP or MAC provided)
        2. If MAC address: Discover IP via UDP broadcast
        3. If auto_adjust_comm_params: Configure XPORT flow control
        4. Establish Telnet connection on configured port

        Args:
            auto_adjust_comm_params: If True (default), automatically configure
                Lantronix XPORT flow control mode to XON_XOFF_PASS_TO_HOST.
                Recommended for all XPORT adapters. Adds 1-2 seconds due to
                device reset. Set False only if XPORT is pre-configured.

        Raises:
            DeviceUnavailableException: If:
                - Neither host nor MAC address provided
                - Device not found during MAC-based discovery
                - Connection timeout (5 seconds)
                - Device not responding on specified IP/port
        
        Example:
            >>> # Standard connection (recommended)
            >>> protocol = TelnetProtocol('192.168.1.100')
            >>> await protocol.connect()  # Auto-configures XPORT
            >>> 
            >>> # Connect by MAC
            >>> protocol = TelnetProtocol('00:80:A3:12:34:56')
            >>> await protocol.connect()  # Discovers IP, then connects
            >>> 
            >>> # Skip auto-configuration
            >>> await protocol.connect(auto_adjust_comm_params=False)
        
        Note:
            - 5-second connection timeout enforced
            - MAC discovery requires network broadcast support
            - Requires network access to device and (optionally) UDP port 30718
        """
        # Validate that at least host or MAC is provided
        if not self.__host and not self.__MAC:
            raise DeviceUnavailableException("Either host or MAC address must be specified to connect to the device")

        # Discover device IP using MAC address if host is not provided
        if not self.__host and self.__MAC:
            self.__host = await xport.discover_lantronix_device_async(self.__MAC)

            if not self.__host:
                raise DeviceUnavailableException(f"Device with MAC address {self.__MAC} not found")

        try:
            # ensure that flow control XON and XOFF chars are forwarded to host
            if auto_adjust_comm_params:
                logger.debug("Adjusting communication parameters for device %s", self.__host)
                await TelnetProtocol.configure_flow_control_mode(self.__host)
                logger.debug("Communication parameters adjusted for device %s", self.__host)

            logger.debug("Connecting to device %s", self.__host)
            await self.__connect_telnetlib()
            logger.debug("Connected to device %s", self.__host)
        except asyncio.TimeoutError as exc:
            raise DeviceUnavailableException(f"Device with host address {self.__host} not found") from exc

    async def flush_input(self):
        """Discard all pending input data from the network connection.
        
        Reads and discards any data already received but not yet processed,
        clearing the input buffer. Uses a short timeout (10ms) to quickly
        drain available data without blocking.
        
        Example:
            >>> await protocol.flush_input()  # Clear old data
            >>> await protocol.write('voltage\\r\\n')  # Send fresh command
            >>> response = await protocol.read_message()  # Get clean response
        
        Note:
            - Non-blocking (returns quickly even if no data)
            - Called automatically by write() method
            - Uses 10ms timeout per read attempt
            - Continues until no data available
        """
        try:
            while True:
                data = await asyncio.wait_for(self.__reader.read(1024), 0.01)
                if not data:
                    break
        except asyncio.TimeoutError:
            pass  # expected when no more data arrives within timeout

    async def write(self, cmd: str):
        """Send a command string to the device via Telnet.
        
        Flushes input buffer, then transmits the command over the Telnet
        connection. Data is sent as-is without additional encoding.

        Args:
            cmd: Complete command string including delimiters (e.g., '\\r\\n')
        
        Example:
            >>> await protocol.write('identify\\r\\n')
            >>> await protocol.write('voltage,0,10.5\\r\\n')
        
        Note:
            - Automatically flushes input buffer before sending
            - Does not wait for response (use read_message() separately)
            - Command is buffered by telnetlib3, may not transmit immediately
        """
        await self.flush_input()
        self.__writer.write(cmd)

    async def read_until(self, expected: bytes = TransportProtocol.XON, timeout: float = TransportProtocol.DEFAULT_TIMEOUT_SECS) -> str:
        """Read from Telnet connection until delimiter is encountered.
        
        Reads data until the expected byte sequence is found or timeout occurs.
        XON (0x11) and XOFF (0x13) flow control characters are automatically
        stripped from the response.

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
            >>> # Read until CRLF with longer timeout
            >>> response = await protocol.read_until(TransportProtocol.CRLF, timeout=2.0)
        
        Note:
            - Uses latin1 decoding
            - Strips XON (0x11) and XOFF (0x13) automatically
            - Delimiter is not included in returned string
            - Network latency may require longer timeouts than serial
        """
        data = await asyncio.wait_for(self.__reader.readuntil(expected), timeout)
        return data.decode('latin1').strip("\x11\x13")  # strip XON and XOFF characters

    async def close(self):
        """Close the Telnet connection and release resources.
        
        Shuts down the Telnet connection and cleans up reader/writer objects.
        Idempotent operation (safe to call multiple times).
        
        Example:
            >>> await protocol.close()
            >>> # Connection is closed, network resources released
        
        Note:
            - Safe to call even if already closed
            - Sets internal reader/writer to None
            - Does not flush pending output
        """
        if self.__writer:
            self.__writer.close()
            self.__writer = None
            self.__reader.close()
            self.__reader = None


    @property
    def host(self) -> str:
        """Get the device IP address.
        
        Returns:
            IP address string (e.g., '192.168.1.100'). May be empty if only
            MAC was provided and discovery hasn't run yet.
        """
        return self.__host

    @property
    def MAC(self) -> str:
        """Get the device MAC address.
        
        Returns:
            MAC address string (e.g., '00:80:A3:12:34:56'), or empty string
            if device was identified by IP only.
        """
        return self.__MAC

    @classmethod
    async def discover_devices(cls, discovery_cb: DiscoveryCallback) -> List[DetectedDevice]:
        """Discover piezo devices connected via Telnet/network.
        
        Scans the local network for Lantronix XPORT adapters via UDP broadcast,
        then attempts to connect to each and identify the attached device.
        Discovery runs concurrently across all found endpoints.
        
        Process:
        1. Send UDP broadcasts on all active network interfaces
        2. Parse responses to extract IP and MAC addresses
        3. Attempt Telnet connection to each responding device
        4. Call discovery_cb to identify device type
        5. Return list of successfully identified devices

        Args:
            discovery_cb: Async callback for device identification.
                Receives (protocol, detected_device), returns True to include.
                Should send identification command and verify device type.

        Returns:
            List of DetectedDevice objects for identified devices. Each contains:
            - transport: TransportType.TELNET
            - identifier: IP address (e.g., '192.168.1.100')
            - mac: MAC address (e.g., '00:80:A3:12:34:56')
            - device_id: Populated by discovery_cb
        
        Example:
            >>> async def identify_d_drive(protocol, detected):
            ...     await protocol.write('identify\\r\\n')
            ...     response = await protocol.read_message(timeout=1.0)
            ...     if 'd-drive' in response.lower():
            ...         detected.device_id = 'd-drive'
            ...         return True
            ...     return False
            >>> 
            >>> devices = await TelnetProtocol.discover_devices(identify_d_drive)
            >>> for dev in devices:
            ...     print(f"Found {dev.device_id} at {dev.identifier} ({dev.mac})")
        
        Note:
            - Only discovers Lantronix XPORT adapters (MAC prefix 00:80:A3)
            - Requires UDP broadcast support (may not work on all networks)
            - Firewall must allow UDP port 30718 and TCP port 23
            - Discovery can take multiple seconds
            - Failed connections logged but don't raise exceptions
        """
        network_endpoints = await xport.discover_lantronix_devices_async()
    
        async def detect_on_endpoint(network_endpoint: NetworkEndpoint) -> DetectedDevice | None:
            logger.debug("Connecting to network endpoint: %s", network_endpoint)
            protocol = TelnetProtocol(identifier=network_endpoint.ip)
            try:
                detected_device = DetectedDevice(
                    transport=TransportType.TELNET,
                    identifier=network_endpoint.ip,
                    mac=network_endpoint.mac
                )

                await protocol.connect()

                # Check if device is requested device
                is_type = await discovery_cb(protocol, detected_device)

                if not is_type:
                    return None
                    
                return detected_device
            except Exception as e:
                # We do ignore the exception - if it is not possible to connect to the device, we just return None
                print(f"Error for network endpoint {network_endpoint}: {e.__class__.__name__} {e}")
                return None
            finally:
                await protocol.close()

        # Run all detections concurrently
        tasks = [detect_on_endpoint(endpoint) for endpoint in network_endpoints]
        results = await asyncio.gather(*tasks)

        # Filter out Nones
        return [dev for dev in results if dev]


    def get_info(self) -> TransportProtocolInfo:
        """Get transport protocol metadata.
        
        Returns:
            TransportProtocolInfo containing:
            - transport: TransportType.TELNET
            - identifier: IP address (e.g., '192.168.1.100')
            - mac: MAC address if known (e.g., '00:80:A3:12:34:56')
        
        Example:
            >>> info = protocol.get_info()
            >>> print(f"Connected via {info.transport.name} to {info.identifier}")
            >>> if info.mac:
            ...     print(f"MAC: {info.mac}")
        """
        return TransportProtocolInfo(
            transport=TransportType.TELNET,
            identifier=self.__host,
            mac=self.__MAC
        )
    

    @property
    def is_connected(self) -> bool:
        """Check if Telnet connection is established.
        
        Returns:
            True if both reader and writer are active, False otherwise
        
        Note:
            This is a local check - does not verify network connectivity
            or device responsiveness
        """
        return self.__reader is not None and self.__writer is not None