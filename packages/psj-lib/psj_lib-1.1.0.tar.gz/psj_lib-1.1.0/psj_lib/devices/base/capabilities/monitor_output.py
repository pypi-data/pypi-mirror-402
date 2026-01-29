"""Monitor output source selection capability."""

from enum import Enum

from .piezo_capability import PiezoCapability


class MonitorOutputSource(Enum):
    """Base enumeration for monitor output signal sources.
    
    Device-specific implementations define available monitor sources.
    Common sources include position, setpoint, voltage, error signal, etc.
    
    Attributes:
        UNKNOWN: Unrecognized or invalid source value
    
    Note:
        - Device-specific subclasses define actual sources
        - UNKNOWN used for unrecognized device responses
    """
    @property
    def UNKNOWN(self):
        return -1


class MonitorOutput(PiezoCapability):
    """Select signal source for analog monitor output.
    
    Configures which internal signal is routed to the device's analog
    monitor output connector. This allows real-time observation of
    various internal signals using an oscilloscope or data acquisition
    system.
    
    Available sources depend on device model and may include:
    - Position sensor value
    - Commanded setpoint
    - Output voltage
    - Control error signal
    - And more...
    
    Example:
        >>> # Device-specific enum
        >>> from psj_lib import MonitorOutputSource
        >>> 
        >>> monitor = channel.monitor_output
        >>> # Route position to monitor output
        >>> await monitor.set_source(MonitorOutputSource.POSITION)
        >>> # Check current source
        >>> source = await monitor.get_source()
        >>> print(f"Monitoring: {source.name}")
    
    Note:
        - Output is typically 0-10V
        - Scaling depends on device and selected source
        - Useful for debugging and real-time monitoring
        - Source enum is device-specific
    """
    
    CMD_OUTPUT_SRC = "MONITOR_OUTPUT_SRC"

    def __init__(
        self,
        write_cb,
        device_commands,
        sources: type[MonitorOutputSource]
    ) -> None:
        """Initialize monitor output capability.
        
        Args:
            write_cb: Command execution callback
            device_commands: Command mapping dictionary
            sources: Device-specific MonitorOutputSource enum type
        """
        super().__init__(write_cb, device_commands)
        self._sources = sources

    async def set_source(self, source: MonitorOutputSource) -> None:
        """Set the monitor output signal source.
        
        Args:
            source: Monitor output source from device-specific enum
        
        Raises:
            ValueError: If source is not from the correct device-specific enum
        
        Example:
            >>> from psj_lib import MonitorOutputSource
            >>> await channel.monitor_output.set_source(
            ...     MonitorOutputSource.SETPOINT
            ... )
        
        Note:
            - Source must be from device-specific enum
            - Invalid sources raise ValueError
            - Monitor output updates in real-time
        """
        if type(source) is not self._sources:
            raise ValueError(f"Invalid monitor source type: {type(source)} (Expected: {self._sources})")

        await self._write(self.CMD_OUTPUT_SRC, [source.value])

    async def get_source(self) -> MonitorOutputSource:
        """Get the current monitor output source.
        
        Returns:
            Current monitor output source enum value, or UNKNOWN if
            device returns unrecognized value
        
        Example:
            >>> source = await channel.monitor_output.get_source()
            >>> if source == MonitorOutputSource.POSITION:
            ...     print("Monitoring position sensor")
        
        Note:
            - Returns UNKNOWN for unrecognized device responses
            - Source enum is device-specific
        """
        result = await self._write(self.CMD_OUTPUT_SRC)
        value = int(result[0])

        try:
            return self._sources(value)
        except ValueError:
            return self._sources.UNKNOWN