"""Unit information capability for device measurements."""

from .piezo_capability import PiezoCapability


class Units(PiezoCapability):
    """Query device measurement units for voltage and position.
    
    Provides methods to retrieve the units of measurement used by the
    device for voltage and position values. Units may vary by device
    configuration or hardware model.
    
    Example:
        >>> units = device.units
        >>> voltage_unit = await units.get_voltage_unit()
        >>> position_unit = await units.get_position_unit()
        >>> print(f"Voltage: {voltage_unit}, Position: {position_unit}")
        >>> # Voltage: V, Position: µm
    
    Note:
        - Units are device-specific and may be configurable
        - Common voltage units: V, mV
        - Common position units: µm, mrad
    """
    
    CMD_UNIT_VOLTAGE = "UNIT_VOLTAGE"
    CMD_UNIT_POSITION = "UNIT_POSITION"

    async def get_voltage_unit(self) -> str:
        """Get the unit of measurement for voltage values (open loop).
        
        Returns:
            Unit string (e.g., 'V', 'mV')
        
        Example:
            >>> unit = await device.units.get_voltage_unit()
            >>> print(f"Voltage is measured in {unit}")
        """
        result = await self._write(self.CMD_UNIT_VOLTAGE)
        return result[0]

    async def get_position_unit(self) -> str:
        """Get the unit of measurement for position values (closed loop).
        
        Returns:
            Unit string (e.g., 'µm', 'mrad')
        
        Example:
            >>> unit = await device.units.get_position_unit()
            >>> print(f"Position is measured in {unit}")
        """
        result = await self._write(self.CMD_UNIT_POSITION)
        return result[0]