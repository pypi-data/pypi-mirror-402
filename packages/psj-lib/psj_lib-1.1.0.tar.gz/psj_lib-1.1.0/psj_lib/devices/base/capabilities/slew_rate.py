"""Slew rate limiting capability."""

from .piezo_capability import PiezoCapability


class SlewRate(PiezoCapability):
    """Control the maximum rate of change for actuator movement.
    
    Slew rate limiting controls how quickly the actuator can change
    position or voltage. This prevents mechanical shock, reduces
    vibration, and protects delicate samples.
    
    Lower slew rates result in slower, smoother movements. Higher
    rates allow faster response but may cause oscillation or overshoot.
    
    Example:
        >>> slew_rate_cap = channel.slew_rate
        >>> # Set gentle slew rate for delicate positioning
        >>> await slew_rate_cap.set(10.0)  # 10 units/second
        >>> # Query current setting
        >>> rate = await slew_rate_cap.get()
        >>> print(f"Slew rate: {rate} units/second")
    
    Note:
        - Units typically V/ms or %/ms, depending on device
        - Lower values = smoother movement
        - Zero or maximum may disable rate limiting (device-specific)
        - Affects both commanded movements and waveform generation
    """
    
    CMD_RATE = "SLEW_RATE"

    async def set(self, rate: float) -> None:
        """Set the slew rate limit.
        
        Args:
            rate: Maximum rate of change (units/second, typically V/ms or %/ms)
        
        Example:
            >>> # Set moderate slew rate
            >>> await channel.slew_rate.set(50.0)
            >>> # Set very slow for ultra-smooth motion
            >>> await channel.slew_rate.set(1.0)
        
        Note:
            - Range is device-specific
            - Zero may disable limiting (instant response)
            - Very low values result in slow movements
        """
        await self._write(self.CMD_RATE, [rate])

    async def get(self) -> float:
        """Get the current slew rate limit.
        
        Returns:
            Current slew rate in device units (typically V/ms or %/ms)
        
        Example:
            >>> current_rate = await channel.slew_rate.get()
            >>> print(f"Max movement speed: {current_rate} V/ms")
        """
        result = await self._write(self.CMD_RATE)
        return float(result[0])