"""Static waveform generator for periodic signal generation."""

from .piezo_capability import PiezoCapability


class StaticWaveformGenerator(PiezoCapability):
    """Generate periodic waveforms for actuator modulation.
    
    The static waveform generator produces continuous periodic signals
    (sine, square, triangle, etc.) that can be used for:
    - Scanning applications
    - Vibration testing
    - Frequency response characterization
    - Dynamic positioning
    
    Configurable parameters:
    - Frequency: Rate of oscillation (Hz)
    - Amplitude: Peak-to-peak magnitude
    - Offset: DC bias level
    - Duty cycle: Pulse width for square/pulse waveforms
    
    The generated waveform can typically be used as the primary control signal.
    
    Example:
        >>> wfg = channel.static_waveform_generator
        >>> # Generate 10 Hz sine wave, 20µm amplitude, centered at 50µm
        >>> await wfg.set(
        ...     frequency=10.0,
        ...     amplitude=20.0,
        ...     offset=50.0
        ... )
        >>> # Create square wave with 30% duty cycle
        >>> await wfg.set(
        ...     frequency=5.0,
        ...     duty_cycle=30.0  # 30% high time
        ... )
        >>> # Query current settings
        >>> freq = await wfg.get_frequency()
        >>> amp = await wfg.get_amplitude()
        >>> print(f"Generating {freq} Hz, ±{amp/2} µm")
    
    Note:
        - May require modulation source selection to use waveform output
        - Waveform type (sine/square/triangle) is device-specific
        - Frequency is limited by device output current and actuator resonance frequency
        - Amplitude is limited by actuator travel range
    """
    
    CMD_FREQUENCY = "STATIC_WAVEFORM_FREQUENCY"
    CMD_AMPLITUDE = "STATIC_WAVEFORM_AMPLITUDE"
    CMD_OFFSET = "STATIC_WAVEFORM_OFFSET"
    CMD_DUTY_CYCLE = "STATIC_WAVEFORM_DUTY_CYCLE"

    async def set(
        self,
        frequency: float | None = None,
        amplitude: float | None = None,
        offset: float | None = None,
        duty_cycle: float | None = None
    ) -> None:
        """Configure waveform generator parameters.
        
        Args:
            frequency: Oscillation frequency in Hz
            amplitude: Amplitude in position units (typically µm or V)
            offset: DC offset/center position in position units (typically µm or V)
            duty_cycle: Pulse width percentage (0-100%)
        
        Example:
            >>> # Slow sine wave scan
            >>> await wfg.set(
            ...     frequency=0.5,  # 0.5 Hz (2 second period)
            ...     amplitude=100.0,  # 100µm amplitude
            ...     offset=50.0  # Centered at 50µm
            ... )
            >>> 
            >>> # Fast square wave with asymmetric duty cycle
            >>> await wfg.set(
            ...     frequency=100.0,
            ...     amplitude=10.0,
            ...     duty_cycle=25.0  # 25% high, 75% low
            ... )
        
        Note:
            - Only provided parameters are updated
            - Amplitude is amplitude
            - Actual range: [offset - amplitude, offset + amplitude]
            - Frequency is limited by device output current and actuator resonance frequency
            - Amplitude is limited by actuator travel range
        """
        if frequency is not None:
            await self._write(self.CMD_FREQUENCY, [frequency])

        if amplitude is not None:
            await self._write(self.CMD_AMPLITUDE, [amplitude])

        if offset is not None:
            await self._write(self.CMD_OFFSET, [offset])

        if duty_cycle is not None:
            await self._write(self.CMD_DUTY_CYCLE, [duty_cycle])

    async def get_frequency(self) -> float:
        """Get waveform frequency.
        
        Returns:
            Frequency in Hz
        
        Example:
            >>> freq = await wfg.get_frequency()
            >>> period = 1.0 / freq
            >>> print(f"Period: {period*1000:.1f} ms")
        """
        result = await self._write(self.CMD_FREQUENCY)
        return float(result[0])

    async def get_amplitude(self) -> float:
        """Get waveform amplitude.
        
        Returns:
            Amplitude in position units (typically µm or V)
        
        Example:
            >>> amp = await wfg.get_amplitude()
            >>> print(f"Oscillating ±{amp:.1f} µm from center")
        """
        result = await self._write(self.CMD_AMPLITUDE)
        return float(result[0])

    async def get_offset(self) -> float:
        """Get waveform DC offset (center position).
        
        Returns:
            Offset in position units (typically µm or V)
        
        Example:
            >>> offset = await wfg.get_offset()
            >>> amp = await wfg.get_amplitude()
            >>> print(f"Range: {offset-amp:.1f} to {offset+amp:.1f} µm")
        """
        result = await self._write(self.CMD_OFFSET)
        return float(result[0])

    async def get_duty_cycle(self) -> float:
        """Get pulse duty cycle percentage.
        
        Returns:
            Duty cycle in percent (0-100%)
        
        Example:
            >>> duty = await wfg.get_duty_cycle()
            >>> print(f"Pulse: {duty:.0f}% high, {100-duty:.0f}% low")
        
        Note:
            - 50% = symmetric wave
        """
        result = await self._write(self.CMD_DUTY_CYCLE)
        return float(result[0])

