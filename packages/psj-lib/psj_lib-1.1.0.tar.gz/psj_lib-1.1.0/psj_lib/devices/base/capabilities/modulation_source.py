"""Modulation input source selection capability."""

from enum import Enum

from .piezo_capability import PiezoCapability


class ModulationSourceTypes(Enum):
    """Base enumeration for modulation input sources.
    
    Device-specific implementations define available modulation sources.
    Common sources include external analog input, internal waveform
    generator, or digital sources.
    
    Attributes:
        UNKNOWN: Unrecognized or invalid source value
    
    Note:
        - Device-specific subclasses define actual sources
        - UNKNOWN used for unrecognized device responses
    """
    @property
    def UNKNOWN(self):
        return -1


class ModulationSource(PiezoCapability):
    """Select the source for setpoint modulation input.
    
    Configures which signal source is used to modulate the actuator
    position or voltage. Modulation allows dynamic control from external
    signals or internal waveform generators.
    
    Common modulation sources:
    - External analog input (0-10V)
    - Internal waveform generator
    - Serial commands
    
    Example:
        >>> # Device-specific enum
        >>> from psj_lib import ModulationSourceTypes
        >>> 
        >>> mod = channel.modulation_source
        >>> # Use internal waveform generator
        >>> await mod.set_source(ModulationSourceTypes.INTERNAL_WAVEFORM)
        >>> # Check current source
        >>> source = await mod.get_source()
        >>> print(f"Modulation from: {source.name}")
    
    Note:
        - Modulation mode must be enabled separately
        - Input range and scaling are device-specific
        - External input typically 0-10V
        - Source enum is device-specific
    """
    
    CMD_SOURCE = "MODULATION_SOURCE"

    def __init__(
        self,
        write_cb,
        device_commands,
        sources: type[ModulationSourceTypes]
    ) -> None:
        """Initialize modulation source capability.
        
        Args:
            write_cb: Command execution callback
            device_commands: Command mapping dictionary
            sources: Device-specific ModulationSourceTypes enum type
        """
        super().__init__(write_cb, device_commands)
        self._sources = sources

    async def set_source(self, source: ModulationSourceTypes) -> None:
        """Set the modulation input source.
        
        Args:
            source: Modulation source from device-specific enum
        
        Raises:
            ValueError: If source is not from the correct device-specific enum
        
        Example:
            >>> from psj_lib import ModulationSourceTypes
            >>> await channel.modulation_source.set_source(
            ...     ModulationSourceTypes.EXTERNAL_INPUT
            ... )
        
        Note:
            - Source must be from device-specific enum
            - Invalid sources raise ValueError
            - May need to enable modulation mode separately
        """
        if type(source) is not self._sources:
            raise ValueError(f"Invalid modulation source type: {type(source)} (Expected: {self._sources})")

        await self._write(self.CMD_SOURCE, [source.value])

    async def get_source(self) -> ModulationSourceTypes:
        """Get the current modulation input source.
        
        Returns:
            Current modulation source enum value, or UNKNOWN if
            device returns unrecognized value
        
        Example:
            >>> source = await channel.modulation_source.get_source()
            >>> if source == ModulationSourceTypes.EXTERNAL_INPUT:
            ...     print("Using external modulation input")
        
        Note:
            - Returns UNKNOWN for unrecognized device responses
            - Source enum is device-specific
        """
        result = await self._write(self.CMD_SOURCE)
        value = int(result[0])

        try:
            return self._sources(value)
        except ValueError:
            return self._sources.UNKNOWN