"""Closed-loop control capability."""

from .piezo_capability import PiezoCapability


class ClosedLoopController(PiezoCapability):
    """Enable or disable closed-loop position control.
    
    Closed-loop control uses sensor feedback to actively maintain the
    actuator at the desired setpoint position. When enabled, the
    controller compensates for drift, hysteresis, and external loads.
    
    When disabled (open-loop), the actuator operates with direct voltage
    control without position feedback.

    Depending on the device, different closed loop algorithms may be available.
    In this case, the device will provide a derived controller class with additional
    methods to configure the specific algorithm type. 
    
    Example:
        >>> controller = channel.closed_loop_controller
        >>> # Enable closed-loop control
        >>> await controller.set(True)
        >>> # Check if enabled
        >>> is_enabled = await controller.get_enabled()
        >>> print(f"Closed-loop: {'On' if is_enabled else 'Off'}")
    
    Note:
        - Requires position sensor for feedback
        - Provides better accuracy and stability than open-loop
        - May have slower response than open-loop
        - PID parameters affect closed-loop performance
    """
    
    CMD_ENABLE = "CLOSED_LOOP_CONTROLLER_ENABLE"

    def __init__(
        self, 
        write_cb, 
        device_commands,
        sample_period: int
    ):
        super().__init__(write_cb, device_commands)
        self._sample_period = sample_period

    async def set(self, enabled: bool) -> None:
        """Enable or disable closed-loop control.
        
        Args:
            enabled: True to enable closed-loop, False for open-loop
        
        Example:
            >>> # Enable closed-loop for precise positioning
            >>> await channel.closed_loop_controller.set(True)
            >>> # Disable for faster response (open-loop)
            >>> await channel.closed_loop_controller.set(False)
        
        Note:
            - Changing mode may cause position jump
            - Closed-loop requires properly tuned PID parameters
        """
        await self._write(self.CMD_ENABLE, [enabled])

    async def get_enabled(self) -> bool:
        """Check if closed-loop control is currently enabled.
        
        Returns:
            True if closed-loop enabled, False if open-loop
        
        Example:
            >>> if await channel.closed_loop_controller.get_enabled():
            ...     print("Using closed-loop control")
            ... else:
            ...     print("Using open-loop control")
        """
        result = await self._write(self.CMD_ENABLE)
        return bool(int(result[0]))
    
    @property
    def sample_period(self) -> int:
        """Get the closed-loop controller sampling period in microseconds.
        
        The sampling period defines how often the controller updates its
        output based on the position feedback. A shorter period allows
        for faster response but may increase noise sensitivity.
        
        Returns:
            Sampling period in microseconds
        
        Example:
            >>> period = channel.closed_loop_controller.sample_period
            >>> print(f"Controller sampling period: {period} µs")
            >>> freq = 1000000 / period
            >>> print(f"Control loop frequency: {freq:.0f} Hz")
        """
        return self._sample_period
