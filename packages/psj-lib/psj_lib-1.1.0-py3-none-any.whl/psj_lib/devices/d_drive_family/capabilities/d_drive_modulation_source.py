from ...base.capabilities import ModulationSourceTypes


class DDriveModulationSourceTypes(ModulationSourceTypes):
    """d-Drive modulation source types for external control input.
    
    Defines available modulation input sources specific to d-Drive amplifiers.
    These sources allow external control of the actuator position or voltage.
    
    Attributes:
        SERIAL_ENCODER: Serial interface + encoder knob is used for modulation.
            When sending a setpoint, the encoder offset is set to zero. Rotate the knob to apply an offset.
        SERIAL_ENCODER_ANALOG: Serial interface + encoder knob + analog input is used for modulation.
            When sending a setpoint, the encoder offset is set to zero. Rotate the knob to apply an offset.
            Additionally, an analog voltage input (0-10 V) can be used to apply a further offset.
    
    Example:
        >>> from psj_lib import DDriveModulationSourceTypes
        >>> await channel.modulation_source.set_source(
        ...     DDriveModulationSourceTypes.SERIAL_ENCODER
        ... )
        >>> current = await channel.modulation_source.get_source()
        >>> print(f"Active source: {current.name}")
    """
    SERIAL_ENCODER = 0
    SERIAL_ENCODER_ANALOG = 1