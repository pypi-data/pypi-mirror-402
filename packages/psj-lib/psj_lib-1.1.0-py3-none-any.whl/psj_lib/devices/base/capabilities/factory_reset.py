"""Factory reset capability."""

from .piezo_capability import PiezoCapability


class FactoryReset(PiezoCapability):
    """Reset device to factory default settings.
    
    Restores all device parameters to their factory default values.
    Depending on the device implementation, this includes PID parameters, 
    filters, control modes, and all other configurable settings.
    
    **WARNING: This operation cannot be undone!**
    
    Example:
        >>> reset = device.factory_reset
        >>> # Save current settings first!
        >>> await device.backup("settings_backup.txt")
        >>> # Reset to factory defaults
        >>> await reset.execute()
        >>> # Device parameters now at factory values
    
    Note:
        - **All custom settings are lost**
        - Use device.backup() to save configuration first
    """
    
    CMD_RESET = "FACTORY_RESET"

    async def execute(self) -> None:
        """Execute factory reset operation.
        
        **WARNING: This permanently erases all custom settings!**
        
        Example:
            >>> # Backup first!
            >>> await device.backup("config_backup.txt")
            >>> # Then reset
            >>> await device.factory_reset.execute()
            >>> print("Device reset to factory defaults")
        
        Note:
            - Cannot be undone
        """
        await self._write(self.CMD_RESET)