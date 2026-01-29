"""Temperature monitoring capability."""

from .piezo_capability import PiezoCapability


class Temperature(PiezoCapability):
    """Read device internal temperature.
    
    Monitors the temperature of device electronics or power stages.
    Temperature monitoring helps prevent overheating and can be used
    for thermal management or diagnostic purposes.
    
    Example:
        >>> temp_cap = device.temperature
        >>> temp = await temp_cap.get()
        >>> print(f"Device temperature: {temp:.1f}°C")
        >>> if temp > 60:
        ...     print("Warning: High temperature")
    
    Note:
        - Temperature unit is typically degrees Celsius
        - Sensor location varies by device (electronics, power stage)
    """
    
    CMD_TEMPERATURE = "TEMPERATURE"


    async def get(self) -> float:
        """Get the current device temperature.
        
        Returns:
            Temperature value in degrees Celsius
        
        Example:
            >>> temperature = await device.temperature.get()
            >>> print(f"Current temp: {temperature:.2f}°C")
        
        Note:
            - Reading frequency depends on device update rate
            - Use for thermal monitoring and diagnostics
        """
        result = await self._write(self.CMD_TEMPERATURE)
        return float(result[0])