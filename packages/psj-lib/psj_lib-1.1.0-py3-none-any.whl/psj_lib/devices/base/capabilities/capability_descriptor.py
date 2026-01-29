"""Descriptor for lazy initialization of device capabilities.

Provides a decorator pattern for capability attributes that are created
only when first accessed, reducing initialization overhead.
"""

from typing import Self, overload

from .piezo_capability import DeviceCommands, PiezoCapability


class CapabilityDescriptor[T: PiezoCapability]:
    """Descriptor for lazy-loading capability objects on device and channel instances.
    
    Implements the descriptor protocol to create capability instances only
    when first accessed. This allows device classes to declare many
    capabilities without the overhead of instantiating them all at once.

    This also allows capabilities to be defined declaratively as class
    attributes, improving code organization and readability. Alternatively,
    capabilities could be created in the device's __init__, and be accessed using
    property decorators, but this results in more boilerplate code.
    
    The descriptor caches the created capability instance, so subsequent
    accesses return the same object.
    
    Generic Type Parameter:
        T: The specific PiezoCapability subclass this descriptor manages
    
    Attributes:
        capability_class: The capability class to instantiate
        device_commands: Command mappings for the capability
        kwargs: Additional keyword arguments for capability initialization
        attr_name: Private attribute name for caching (set by __set_name__)
    
    Example:
        >>> class MyDevice(PiezoDevice):
        ...     position = CapabilityDescriptor(
        ...         Position,
        ...         {Position.CMD_POSITION: "pos"}
        ...     )
        >>> 
        >>> device = MyDevice()
        >>> # First access creates the Position instance
        >>> pos = device.position
        >>> # Subsequent accesses return cached instance
        >>> assert device.position is pos
    
    Note:
        - Uses descriptor protocol for property-like access
        - Requires device/channel instance to have _capability_write method
        - Python 3.12+ generic syntax for type safety
    """
    
    def __init__(self, capability_class: type[T], device_commands: DeviceCommands, **kwargs):
        """Initialize the capability descriptor.
        
        Args:
            capability_class: The PiezoCapability subclass to instantiate
            device_commands: Command ID to device command string mapping
            **kwargs: Additional arguments passed to capability constructor
        """
        self.capability_class = capability_class
        self.device_commands = device_commands
        self.kwargs = kwargs
    
    def __set_name__(self, owner, name):
        """Store the attribute name when descriptor is assigned to class.
        
        Called automatically by Python when the descriptor is assigned to
        a class attribute. Sets up the private attribute name for caching.
        
        Args:
            owner: The class that owns this descriptor
            name: The attribute name assigned to this descriptor
        """
        self.attr_name = f"_{name}"
    
    @overload
    def __get__(self, instance: None, owner: type) -> Self: ...
    
    @overload  
    def __get__(self, instance: object, owner: type) -> T: ...
    
    def __get__(self, instance, owner) -> T | Self:
        """Get or create the capability instance.
        
        Implements lazy initialization: creates the capability on first
        access and caches it for subsequent accesses.
        
        Args:
            instance: The device instance accessing the capability (None for class access)
            owner: The device class that owns this descriptor
        
        Returns:
            The descriptor itself if accessed from class, or the capability
            instance if accessed from an instance
        
        Note:
            - Class access (MyDevice.position) returns descriptor
            - Instance access (device.position) returns capability
        """
        if instance is None:
            return self
        
        if not hasattr(instance, self.attr_name):
            capability = self.capability_class(
                instance._capability_write,
                self.device_commands,
                **self.kwargs
            )
            setattr(instance, self.attr_name, capability)
        
        return getattr(instance, self.attr_name)