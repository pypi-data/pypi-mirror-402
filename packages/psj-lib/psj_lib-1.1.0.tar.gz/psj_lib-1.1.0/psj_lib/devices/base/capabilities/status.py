"""Device status register capability."""

from .piezo_capability import PiezoCapability


class StatusRegister:
    """Base class for device status register interpretation.
    
    Holds raw status data from device. Device-specific subclasses
    interpret the raw status bits to provide meaningful properties
    and error conditions.
    
    Attributes:
        _raw: Raw status response from device
    
    Example:
        >>> # Subclass provides bit interpretation
        >>> class DeviceStatusRegister(StatusRegister):
        ...     @property
        ...     def is_moving(self) -> bool:
        ...         return bool(int(self._raw) & 0x01)
        >>> 
        >>> status = await device.status.get()
        >>> if status.is_moving:
        ...     print("Device is moving")
    
    Note:
        - Device-specific implementations decode status bits
        - Raw value format varies by device model
    """
    
    def __init__(self, value: list[str]) -> None:
        """Initialize status register with raw device response.
        
        Args:
            value: Raw status response from device
        """
        self._raw = value

    @property
    def raw(self) -> list[str]:
        """Get the raw status register value from the device.
        
        Returns:
            Raw status response as received from the device
        
        Example:
            >>> status = await device.status.get()
            >>> print(f"Raw status: {status.raw}")
        """
        return self._raw


class Status(PiezoCapability):
    """Query device status register.
    
    Retrieves the current status of the device, returning a status
    register object that interprets device state, error conditions,
    and operational flags.
    
    The status register class is device-specific and provided during
    capability initialization.
    
    Example:
        >>> status_cap = device.status
        >>> status_reg = await status_cap.get()
        >>> # Device-specific status properties
        >>> if hasattr(status_reg, 'has_error'):
        ...     if status_reg.has_error:
        ...         print("Device error detected")
    
    Note:
        - Status format is device-specific
        - Register type specified at capability creation
        - Provides real-time device state information
    """
    
    CMD_STATUS = "STATUS"

    def __init__(
        self,
        write_cb,
        device_commands,
        register_type: type[StatusRegister]
    ) -> None:
        """Initialize status capability with register interpreter.
        
        Args:
            write_cb: Command execution callback
            device_commands: Command mapping dictionary
            register_type: Device-specific StatusRegister subclass
        """
        super().__init__(write_cb, device_commands)
        self._register_type = register_type

    async def get(self) -> StatusRegister:
        """Query device status register.
        
        Returns:
            StatusRegister instance with device state information
        
        Example:
            >>> status = await device.status.get()
            >>> # Access device-specific properties
            >>> print(f"Status: {status.raw}")
        
        Note:
            - Return type depends on device-specific register class
            - Status interpretation varies by device model
        """
        response = await self._write(self.CMD_STATUS)
        return self._register_type(response)