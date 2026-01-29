"""Base classes for piezoelectric device communication and control.

This module provides the generic PiezoDevice base class that handles low-level
communication, command caching, synchronization, and channel management for
piezoelectric amplifiers and controllers.

The PiezoDevice class is designed to be subclassed by device-specific
implementations (e.g., d-Drive, NV200) which define their specific command
sets, capabilities, and behaviors.

Key Features:
    - Async command execution with automatic response parsing
    - Optional command caching to reduce communication overhead  
    - Reentrant async locking for thread-safe access
    - Multi-channel device support
    - Backup/restore of device configurations
"""

import logging
from typing import Awaitable, Self, Type

from ..._internal._reentrant_lock import _ReentrantAsyncLock
from ..transport_protocol import (
    DeviceDiscovery,
    DeviceUnavailableException,
    DiscoverFlags,
    TransportFactory,
    TransportProtocol,
    TransportType,
)
from .command_cache import CommandCache
from .device_factory import DeviceFactory, DEVICE_MODEL_REGISTRY
from .exceptions import ErrorCode
from .piezo_channel import PiezoChannel
from .piezo_types import DeviceInfo

# Global module locker
logger = logging.getLogger(__name__)


class PiezoDevice:
    """Generic base class for piezoelectric amplifier and controller devices.

    PiezoDevice provides a comprehensive async interface for communicating with
    piezoelectric devices over various transport protocols (serial or Telnet).
    It encapsulates low-level device commands, response parsing, synchronization,
    and optional result caching.

    This class is designed to be subclassed by concrete device implementations
    (e.g., DDriveDevice, NV200Device) which define specific command sets,
    capabilities, and channel configurations.

    Command Caching:
        PiezoDevice supports intelligent caching of command parameters/values to
        reduce latency from frequent read operations. Each read over serial/Telnet
        can add several milliseconds of latency, so caching significantly improves performance
        for applications that repeatedly query device state (e.g., GUI monitoring).
        
        Caching behavior:
        - Only commands in CACHEABLE_COMMANDS set are cached
        - Cache is automatically invalidated on write operations
        - Enable/disable per-instance via enable_cmd_cache() method
    
    Thread Safety:
        All device operations use a reentrant async lock, ensuring safe concurrent
        access from multiple async tasks or threads. Use `async with device.lock:`
        to group multiple operations atomically.

    Multi-Channel Support:
        Devices with multiple actuator channels expose them via the `channels`
        property. Each channel can be controlled independently.

    Important:
        Caching should ONLY be used when the device has exclusive access (no other
        applications modifying device state). If multiple applications can access
        the device (e.g., both serial and Telnet), disable caching to prevent stale
        data issues (e.g. by calling enable_cmd_cache(False)).

    Class Attributes:
        DEVICE_ID (str | None): Unique identifier for this device model. Subclasses
            must set this to auto-register with the DeviceFactory.
        CACHEABLE_COMMANDS (set[str]): Commands whose results can be cached.
        BACKUP_COMMANDS (set[str]): Commands to include in device backup operations.
        DEFAULT_TIMEOUT_SECS (float): Default timeout for command operations (0.6s).
        FRAME_DELIMITER_WRITE (bytes): Byte sequence appended to commands (default: CRLF).
        FRAME_DELIMITER_READ (bytes): Byte sequence expected at end of responses (default: CRLF).

    Instance Attributes:
        _transport: TransportProtocol instance handling low-level communication
        _cache: CommandCache instance for caching read operations
        _lock: Reentrant async lock for thread-safe access
        _channels: Dictionary mapping channel IDs to PiezoChannel instances

    Example:
        >>> # Discover and connect to a device
        >>> devices = await PiezoDevice.discover_devices()
        >>> device = devices[0]
        >>> await device.connect()
        >>> 
        >>> # Access device information
        >>> info = device.device_info
        >>> print(f"Device: {info.device_id} on {info.transport_info.identifier}")
        >>> 
        >>> # Execute commands with caching
        >>> voltage = await device.write('voltage', None)  # Read (cached)
        >>> await device.write('voltage', [10.5])  # Write (invalidates cache)
        >>> 
        >>> # Thread-safe grouped operations
        >>> async with device.lock:
        ...     await device.write('cmd1', [100])
        ...     await device.write('cmd2', [200])
        >>> 
        >>> # Backup and restore configuration
        >>> backup = await device.backup(['voltage', 'frequency'])
        >>> # ... change settings ...
        >>> await device.restore(backup)
        >>> 
        >>> # Clean shutdown
        >>> await device.close()
    
    Note:
        Subclasses must implement:
        - _discover_channels(): Initialize the _channels dictionary
        - _is_device_type(): Verify connected device matches expected type
        - Set DEVICE_ID to a unique string for factory registration
    """
    DEVICE_ID = None  # Placeholder for device ID, to be set in subclasses

    CACHEABLE_COMMANDS: set[str] = set()  # set of commands that can be cached
    BACKUP_COMMANDS: set[str] = set()  # set of commands to backup device settings

    DEFAULT_TIMEOUT_SECS = 0.6
    FRAME_DELIMITER_WRITE = TransportProtocol.CRLF  # Default frame delimiter for writing commands
    FRAME_DELIMITER_READ = TransportProtocol.CRLF

    _channels: dict[int, PiezoChannel] = {}  # Dictionary to store channels by their number


    def __init__(
        self,
        transport_type: TransportType,
        identifier: str
    ):
        """Initialize a piezo device with the specified transport connection.
        
        Creates a new device instance configured to communicate via the specified
        transport protocol. The device is not connected until connect() is called.
        
        Args:
            transport_type: Communication protocol to use (SERIAL or TELNET).
                SERIAL: Direct connection via RS-232, USB-serial adapter
                TELNET: Network connection via TCP/IP (typically using Lantronix adapter)
            identifier: Connection identifier specific to the transport type:
                For SERIAL: Port name (e.g., 'COM3', '/dev/ttyUSB0')
                For TELNET: IP address or hostname (e.g., '192.168.1.100')
        
        Example:
            >>> # Create device with serial connection
            >>> device = DDriveDevice(
            ...     transport_type=TransportType.SERIAL,
            ...     identifier='/dev/ttyUSB0'
            ... )
            >>> 
            >>> # Create device with Telnet connection
            >>> device = DDriveDevice(
            ...     transport_type=TransportType.TELNET,
            ...     identifier='192.168.1.100'
            ... )
            >>> 
            >>> # Must call connect() before using
            >>> await device.connect()
        
        Note:
            The device is not connected after initialization. Call connect()
            to establish communication before issuing commands.
        """
        # Initialize transport
        self._transport: TransportProtocol = TransportFactory.from_transport_type(
            transport_type,
            identifier
        )

        self._cache: CommandCache = CommandCache(self.CACHEABLE_COMMANDS)
        self._lock = _ReentrantAsyncLock()
        self._transport.rx_delimiter = self.FRAME_DELIMITER_READ

    def __init_subclass__(cls, **kwargs):
        super().__init_subclass__(**kwargs)
        cls._register_device_class(cls)
        cls._register_descendant_devices(cls)

    @staticmethod
    def _register_device_class(device_cls: type["PiezoDevice"]) -> None:
        if device_cls.DEVICE_ID:
            DEVICE_MODEL_REGISTRY[device_cls.DEVICE_ID] = device_cls

    @classmethod
    def _register_descendant_devices(cls, base_cls: type["PiezoDevice"]) -> None:
        for subclass in base_cls.__subclasses__():
            cls._register_device_class(subclass)
            cls._register_descendant_devices(subclass)


    @classmethod
    async def discover_devices(cls, flags: DiscoverFlags = DiscoverFlags.ALL_INTERFACES) -> list[Self]:
        """Discover and create instances of devices accessible via available transports.

        This class method scans for devices using the specified discovery flags,
        identifies devices matching the class's DEVICE_ID, and returns a list of
        ready-to-connect device instances.
        
        The discovery process:
        1. Scans serial ports and/or network interfaces based on flags
        2. Attempts basic communication to identify device type
        3. Filters for devices matching this class's DEVICE_ID (if defined)
        4. Creates appropriate device instances via DeviceFactory

        Args:
            flags: Discovery scope controlling which interfaces to scan.
                DiscoverFlags.ALL_INTERFACES: Scan both serial and network
                DiscoverFlags.SERIAL_ONLY: Scan only serial/USB ports
                DiscoverFlags.TELNET_ONLY: Scan only network interfaces
                Default: ALL_INTERFACES

        Returns:
            List of device instances found during discovery. Each device is
            created but not connected (call connect() on each device to establish
            communication).

        Example:
            >>> # Discover all available devices
            >>> devices = await DDriveDevice.discover_devices()
            >>> print(f"Found {len(devices)} devices")
            >>> 
            >>> # Discover only network-connected devices
            >>> network_devices = await DDriveDevice.discover_devices(
            ...     flags=DiscoverFlags.TELNET_ONLY
            ... )
            >>> 
            >>> # Connect to first discovered device
            >>> if devices:
            ...     await devices[0].connect()
        
        Note:
            - Base PiezoDevice class discovers all registered device types
            - Subclasses only discover devices matching their DEVICE_ID
            - Discovery can take several seconds, especially for network scanning
            - Devices must be powered on and properly connected to be discovered
        """
        discovered_devices = await DeviceDiscovery.discover_devices(cls._is_device_type, flags)
        devices = []

        for device in discovered_devices:
            devices.append(DeviceFactory.from_detected_device(device))

        return devices


    @classmethod
    async def _is_device_type(cls, tp: TransportProtocol) -> str | None:
        """Check if the device on the transport matches this device class type.
        
        This internal method is called during device discovery to verify that a
        detected device matches the expected device type. The base implementation
        checks all registered subclasses if DEVICE_ID is None (discovery of any
        device type).
        
        Subclasses should override this method to implement device-specific
        identification logic, typically by:
        1. Sending an identification command (e.g., 'identify', 'version')
        2. Parsing the response
        3. Comparing against expected device ID or version string

        Args:
            tp: TransportProtocol instance with an open connection to the device

        Returns:
            Device ID string if the device matches this class type, None otherwise.
        
        Example (subclass implementation):
            >>> @classmethod
            >>> async def _is_device_type(cls, tp: TransportProtocol) -> str | None:
            ...     await tp.write('identify' + tp.CRLF)
            ...     response = await tp.read_message()
            ...     return cls.DEVICE_ID if cls.DEVICE_ID in response else None
        
        Note:
            - Base class checks all registered subclasses if DEVICE_ID is None
            - Called during discovery with temporary transport connections
            - Should be fast to avoid slowing down discovery process
            - Should handle communication errors gracefully (return False)
        """
        if cls.DEVICE_ID is None:
            for subclass in DEVICE_MODEL_REGISTRY.values():
                id = await subclass._is_device_type(tp)
                if id is not None:
                    return id

            return None

    @property
    def lock(self) -> _ReentrantAsyncLock:
        """Reentrant async lock for thread-safe device access.
        
        This lock ensures that device operations are atomic and thread-safe when
        multiple async tasks or threads access the device concurrently. The lock
        is reentrant, meaning the same task can acquire it multiple times.
        
        All internal write/read operations automatically use this lock. Use it
        explicitly when you need to group multiple operations atomically.

        Returns:
            Reentrant async context manager lock
        
        Example:
            >>> # Atomic multi-command sequence
            >>> async with device.lock:
            ...     await device.write('mode', [1])  # Switch to mode 1
            ...     await device.write('voltage', [10.0])  # Set voltage
            ...     await device.write('enable', [True])  # Enable output
            >>> 
            >>> # Guarantees no other task can execute commands between these
        
        Note:
            - Lock is automatically used by write(), write_raw(), and other methods
            - Explicit locking is only needed for grouping multiple operations
            - Lock is reentrant: nested acquisitions from same task are allowed
            - Always use with async context manager (async with)
        """
        return self._lock


    @property
    def device_info(self) -> DeviceInfo:
        """Get comprehensive information about the connected device.

        Provides a DeviceInfo object containing the device's model identifier
        and transport connection details. This property is useful for logging,
        diagnostics, and displaying device information in user interfaces.

        Returns:
            DeviceInfo object containing:
                - device_id: Model identifier (e.g., 'd-drive', 'nv200')
                - transport_info: TransportProtocolInfo with connection details
                    (transport type, identifier, etc.)

        Raises:
            DeviceUnavailableException: If the transport is not initialized or
                the device is not connected. Call connect() before accessing.

        Example:
            >>> await device.connect()
            >>> info = device.device_info
            >>> print(f"Connected to {info.device_id}")
            >>> print(f"  Transport: {info.transport_info.transport_type.name}")
            >>> print(f"  Identifier: {info.transport_info.identifier}")
            >>> 
            >>> # Example output:
            >>> # Connected to d-drive
            >>> #   Transport: SERIAL
            >>> #   Identifier: COM3
        
        Note:
            Device must be connected before accessing this property. The device_id
            comes from the class's DEVICE_ID attribute, while transport_info is
            provided by the active transport protocol.
        """
        if self._transport is None:
            raise DeviceUnavailableException("Cannot access device_info: transport is not initialized or device is not connected.")

        return DeviceInfo(
            device_id=self.DEVICE_ID,
            transport_info=self._transport.get_info()
        )

    @property
    def channels(self) -> dict[int, PiezoChannel]:
        """Get dictionary of available device channels.

        Multi-channel devices expose their channels through this property,
        allowing independent control of each actuator output. Channel IDs
        are typically 0-based integers (0, 1, 2, etc.).

        Returns:
            Dictionary mapping channel IDs (int) to PiezoChannel instances.
            Returns empty dict before channels are discovered during connect().

        Example:
            >>> await device.connect()  # Discovers channels
            >>> 
            >>> # Access specific channel
            >>> channel_0 = device.channels[0]
            >>> print(f"Channel ID: {channel_0.id}")
            >>> 
            >>> # Iterate all channels
            >>> for ch_id, channel in device.channels.items():
            ...     print(f"Channel {ch_id}: {channel}")
            >>> 
            >>> # Check number of channels
            >>> num_channels = len(device.channels)
            >>> print(f"Device has {num_channels} channels")
        
        Note:
            - Channels are populated during connect() via _discover_channels()
            - Single-channel devices may only have one channel (ID 0)
            - Channel objects provide access to channel-specific capabilities
            - Each channel can be controlled independently
        """
        return self._channels
    

    def _parse_response(self, response: str) -> list[str]:
        """Parse device response and extract parameter values.
        
        This internal method processes raw device responses, checks for error
        conditions, and extracts parameter values. Device responses typically
        have the format: "command,param1,param2,..." or "error,code".
        
        Error Handling:
            If the response starts with "error", raises the appropriate DeviceError
            exception based on the error code. See ErrorCode enum for all possible
            error types.

        Args:
            response: Raw response string from the device

        Returns:
            List of parameter strings from the response (command name is stripped).
            Returns empty list if no parameters were included in the response.

        Raises:
            DeviceError: If the response indicates an error condition. Specific
                exception type depends on the error code (see exceptions.py).
        
        Example:
            >>> # Successful response with parameters
            >>> result = self._parse_response("voltage,10.5,V")
            >>> # result = ['10.5', 'V']
            >>> 
            >>> # Error response
            >>> result = self._parse_response("error,2")
            >>> # Raises UnknownCommand exception
        
        Note:
            - Internal method for use by write operations
            - Trailing whitespace and control characters are stripped from parameters
            - Error responses halt execution by raising exceptions
        """
        # Check if the response indicates an error
        if response.startswith("error"):
            self._raise_error(response)
            return  # This line will never be reached due to the exception being raised
            
        # Else, Normal response, split the command and parameters
        parts = response.split(',', 1)
        parameters = []

        if len(parts) > 1:
            parameters = [param.strip("\x01\n\r\x00") for param in parts[1].split(',')]

        return parameters
    

    def _raise_error(self, response: str):
        """Parse error response and raise appropriate DeviceError exception.
        
        This internal method extracts the error code from a device error response
        and raises the corresponding typed exception. Error responses have the
        format: "error,code" where code is an integer.

        Args:
            response: Error response string from device (e.g., "error,2")

        Raises:
            DeviceError: Specific subclass based on error code:
                - ErrorNotSpecified: Code 1 or invalid/missing code
                - UnknownCommand: Code 2
                - ParameterMissing: Code 3
                - AdmissibleParameterRangeExceeded: Code 4
                - CommandParameterCountExceeded: Code 5
                - ParameterLockedOrReadOnly: Code 6
                - Underload: Code 7
                - Overload: Code 8
                - ParameterTooLow: Code 9
                - ParameterTooHigh: Code 10
        
        Note:
            - Internal method called by _parse_response when errors detected
            - Always raises an exception (never returns normally)
            - Malformed error responses default to ErrorNotSpecified
        """
        parts = response.split(',', 1)
        
        # Check if error code is present
        if len(parts) < 2:
            ErrorCode.raise_error(ErrorCode.ERROR_NOT_SPECIFIED)  # Default error: Error not specified
            return

        # Try to parse the error code
        try:
            error_code = int(parts[1].strip("\x01\n\r\x00"))

            # Raise a DeviceError with the error code
            ErrorCode.raise_error(error_code)
            return
        except ValueError:
            # In case the error code isn't valid
            ErrorCode.raise_error(ErrorCode.ERROR_NOT_SPECIFIED)  # Default error: Error not specified
            return
        

    async def _discover_channels(self):
        """Discover and initialize device channels.

        This abstract method must be implemented by subclasses to detect and
        create PiezoChannel instances for the device. It is called automatically
        during connect() after device type verification.
        
        Subclasses should:
        1. Query the device to determine number of available channels
        2. Create PiezoChannel (or subclass) instances for each channel
        3. Populate the _channels dictionary with channel_id -> channel mapping
        4. (Optional) Initialize channel-specific capabilities

        Raises:
            NotImplementedError: If called on base class without subclass override
        
        Example (subclass implementation):
            >>> async def _discover_channels(self):
            ...     # Query device for channel count
            ...     response = await self.write('numchannels', None)
            ...     num_channels = int(response[0])
            ...     
            ...     # Create channel instances
            ...     for ch_id in range(num_channels):
            ...         self._channels[ch_id] = DDriveChannel(
            ...             channel_id=ch_id,
            ...             write_cb=self._write_channel
            ...         )
        
        Note:
            - Called automatically during connect(), not by user code
            - Subclasses can query device for dynamic channel configuration
            - Some devices may have fixed channel counts
        """
        raise NotImplementedError("Channel discovery must be implemented in subclasses.")
    

    async def _write_channel(
        self,
        channel_id: int | None,
        cmd: str,
        params: list[int | float | str | bool] | None = None
    ) -> list[str]:
        """Internal method to write a command to a specific channel.
        
        This helper method constructs a channel-specific command by appending
        the channel ID to the command string, then delegates to the main write()
        method. It's used as the write callback for PiezoChannel instances.

        Args:
            channel_id: Numeric ID of the target channel (typically 0-based) or None for single-channel devices
            cmd: Command name to send
            params: Optional list of parameters for the command. None for read operations.

        Returns:
            Device response as a list of string values
        
        Example:
            >>> # Called internally by channel objects:
            >>> result = await self._write_channel(0, 'voltage', [10.5])
            >>> # Sends: "voltage,0,10.5" to device
        
        Note:
            - Internal method used by PiezoChannel write callback
            - Automatically formats command with channel ID
            - Command format: "command,channel_id[,param1,param2,...]"
        """
        cmd_list = cmd.split(",")
        full_cmd = f"{cmd_list[0]},{channel_id}" if channel_id is not None else cmd_list[0]

        # If channel command has additional parts after comma, append them as parameters
        if len(cmd_list) > 1:
            params = cmd_list[1:] + (params if params is not None else [])

        response = await self.write(full_cmd, params)

        # Strip channel ID (first param) from response
        if channel_id is not None and len(response) > 0:
            return response[1:]
        
        # If no channel ID, return full response
        return response

    async def _capability_write(
        self,
        device_commands: dict[str, str],
        cmd: str,
        params: list[int | float | str | bool]
    ):
        """Write method for capabilities with command name validation.
        
        This helper method is used by capability implementations to send commands
        with validation against the device's supported command set. Capabilities
        can remain device-agnostic by using generic command names that are mapped
        to actual device commands via the device_commands dictionary.

        Args:
            device_commands: Dictionary mapping generic capability command names
                to device-specific command strings
            cmd: Generic command name from capability
            params: List of parameters for the command

        Returns:
            Device response as list of strings, or None if command not supported
        
        Example:
            >>> # In a capability implementation:
            >>> commands = {'set_voltage': 'xsvoltage', 'get_voltage': 'xgvoltage'}
            >>> result = await self._capability_write(commands, 'set_voltage', [10.0])
        
        Note:
            - Logs warning if command not found in device_commands dictionary
            - Returns None instead of raising exception for unsupported commands
            - Allows capabilities to gracefully handle device capability differences
        """
        # Check if command can be found in cmd dictionary
        if cmd not in device_commands:
            logger.warning(f"Capability requested to send unknown command: {cmd}.")
            return
        
        return await self.write(device_commands[cmd], params)
    

    async def connect(self, auto_adjust_comm_params: bool = True):
        """Establish connection to the device and initialize channels.

        This method connects to the device via the transport layer, verifies
        the device type matches expectations, and discovers available channels.
        After successful connection, the device is ready for command execution.
        
        Connection Process:
        1. Check if already connected (skip if yes)
        2. Establish transport-layer connection
        3. Auto-adjust communication parameters if enabled (Telnet only)
        4. Verify device type matches expected DEVICE_ID
        5. Discover and initialize device channels

        Args:
            auto_adjust_comm_params: For Telnet connections only, automatically
                configure the internal Lantronix XPORT ethernet module for communication. 
                Sets flow control to XON_XOFF_PASS_TO_HOST mode,
                which is required for library to function correctly.
                Default: True (recommended)
                
                Set to False only if:
                - Using serial connection (parameter is ignored)
                - XPORT is already properly configured
                - Manual configuration is preferred

        Raises:
            DeviceUnavailableException: If:
                - Transport is not initialized
                - Connection to device fails
                - Device type verification fails (wrong device connected)
            TransportException: If transport-specific connection errors occur

        Example:
            >>> # Standard connection (recommended)
            >>> device = DDriveDevice(TransportType.SERIAL, 'COM3')
            >>> await device.connect()
            >>> 
            >>> # Connect without auto-configuration
            >>> device = DDriveDevice(TransportType.TELNET, '192.168.1.100')
            >>> await device.connect(auto_adjust_comm_params=False)
            >>> 
            >>> # Verify connection
            >>> info = device.device_info
            >>> print(f"Connected to {info.device_id}")

        Note:
            - Safe to call multiple times (idempotent if already connected)
            - Device type mismatch causes connection to be closed
            - Must be called before any device commands
            - Channels are not available until connection completes
        """
        if self._transport is None:
            raise DeviceUnavailableException("Cannot connect: transport is not initialized.")

        if self._transport.is_connected:
            logger.debug("Device is already connected.")
            return

        await self._transport.connect(auto_adjust_comm_params=auto_adjust_comm_params)
        is_match = await self._is_device_type(self._transport)
        
        if not is_match:
            await self._transport.close()
            raise DeviceUnavailableException(
                f"Device type mismatch. Expected device ID: {self.DEVICE_ID}. "
                "Please check the device connection and ensure the correct device is connected."
            )
        
        await self._discover_channels()

    async def _write_and_parse(
        self,
        cmd: str,
        timeout: float = DEFAULT_TIMEOUT_SECS
    ) -> list[str]:
        response = await self.write_raw(cmd, timeout=timeout)
        return self._parse_response(response)

    async def _read_with_cache(
        self,
        cmd: str,
        timeout: float = DEFAULT_TIMEOUT_SECS
    ) -> list[str]:
        values = self._cache.get(cmd)

        if values is not None:
            return values

        logger.debug("Reading string values for command: %s", cmd)

        values = await self._write_and_parse(cmd, timeout=timeout)

        for i in range(len(values)):
            values[i] = values[i].rstrip()  # strip trailing whitespace - some strings like units may contain trailing spaces

        self._cache.set(cmd, values)
        
        return values
    
    async def _write_with_cache(
        self,
        cmd: str,
        values: list[int | float | str | bool],
        timeout: float = DEFAULT_TIMEOUT_SECS
    ) -> list[str]:
        str_values = []

        # Convert all values to strings, handling booleans as integers
        for value in values:
            if isinstance(value, bool):
                str_values.append(str(int(value)))
            else:
                str_values.append(str(value))

        response = await self._write_and_parse(f"{cmd},{','.join(str_values)}", timeout=timeout)

        self._cache.invalidate(cmd)

        return response
    

    async def write(
        self,
        cmd: str,
        params: list[int | float | str | bool] | None = None,
        timeout: float = DEFAULT_TIMEOUT_SECS
    ) -> list[str]:
        """Execute a device command with optional parameters and caching.
        
        This is the primary method for device interaction. It automatically handles:
        - Read vs write operations (based on params being None or not)
        - Command result caching for read operations
        - Cache invalidation for write operations  
        - Parameter type conversion (bool -> int, all -> str)
        - Response parsing and error handling
        
        Read Operation (params=None):
            - Checks cache first, returns cached value if available
            - If cache miss, sends command to device
            - Caches result if command is cacheable
            - Returns response parameter values
        
        Write Operation (params provided):
            - Converts parameters to proper string format
            - Sends command with parameters to device
            - Caches written values if command is cacheable
            - Returns device response

        Args:
            cmd: Command name to execute (e.g., 'voltage', 'position', 'identify')
            params: Parameters for the command. Pass None for read operations,
                list of values for write operations. Boolean values are automatically
                converted to integers (True=1, False=0).
            timeout: Maximum time to wait for device response in seconds.
                Default: 0.6 seconds

        Returns:
            List of response strings from the device. The command name is stripped,
            only parameter values are returned.

        Raises:
            DeviceUnavailableException: If device is not connected or transport fails
            DeviceError: If device returns an error response (see exceptions.py)
            TimeoutException: If device does not respond within timeout period

        Example:
            >>> # Read operation (returns cached value if available)
            >>> voltage = await device.write('voltage', None)
            >>> print(f"Voltage: {voltage[0]} {voltage[1]}")  # ['10.5', 'V']
            >>> 
            >>> # Write operation (invalidates cache)
            >>> await device.write('voltage', [12.5])
            >>> 
            >>> # Boolean parameters (converted to 0/1)
            >>> await device.write('enable', [True])  # Sends 'enable,1'
            >>> 
            >>> # Multiple parameters
            >>> await device.write('pid', [5.0, 0.1, 0.2])  # P, I, D values
            >>> 
            >>> # Custom timeout for slow operations
            >>> result = await device.write('calibrate', None, timeout=5.0)

        Note:
            - Caching only applies to commands in CACHEABLE_COMMANDS set
            - Cache is automatically invalidated on write operations
            - All operations use the device's reentrant lock for thread safety
            - Boolean parameters: True becomes '1', False becomes '0'
        """
        # If params is None, perform a read operation
        if params is None:
            return await self._read_with_cache(cmd, timeout=timeout)
        
        # Else, perform a write operation
        return await self._write_with_cache(cmd, params, timeout=timeout)
        
        
    async def write_raw(
        self,
        cmd: str,
        timeout: float = DEFAULT_TIMEOUT_SECS,
        rx_delimiter: bytes = FRAME_DELIMITER_READ
    ) -> Awaitable[str]:
        """Send a raw command string and return unparsed device response.
        
        This low-level method sends a command directly to the device without:
        - Parameter formatting or conversion
        - Response parsing or error checking
        - Caching of any kind
        
        Use this method when you need direct access to raw device responses,
        such as during device identification, debugging, or when implementing
        new command support.
        
        The method automatically:
        - Adds the appropriate frame delimiter (CRLF by default)
        - Uses the device lock for thread safety
        - Waits for complete device response with timeout

        Args:
            cmd: Complete command string to send (e.g., 'identify' or 'voltage,0,10.5').
                Frame delimiters are added automatically.
            timeout: Maximum time to wait for device response in seconds.
                Default: 0.6 seconds
            rx_delimiter: Optional custom receive delimiter bytes.
                Default: Device configured FRAME_DELIMITER_READ

        Returns:
            Raw response string from device including any delimiters or control characters

        Raises:
            DeviceUnavailableException: If device is not connected or transport error occurs
            TimeoutException: If device does not respond within timeout period

        Example:
            >>> # Send raw identification command
            >>> response = await device.write_raw('identify')
            >>> print(f"Raw response: {repr(response)}")
            >>> # Raw response: 'identify,d-drive,v1.2.3\r\n'
            >>> 
            >>> # Debugging - see exact device response
            >>> raw = await device.write_raw('voltage,0')
            >>> print(f"Response bytes: {raw.encode()}")

        Note:
            - Prefer write() method for normal operations
            - No error checking is performed on responses
            - Response must be manually parsed
            - Useful for device discovery and debugging
            - Thread-safe via automatic lock acquisition
        """
        logger.debug("Writing cmd.: %s", cmd)
        response = None

        if self._transport is None or not self._transport.is_connected:
            raise DeviceUnavailableException("Cannot write to device: transport is not initialized or device is not connected.")

        async with self.lock:
            try:
                await self._transport.write(cmd + self.FRAME_DELIMITER_WRITE.decode("utf-8"))
                response = await self._transport.read_until(expected=rx_delimiter, timeout=timeout)
            except Exception as e:
                raise DeviceUnavailableException(f"Failed to write/read from device: {repr(e)}") from e

        return response


    async def close(self):
        """Close the connection to the device and release resources.

        This method properly shuts down the transport connection and releases
        any associated resources (serial ports, network sockets, etc.). Always
        call this when finished with the device to prevent resource leaks.
        
        The method is idempotent - it's safe to call multiple times or on
        an already-closed connection.

        Raises:
            Exception: May propagate transport-specific exceptions if close fails

        Example:
            >>> device = await DDriveDevice.connect(TransportType.SERIAL, 'COM3')
            >>> try:
            ...     await device.write('voltage', [10.0])
            ... finally:
            ...     await device.close()  # Always close in finally block
            >>> 
            >>> # Or use async context manager (preferred)
            >>> async with DDriveDevice(...) as device:
            ...     await device.connect()
            ...     await device.write('voltage', [10.0])
            >>> # Automatically closed on exit

        Note:
            - Safe to call on already-closed or non-initialized transport
            - Logs debug message if already closed
            - Recommended to use in finally block or async context manager
            - Automatically clears command cache on close
        """
        if self._transport is None or not self._transport.is_connected:
            logger.debug("Transport is already closed or not initialized.")
            return

        await self._transport.close()
        self.clear_cmd_cache()

    
    def clear_cmd_cache(self):
        """Clear all cached command results.
        
        Removes all entries from the command cache, forcing subsequent read
        operations to query the device hardware. Use this when:
        - Device state may have changed externally
        - Recovering from errors
        - Switching operation modes
        - Debugging cache-related issues

        Example:
            >>> # After external device modification
            >>> device.clear_cmd_cache()
            >>> voltage = await device.write('voltage', None)  # Fresh read
            >>> 
            >>> # In error recovery
            >>> try:
            ...     await device.write('something', [val])
            ... except DeviceError:
            ...     device.clear_cmd_cache()  # Start fresh

        Note:
            - Does not disable caching, only clears current entries
            - Next read operations will rebuild cache as normal
            - To disable caching entirely, use enable_cmd_cache(False)
        """
        self._cache.clear()
        logger.debug("Command cache cleared.")

    def enable_cmd_cache(self, enable: bool):
        """Enable or disable command caching for this device instance.
        
        Controls whether command results are cached. Disabling cache also
        automatically clears all cached entries.

        Args:
            enable: True to enable caching, False to disable and clear cache

        Example:
            >>> # Disable caching for debugging
            >>> device.enable_cmd_cache(False)
            >>> voltage = await device.write('voltage', None)  # Always fresh
            >>> 
            >>> # Re-enable for better performance
            >>> device.enable_cmd_cache(True)
            >>> 
            >>> # Temporarily disable for critical operations
            >>> device.enable_cmd_cache(False)
            >>> await perform_calibration()
            >>> device.enable_cmd_cache(True)

        Note:
            - Disabling cache automatically clears all cached values
            - Setting to False is important when other apps access device
            - Per-instance setting (doesn't affect other device instances)
            - See CommandCache class for detailed caching behavior
        """
        self._cache.enabled = enable
        logger.debug(f"Command cache enabled: {enable}")

    async def backup(
        self, 
        backup_list: list[str] | None = None, 
        backup_channels: bool = True
    ) -> dict[str, str]:
        """Create a backup of device and channel settings.
        
        Reads and stores current values of specified commands and all channel
        settings. The backup can later be restored using restore() method.
        Cache is automatically cleared before backup to ensure fresh values.
        
        The backup includes:
        1. All channel-specific settings (from each channel's BACKUP_COMMANDS)
        2. Device-level commands specified in backup_list

        Args:
            backup_list: List of device-level command names to backup.
                If None, the default BACKUP_COMMANDS list of the device is used.
                Example: ['modsrc', 'notchon', 'sr', 'reclen']
            backup_channels: If True, backs up all channel settings automatically. (Default: True)

        Returns:
            Dictionary mapping command strings to their response values.
            Channel commands are formatted as 'command,channel_id'.
            Can be passed to restore() to recreate this configuration.

        Example:
            >>> # Backup specific device settings
            >>> backup = await device.backup(['voltage', 'frequency', 'mode'])
            >>> 
            >>> # Make changes
            >>> await device.write('voltage', [15.0])
            >>> await device.write('mode', [2])
            >>> 
            >>> # Restore original settings
            >>> await device.restore(backup)
            >>> 
            >>> # Backup includes all channels automatically
            >>> backup = await device.backup(['global_setting'])
            >>> # backup contains: {'voltage,0': ['10.0'], 'voltage,1': ['12.0'], ...}

        Note:
            - Cache is cleared before backup to ensure fresh values
            - Channel settings are backed up automatically
            - Backup format matches restore() input requirements
        """
        backup: dict[str, list[str]] = {}

        if backup_list is None:
            backup_list = self.BACKUP_COMMANDS

        # Invalidate cache to make sure we read fresh values
        self.clear_cmd_cache()

        # Go through every command in the backup list and read its value
        for cmd in backup_list:
            backup[cmd] = await self.write(cmd)

        if not backup_channels:
            return backup

        # Backup every channel
        for channel in self._channels.values():
            channel_backup = await channel.backup()

            for cmd, values in channel_backup.items():
                backup[f"{cmd},{channel.id}"] = values


        return backup

    async def restore(self, backup: dict[str, list[str]]):
        """Restore device settings from a backup created with backup().
        
        Iterates through the backup dictionary and writes each command with
        its saved values back to the device. This restores both device-level
        and channel-specific settings.

        Args:
            backup: Dictionary created by backup() method, mapping command
                strings to their parameter value lists.

        Raises:
            DeviceError: If any command in the backup fails to restore
                (e.g., parameter out of range, read-only parameter)

        Example:
            >>> # Create backup before experiment
            >>> backup = await device.backup(['voltage', 'frequency'])
            >>> 
            >>> # Run experiment with different settings
            >>> await device.write('voltage', [20.0])
            >>> await device.write('frequency', [100])
            >>> # ... perform measurements ...
            >>> 
            >>> # Restore original configuration
            >>> await device.restore(backup)
            >>> 
            >>> # All settings now back to original values
            >>> voltage = await device.write('voltage', None)
            >>> # voltage matches original backed-up value

        Note:
            - Commands are restored in dictionary iteration order
            - If a command fails, the exception propagates immediately
            - Works with backups containing both device and channel commands
        """
        for cmd, values in backup.items():
            await self.write(cmd, values)

    async def __aenter__(self) -> Self:
        """Async context manager entry - connects and returns the device instance.
        
        Allows using the device with async context manager syntax for
        automatic connection and resource cleanup. The device is automatically
        connected when entering the context.

        Returns:
            The connected device instance (self)

        Raises:
            DeviceUnavailableException: If connection fails or device type mismatch
            TransportException: If transport-specific connection errors occur

        Example:
            >>> async with DDriveDevice(TransportType.SERIAL, 'COM3') as device:
            ...     await device.write('voltage', [10.0])
            >>> # Automatically closed on exit
        
        Note:
            - Automatically calls connect() with default parameters
            - Device is closed automatically on context exit
            - Exceptions during connection propagate normally
        """
        await self.connect()
        return self

    async def __aexit__(self, exc_type, exc_val, exc_tb):
        """Async context manager exit - closes device connection.
        
        Automatically called when exiting the async context manager block.
        Ensures proper cleanup of device resources even if exceptions occur.

        Args:
            exc_type: Exception type if an exception occurred, None otherwise
            exc_val: Exception value if an exception occurred, None otherwise
            exc_tb: Exception traceback if an exception occurred, None otherwise

        Returns:
            False to allow exceptions to propagate (not suppressed)
        
        Note:
            - Always closes device connection
            - Does not suppress exceptions (returns False)
            - Safe to call even if already closed
        """
        await self.close()
        return False
    