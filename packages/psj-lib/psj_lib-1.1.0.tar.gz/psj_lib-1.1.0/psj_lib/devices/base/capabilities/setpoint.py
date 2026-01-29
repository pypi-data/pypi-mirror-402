"""Setpoint control capability for piezoelectric actuators."""

from .piezo_capability import PiezoCapability


class Setpoint(PiezoCapability):
    """Control the target setpoint (desired position) of an actuator.
    
    The setpoint represents the target position that the actuator should
    move to. In closed-loop mode, the controller adjusts voltage to
    achieve this setpoint. In open-loop mode, this directly controls
    the output voltage.
    
    Example:
        >>> setpoint_cap = channel.setpoint
        >>> # Move to 50 micrometers
        >>> await setpoint_cap.set(50.0)
        >>> # Read current setpoint
        >>> current = await setpoint_cap.get()
        >>> print(f"Target position: {current} µm")
    
    Note:
        - Setpoint units match position units (typically µm in closed-loop, V in open-loop)
        - Range limited by actuator travel range
        - In closed-loop: controller drives to this position
        - In open-loop: maps to output voltage
    """
    
    CMD_SETPOINT = "SETPOINT"

    async def set(self, setpoint: float) -> None:
        """Set the target position for the actuator.
        
        Args:
            setpoint: Desired position in device units (typically µm in closed-loop, V in open-loop)
        
        Example:
            >>> # Move to 75.5 micrometers (closed-loop) or volts (open-loop)
            >>> await channel.setpoint.set(75.5)
        
        Note:
            - Value is clamped to actuator range by device
            - Movement speed affected by slew rate settings
            - In closed-loop mode, position is actively controlled by the amplifier
        """
        await self._write(self.CMD_SETPOINT, [setpoint])
