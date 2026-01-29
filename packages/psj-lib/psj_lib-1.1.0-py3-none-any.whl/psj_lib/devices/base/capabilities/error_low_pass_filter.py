"""Error signal low-pass filter for PID controller."""

from .piezo_capability import PiezoCapability


class ErrorLowPassFilter(PiezoCapability):
    """Filter the position error signal in closed-loop control.
    
    Applies low-pass filtering to the error signal (setpoint - position)
    before it enters the PID controller. This reduces high-frequency
    noise in the error signal that could cause unstable control behavior.
    
    Unlike the general low-pass filter, this specifically filters the
    error signal used by the PID controller, helping to stabilize
    control without filtering the position feedback directly.
    
    Parameters:
    - Cutoff frequency: Where filtering begins (-3dB point)
    - Order: Filter steepness (1st, 2nd order, etc.)
    
    Example:
        >>> err_lpf = channel.error_low_pass_filter
        >>> # Configure 2nd-order filter at 200 Hz
        >>> await err_lpf.set(
        ...     cutoff_frequency=200.0,
        ...     order=2
        ... )
        >>> # Query settings
        >>> freq = await err_lpf.get_cutoff_frequency()
        >>> order = await err_lpf.get_order()
        >>> print(f"{order}-order error filter at {freq} Hz")
    
    Note:
        - Only affects closed-loop control
        - Higher order = steeper rolloff, more phase lag
        - Lower cutoff = more filtering, slower response
        - Helps stabilize noisy systems
    """
    
    CMD_CUTOFF_FREQUENCY = "ERROR_LOW_PASS_FILTER_CUTOFF_FREQUENCY"
    CMD_ORDER = "ERROR_LOW_PASS_FILTER_ORDER"

    async def set(
        self,
        cutoff_frequency: float | None = None,
        order: int | None = None,
    ) -> None:
        """Configure error signal filter parameters.
        
        Args:
            cutoff_frequency: -3dB cutoff frequency in Hz
            order: Filter order (1 = 1st order, 2 = 2nd order, etc.)
        
        Example:
            >>> # Set moderate filtering
            >>> await channel.error_low_pass_filter.set(
            ...     cutoff_frequency=150.0,
            ...     order=1
            ... )
            >>> # Increase filter steepness
            >>> await channel.error_low_pass_filter.set(order=2)
        
        Note:
            - Only provided parameters are updated
            - Higher order provides sharper cutoff but more phase lag
            - Typical orders: 1 (gentlest) to 4 (steepest)
            - Coordinate with PID tuning for best stability
        """
        if cutoff_frequency is not None:
            await self._write(self.CMD_CUTOFF_FREQUENCY, [cutoff_frequency])

        if order is not None:
            await self._write(self.CMD_ORDER, [order])

    async def get_cutoff_frequency(self) -> float:
        """Get the current error filter cutoff frequency.
        
        Returns:
            Cutoff frequency in Hz
        
        Example:
            >>> freq = await channel.error_low_pass_filter.get_cutoff_frequency()
            >>> print(f"Error signal filtered above {freq} Hz")
        """
        result = await self._write(self.CMD_CUTOFF_FREQUENCY)
        return float(result[0])

    async def get_order(self) -> int:
        """Get the current filter order.
        
        Returns:
            Filter order (1, 2, 3, or 4 typically)
        
        Example:
            >>> order = await channel.error_low_pass_filter.get_order()
            >>> rolloff = order * 20  # dB/decade
            >>> print(f"{order}-order filter ({rolloff} dB/decade rolloff)")
        """
        result = await self._write(self.CMD_ORDER)
        return int(result[0])