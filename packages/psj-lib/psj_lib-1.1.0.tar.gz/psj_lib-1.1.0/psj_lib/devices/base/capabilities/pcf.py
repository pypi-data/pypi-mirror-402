"""Pre-control factor capability."""

from .piezo_capability import PiezoCapability


class PreControlFactor(PiezoCapability):
    """Configure pre-control factor for feedforward control.
    
    The Pre-Control Factor (PCF) provides feedforward compensation
    to improve control system response. It anticipates required
    control action based on the setpoint change, reducing settling
    time and tracking error.
    
    PCF is added to the PID controller output to provide faster
    initial response to setpoint changes.
    
    Example:
        >>> pcf = channel.pre_control_factor
        >>> # Set moderate pre-control
        >>> await pcf.set(0.5)
        >>> # Query current value
        >>> value = await pcf.get()
        >>> print(f"PCF: {value}")
    
    Note:
        - Typical range: 0.0 (no feedforward) to 1.0 (full feedforward)
        - Higher values = faster response but potential overshoot
        - Only active in closed-loop mode
        - Interacts with PID parameters
        - Device-specific implementation and range
    """
    
    CMD_VALUE = "PCF_VALUE"

    async def set(self, value: float) -> None:
        """Set the pre-control factor value.
        
        Args:
            value: Pre-control factor (typically 0.0 to 1.0)
        
        Example:
            >>> # Conservative feedforward
            >>> await channel.pre_control_factor.set(0.3)
            >>> # Aggressive feedforward
            >>> await channel.pre_control_factor.set(0.8)
        
        Note:
            - Exact range is device-specific
            - Higher values improve response speed
            - Too high may cause overshoot
            - Tune in conjunction with PID parameters
        """
        await self._write(self.CMD_VALUE, [value])

    async def get(self) -> None:
        """Get the current pre-control factor value.
        
        Returns:
            Current PCF value (device-specific units, typically 0.0-1.0)
        
        Example:
            >>> pcf_value = await channel.pre_control_factor.get()
            >>> print(f"Feedforward factor: {pcf_value}")
        """
        return await self._write(self.CMD_VALUE)