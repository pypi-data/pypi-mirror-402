from .transport_protocol import TRANSPORT_REGISTRY, TransportProtocol
from .transport_types import DetectedDevice

class TransportFactory:
    """Internal factory for creating transport protocol instances.
    
    The TransportFactory provides a centralized mechanism for instantiating
    the appropriate transport protocol implementation based on either a
    TransportType enum or a DetectedDevice from discovery.
    
    Transport protocols register themselves in TRANSPORT_REGISTRY when their
    class is defined (via __init_subclass__), making them available to the
    factory without explicit registration code.
    
    Two creation patterns are supported:
    1. Direct creation from transport type and identifier
    2. Creation from a DetectedDevice object (from discovery)
    
    Example:
        >>> # Create serial transport directly
        >>> transport = TransportFactory.from_transport_type(
        ...     TransportType.SERIAL,
        ...     identifier='/dev/ttyUSB0'
        ... )
        >>> 
        >>> # Create from discovered device
        >>> devices = await DeviceDiscovery.discover_devices(...)
        >>> transport = TransportFactory.from_detected_device(devices[0])
    
    Note:
        - Transport implementations auto-register via TRANSPORT_TYPE class attribute
        - Factory uses TRANSPORT_REGISTRY populated by TransportProtocol.__init_subclass__
        - Created transports are not connected (call connect() after creation)
    """
    
    @staticmethod
    def from_detected_device(detected_device: DetectedDevice) -> "TransportProtocol":
        """Create a transport instance from a DetectedDevice discovery result.
        
        This convenience method extracts the transport type and identifier from
        a DetectedDevice object and creates the appropriate transport protocol
        instance. This is the typical pattern after device discovery.

        Args:
            detected_device: DetectedDevice object from discovery, containing:
                - transport: TransportType (SERIAL or TELNET)
                - identifier: Connection string (port name or IP address)
                - device_id: Identified device model
                - extended_info: Optional additional information

        Returns:
            TransportProtocol instance (SerialProtocol or TelnetProtocol)
            configured with the detected device's connection parameters.
            The transport is created but not connected.

        Raises:
            ValueError: If the detected device's transport type is not
                registered in TRANSPORT_REGISTRY (unknown transport type)

        Example:
            >>> # Typical discovery -> transport creation flow
            >>> discovered = await DeviceDiscovery.discover_devices(
            ...     flags=DiscoverFlags.ALL_INTERFACES
            ... )
            >>> 
            >>> # Create transport for first discovered device
            >>> transport = TransportFactory.from_detected_device(discovered[0])
            >>> await transport.connect()
            >>> 
            >>> # Or create device directly (uses factory internally)
            >>> device = DeviceFactory.from_detected_device(discovered[0])

        Note:
            - Typically used by DeviceFactory.from_detected_device()
            - Created transport is not connected
            - Validates transport type is supported
        """

        if detected_device.transport not in TRANSPORT_REGISTRY:
            raise ValueError(f"Unsupported transport type: {detected_device.transport}")

        return TRANSPORT_REGISTRY[detected_device.transport](detected_device.identifier)
    

    @staticmethod
    def from_transport_type(transport_type: str, identifier: str) -> "TransportProtocol":
        """Create a transport instance from type and identifier.
        
        Directly instantiates a transport protocol implementation based on the
        specified TransportType. This is used when creating devices manually
        without going through discovery.

        Args:
            transport_type: TransportType enum specifying protocol:
                - TransportType.SERIAL: Serial/USB connection
                - TransportType.TELNET: TCP/IP network connection
            identifier: Connection identifier specific to transport type:
                - Serial: Port name (e.g., 'COM3', '/dev/ttyUSB0')
                - Telnet: IP address or hostname (e.g., '192.168.1.100')

        Returns:
            TransportProtocol instance (SerialProtocol or TelnetProtocol)
            configured with the specified connection parameters.
            The transport is created but not connected.

        Raises:
            ValueError: If the transport_type is not registered in
                TRANSPORT_REGISTRY (unknown or unimplemented transport)

        Example:
            >>> # Create serial transport
            >>> transport = TransportFactory.from_transport_type(
            ...     TransportType.SERIAL,
            ...     identifier='/dev/ttyUSB0'
            ... )
            >>> await transport.connect()
            >>> 
            >>> # Create network transport
            >>> transport = TransportFactory.from_transport_type(
            ...     TransportType.TELNET,
            ...     identifier='192.168.1.100'
            ... )
            >>> await transport.connect()
            >>> 
            >>> # Typically used internally by PiezoDevice.__init__
            >>> device = DDriveDevice(
            ...     transport_type=TransportType.SERIAL,
            ...     identifier='COM3'
            ... )
            >>> # Device uses factory to create transport internally

        Note:
            - Used internally by PiezoDevice class during initialization
            - Created transport is not connected
            - Must call connect() before using transport
            - Validates transport type is registered and available
        """

        if transport_type not in TRANSPORT_REGISTRY:
            raise ValueError(f"Unsupported transport type: {transport_type}")

        return TRANSPORT_REGISTRY[transport_type](identifier)