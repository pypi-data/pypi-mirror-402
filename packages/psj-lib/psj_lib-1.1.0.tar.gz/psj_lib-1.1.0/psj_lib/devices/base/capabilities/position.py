"""Position readback capability for piezoelectric actuators."""

from .piezo_capability import PiezoCapability


class Position(PiezoCapability):
    """Read the current position of a piezoelectric actuator.
    
    Provides access to the current measured position of the actuator.
    In closed-loop systems, this represents the sensor feedback value.
    In open-loop systems, this may represent the output voltage.
    
    Example:
        >>> position_cap = channel.position
        >>> current_pos = await position_cap.get()
        >>> print(f"Current position: {current_pos} µm")
    
    Note:
        - Position units depend on device configuration
        - In closed-loop mode: sensor feedback value
        - In open-loop mode: output voltage representation
        - Value range depends on actuator specifications
    """
    
    CMD_POSITION = "POSITION"

    async def get(self) -> float:
        """Get the current actuator position.
        
        Returns:
            Current position value in device-configured units (typically µm or volts)
        
        Example:
            >>> pos = await channel.position.get()
            >>> print(f"Actuator at {pos:.2f} µm")
        
        Note:
            - Units can be queried via device.units.get_position_unit()
            - Update rate depends on device capabilities
        """
        result = await self._write(self.CMD_POSITION)
        return float(result[0])