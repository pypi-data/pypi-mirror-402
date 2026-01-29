"""Cooling fan control capability."""

from .piezo_capability import PiezoCapability


class Fan(PiezoCapability):
    """Control device/channel cooling fan operation.
    
    Enables or disables the internal cooling fan for thermal management.
    The fan helps dissipate heat from power electronics during operation.
    
    Example:
        >>> fan = channel.fan
        >>> # Enable cooling fan
        >>> await fan.set(True)
        >>> # Check fan status
        >>> is_running = await fan.get_enabled()
        >>> print(f"Fan: {'On' if is_running else 'Off'}")
    
    Note:
        - Not all devices have controllable fans
        - Some fans run automatically based on temperature
        - Disabling may cause thermal shutdown under heavy load
        - Fan noise may affect sensitive measurements
    """
    
    CMD_ENABLE = "FAN_ENABLE"

    async def set(self, enabled: bool) -> None:
        """Enable or disable the cooling fan.
        
        Args:
            enabled: True to turn fan on, False to turn off
        
        Example:
            >>> # Turn fan on for active cooling
            >>> await channel.fan.set(True)
            >>> # Turn off for quiet operation
            >>> await channel.fan.set(False)
        
        Note:
            - Disabling may limit operating power
            - Monitor temperature if fan is disabled
        """
        await self._write(self.CMD_ENABLE, [enabled])

    async def get_enabled(self) -> bool:
        """Check if the cooling fan is enabled.
        
        Returns:
            True if fan is running, False if stopped
        
        Example:
            >>> if await device.fan.get_enabled():
            ...     print("Fan is running")
            ... else:
            ...     print("Fan is off")
        """
        result = await self._write(self.CMD_ENABLE)
        return bool(int(result[0]))