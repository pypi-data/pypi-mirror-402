"""d-Drive specific setpoint implementation with local caching."""

from ...base.capabilities import Setpoint


class DDriveSetpoint(Setpoint):
    """d-Drive setpoint control with client-side caching.
    
    Unlike the base Setpoint class, DDriveSetpoint maintains a local cache
    of the last set value. This is necessary because the d-Drive hardware
    does not support reading back the setpoint value - it only accepts
    write operations.
    
    The cached value is returned when get() is called, providing a 
    consistent API while working around the hardware limitation.
    
    Example:
        >>> # Set target position
        >>> await channel.setpoint.set(50.0)
        >>> # Read back the cached value (not from device)
        >>> value = await channel.setpoint.get()
        >>> print(f"Setpoint: {value} µm")  # 50.0
    
    Note:
        - get() returns the cached value, not a hardware read
        - Cache is only updated by set() calls
        - Initial cache value is 0 before first set()
        - If setpoint is changed by another application, cache will be stale
    """
    
    def __init__(self, write_cb, device_commands):
        super().__init__(write_cb, device_commands)
        self._setpoint_cache = 0.0
    
    async def set(self, value: float) -> None:
        """Set target position and update local cache.
        
        Args:
            value: Desired position in device units
        
        Example:
            >>> await channel.setpoint.set(75.5)
        """
        self._setpoint_cache = value
        await super().set(value)

    async def get(self) -> float:
        """Get the cached setpoint value.
        
        Returns:
            Last setpoint value set via set() method
        
        Example:
            >>> target = await channel.setpoint.get()
            >>> actual = await channel.position.get()
            >>> error = target - actual
        
        Note:
            This returns the cached value, not a hardware read.
            The d-Drive does not support reading back setpoint.
        """
        return self._setpoint_cache
