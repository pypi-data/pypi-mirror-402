"""Notch filter capability for resonance suppression."""

from .piezo_capability import PiezoCapability


class NotchFilter(PiezoCapability):
    """Configure notch filtering to suppress specific frequency components.
    
    Notch filters (band-stop filters) attenuate signals at a specific
    frequency while passing all other frequencies. They are used to
    suppress mechanical resonances that can cause instability or
    oscillation in closed-loop systems.
    
    Parameters:
    - Center frequency: The frequency to suppress (resonance peak)
    - Bandwidth: Width of suppressed frequency band
    
    Example:
        >>> notch = channel.notch_filter
        >>> # Suppress 500 Hz resonance
        >>> await notch.set(
        ...     enabled=True,
        ...     frequency=500.0,
        ...     bandwidth=50.0
        ... )
        >>> # Check configuration
        >>> freq = await notch.get_frequency()
        >>> bw = await notch.get_bandwidth()
        >>> print(f"Notch at {freq}±{bw/2} Hz")
    
    Note:
        - Center frequency should match mechanical resonance
        - Narrow bandwidth = precise suppression, may be insufficient
        - Wide bandwidth = broader suppression, affects more frequencies
        - Multiple resonances may require cascaded notch filters
    """
    
    CMD_ENABLE = "NOTCH_FILTER_ENABLE"
    CMD_FREQUENCY = "NOTCH_FILTER_FREQUENCY"    
    CMD_BANDWIDTH = "NOTCH_FILTER_BANDWIDTH"


    async def set(
        self,
        enabled: bool | None = None,
        frequency: float | None = None,
        bandwidth: float | None = None,
    ) -> None:
        """Configure notch filter parameters.
        
        Args:
            enabled: True to enable filtering, False to bypass
            frequency: Center frequency to suppress (Hz)
            bandwidth: Width of suppression band (Hz)
        
        Example:
            >>> # Enable notch at 750 Hz with 100 Hz bandwidth
            >>> await channel.notch_filter.set(
            ...     enabled=True,
            ...     frequency=750.0,
            ...     bandwidth=100.0
            ... )
            >>> # Just adjust bandwidth
            >>> await channel.notch_filter.set(bandwidth=80.0)
        
        Note:
            - Only provided parameters are updated
            - Frequency range is device-specific
            - Bandwidth affects depth and width of suppression
        """
        if enabled is not None:
            await self._write(self.CMD_ENABLE, [enabled])
    
        if frequency is not None:
            await self._write(self.CMD_FREQUENCY, [frequency])
    
        if bandwidth is not None:
            await self._write(self.CMD_BANDWIDTH, [bandwidth])


    async def get_enabled(self) -> bool:
        """Check if notch filter is enabled.
        
        Returns:
            True if filter is active, False if bypassed
        
        Example:
            >>> if await channel.notch_filter.get_enabled():
            ...     print("Notch filter active")
        """
        result = await self._write(self.CMD_ENABLE)
        return bool(result[0])
    

    async def get_frequency(self) -> float:
        """Get the notch center frequency.
        
        Returns:
            Center frequency in Hz
        
        Example:
            >>> freq = await channel.notch_filter.get_frequency()
            >>> print(f"Suppressing {freq} Hz")
        """
        result = await self._write(self.CMD_FREQUENCY)
        return float(result[0])
    

    async def get_bandwidth(self) -> float:
        """Get the notch filter bandwidth.
        
        Returns:
            Bandwidth in Hz
        
        Example:
            >>> bw = await channel.notch_filter.get_bandwidth()
            >>> freq = await channel.notch_filter.get_frequency()
            >>> print(f"Suppressing {freq-bw/2:.0f}-{freq+bw/2:.0f} Hz")
        """
        result = await self._write(self.CMD_BANDWIDTH)
        return float(result[0])