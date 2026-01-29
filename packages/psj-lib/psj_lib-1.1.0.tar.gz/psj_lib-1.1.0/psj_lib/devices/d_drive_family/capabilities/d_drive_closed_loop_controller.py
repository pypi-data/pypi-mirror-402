"""d-Drive specific closed-loop controller implementation."""

from ...base.capabilities import ClosedLoopController


class DDriveClosedLoopController(ClosedLoopController):
    """d-Drive closed-loop controller with status register reading.
    
    This d-Drive specific implementation reads the closed-loop state from
    the device status register rather than using a dedicated command.
    The closed-loop enable bit is bit 7 (0x80) of the status register.
    
    The d-Drive operates at 50 kHz (20 µs sample period) in closed-loop mode,
    providing high-bandwidth position control with the digital PID controller.
    
    Example:
        >>> controller = channel.closed_loop_controller
        >>> # Enable closed-loop control
        >>> await controller.set(True)
        >>> # Check if enabled by reading status register
        >>> is_enabled = await controller.get_enabled()
        >>> print(f"Closed-loop: {'Active' if is_enabled else 'Inactive'}")
        >>> # Get sample period
        >>> period = controller.sample_period
        >>> print(f"Control loop: {1000000 / period:.0f} Hz")
    
    Note:
        - Sample period is 20 µs (50 kHz control loop)
        - Status is read from hardware status register bit 7
        - Closed-loop requires properly tuned PID parameters
        - Sensor must be present and functioning
    """
    
    CMD_STATUS = "STATUS"

    async def get_enabled(self) -> bool:
        """Check if closed-loop control is enabled via status register.
        
        Reads the device status register and extracts bit 7 (0x80) which
        indicates whether closed-loop control is currently active.
        
        Returns:
            True if closed-loop enabled, False if open-loop
        
        Example:
            >>> if await channel.closed_loop_controller.get_enabled():
            ...     print("Running in closed-loop mode")
            ... else:
            ...     print("Running in open-loop mode")
        
        Note:
            This performs a hardware read of the status register,
            not a cached value.
        """
        # Read closed loop enabled state from status register
        status = await self._write(self.CMD_STATUS)

        # Bit 7 (0x80) indicates closed-loop enabled
        return bool(int(status[0]) & 0x80)
