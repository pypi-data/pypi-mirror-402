from typing import TYPE_CHECKING

from ..transport_protocol import DetectedDevice

if TYPE_CHECKING:
    from .piezo_device import PiezoDevice

# Device model registry
DEVICE_MODEL_REGISTRY: dict[str, type["PiezoDevice"]] = {}

class DeviceFactory:
    """Internal factory class for creating device instances from device identifiers.
    
    The DeviceFactory provides a centralized mechanism for instantiating the
    correct device class based on a device ID string. This is particularly useful
    when devices are discovered automatically, as it allows the discovery system
    to create the appropriate device object without knowing the specific class.
    
    Device classes register themselves automatically in the DEVICE_MODEL_REGISTRY
    when they define a DEVICE_ID class attribute. The factory then uses this
    registry to map device IDs to their corresponding classes.
    
    The factory supports two creation patterns:
    1. Direct creation from device ID and connection parameters
    2. Creation from a DetectedDevice object (from device discovery)
    
    Example:
        >>> # Create device directly by ID
        >>> device = DeviceFactory.from_id('d-drive', 
        ...                                 transport_type=TransportType.SERIAL,
        ...                                 identifier='COM3')
        >>> 
        >>> # Create from discovered device
        >>> discovered = await DeviceDiscovery.discover_devices()
        >>> device = DeviceFactory.from_detected_device(discovered[0])
    
    Note:
        This factory uses the DEVICE_MODEL_REGISTRY which is populated by
        device class definitions (via __init_subclass__). Devices must inherit
        from PiezoDevice and define DEVICE_ID to be registered.
    """

    @staticmethod
    def from_id(device_id: str, *args, **kwargs) -> "PiezoDevice":
        """Create a device instance from its device ID string.

        This method looks up the device class in the registry and instantiates
        it with the provided arguments. The device ID must match a registered
        device class's DEVICE_ID attribute.

        Args:
            device_id: Unique identifier string for the device model (e.g., 'd-drive',
                'nv200'). This must match a DEVICE_ID defined by a PiezoDevice subclass.
            *args: Positional arguments passed to the device class constructor.
                Typically includes transport_type and identifier.
            **kwargs: Keyword arguments passed to the device class constructor.

        Returns:
            An instance of the PiezoDevice subclass corresponding to the device_id

        Raises:
            ValueError: If the device_id is not found in the registry (i.e., no
                device class has registered with that ID)
        
        Example:
            >>> device = DeviceFactory.from_id(
            ...     'd-drive',
            ...     transport_type=TransportType.SERIAL,
            ...     identifier='/dev/ttyUSB0'
            ... )
            >>> await device.connect()
        
        Note:
            Device classes auto-register by defining DEVICE_ID. If you get a
            ValueError, ensure the device class has been imported and defines
            a DEVICE_ID class attribute.
        """
        cls = DEVICE_MODEL_REGISTRY.get(device_id)

        if cls is None:
            raise ValueError(f"Unsupported device ID: {device_id}")

        return cls(*args, **kwargs)

    @staticmethod
    def from_detected_device(detected_device: DetectedDevice) -> "PiezoDevice":
        """Create a device instance from a DetectedDevice discovery result.
        
        This is a convenience method that extracts the device ID, transport type,
        and identifier from a DetectedDevice object and creates the appropriate
        device instance. This is the typical pattern used after device discovery.

        Args:
            detected_device: A DetectedDevice object returned by the device
                discovery system, containing device identification and connection
                information.

        Returns:
            An instance of the appropriate PiezoDevice subclass, configured with
            the detected device's connection parameters

        Raises:
            ValueError: If detected_device is None or if the device_id is not
                registered
        
        Example:
            >>> # Discover all available devices
            >>> discovered = await DeviceDiscovery.discover_devices()
            >>> 
            >>> # Create device instances from discovery results
            >>> devices = [DeviceFactory.from_detected_device(d) for d in discovered]
            >>> 
            >>> # Connect to first device
            >>> await devices[0].connect()
        
        Note:
            This method is commonly used in conjunction with DeviceDiscovery:
            1. Discovery identifies available devices
            2. DetectedDevice objects are created with connection info
            3. Factory creates typed device instances from detection results
        """
        if not detected_device:
            raise ValueError("No detected device provided.")

        return DeviceFactory.from_id(
            detected_device.device_id,
            transport_type=detected_device.transport,
            identifier=detected_device.identifier
        )