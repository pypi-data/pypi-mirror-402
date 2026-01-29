"""Low-pass filter capability for signal conditioning."""

from .piezo_capability import PiezoCapability


class LowPassFilter(PiezoCapability):
    """Configure low-pass filtering of position or control signals.
    
    Low-pass filters attenuate high-frequency noise and oscillations
    while allowing low-frequency signals to pass. This improves signal
    quality and reduces noise in position measurements or control output.
    
    The cutoff frequency determines which frequencies are filtered:
    - Signals below cutoff: pass through unaffected
    - Signals above cutoff: progressively attenuated
    
    Example:
        >>> lpf = channel.low_pass_filter
        >>> # Enable with 100 Hz cutoff
        >>> await lpf.set(enabled=True, cutoff_frequency=100.0)
        >>> # Check settings
        >>> enabled = await lpf.get_enabled()
        >>> freq = await lpf.get_cutoff_frequency()
        >>> print(f"LPF: {'On' if enabled else 'Off'}, {freq} Hz")
    
    Note:
        - Lower cutoff = more filtering, slower response
        - Higher cutoff = less filtering, faster response
        - Can be applied to sensor input, control output, or both
        - Adds phase lag proportional to filtering strength
    """
    
    CMD_ENABLE = "LOW_PASS_FILTER_ENABLE"
    CMD_CUTOFF_FREQUENCY = "LOW_PASS_FILTER_CUTOFF_FREQUENCY"

    async def set(
        self,
        enabled: bool | None = None,
        cutoff_frequency: float | None = None,
    ) -> None:
        """Configure low-pass filter parameters.
        
        Args:
            enabled: True to enable filtering, False to bypass
            cutoff_frequency: -3dB cutoff frequency in Hz
        
        Example:
            >>> # Enable with specific cutoff
            >>> await channel.low_pass_filter.set(
            ...     enabled=True,
            ...     cutoff_frequency=50.0
            ... )
            >>> # Just change frequency
            >>> await channel.low_pass_filter.set(cutoff_frequency=200.0)
        
        Note:
            - Only provided parameters are updated
            - Cutoff range is device-specific
            - Typical range: 1 Hz to several kHz
        """
        if enabled is not None:
            await self._write(self.CMD_ENABLE, [enabled])

        if cutoff_frequency is not None:
            await self._write(self.CMD_CUTOFF_FREQUENCY, [cutoff_frequency])

    async def get_enabled(self) -> bool:
        """Check if low-pass filter is enabled.
        
        Returns:
            True if filter is active, False if bypassed
        
        Example:
            >>> if await channel.low_pass_filter.get_enabled():
            ...     print("Filtering active")
        """
        result = await self._write(self.CMD_ENABLE)
        return bool(result[0])

    async def get_cutoff_frequency(self) -> float:
        """Get the current cutoff frequency.
        
        Returns:
            Cutoff frequency in Hz
        
        Example:
            >>> freq = await channel.low_pass_filter.get_cutoff_frequency()
            >>> print(f"Filtering above {freq} Hz")
        """
        result = await self._write(self.CMD_CUTOFF_FREQUENCY)
        return float(result[0])