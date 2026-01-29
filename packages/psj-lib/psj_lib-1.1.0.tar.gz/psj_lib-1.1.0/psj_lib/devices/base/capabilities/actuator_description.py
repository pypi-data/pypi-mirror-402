"""Actuator description capability."""

from .piezo_capability import PiezoCapability


class ActuatorDescription(PiezoCapability):
    """Query descriptive information about the connected actuator.
    
    Retrieves a human-readable description of the piezoelectric actuator
    attached to a channel. This may include model number, specifications,
    or other identifying information.
    
    Example:
        >>> desc_cap = channel.actuator_description
        >>> description = await desc_cap.get()
        >>> print(f"Actuator: {description}")
        >>> # Actuator: MIPOS 100
    
    Note:
        - Description format is actuator-specific
        - May include model, travel range, resolution
        - Useful for logging and system documentation
        - Some devices return empty string if not configured
    """
    
    CMD_DESCRIPTION = "actuator_description"

    async def get(self) -> str:
        """Get the actuator description string.
        
        Returns:
            Human-readable description of the connected actuator
        
        Example:
            >>> desc = await channel.actuator_description.get()
            >>> print(f"Connected actuator: {desc}")
        """
        result = await self._write(self.CMD_DESCRIPTION)
        return result[0]