"""PID controller parameter configuration."""

from .piezo_capability import PiezoCapability


class PIDController(PiezoCapability):
    """Configure PID controller parameters for closed-loop operation.
    
    Provides access to Proportional, Integral, Derivative, and differential
    filter parameters that control closed-loop positioning behavior.
    
    PID Control Theory:
    - P (Proportional): Response proportional to error. Higher = faster but may overshoot
    - I (Integral): Eliminates steady-state error. Too high causes oscillation
    - D (Derivative): Dampens oscillation. Higher = more damping but noise sensitive
    - TF (Diff Filter): Filters derivative term to reduce noise amplification
    
    Example:
        >>> pid = channel.pid_controller
        >>> # Set aggressive PID for fast response
        >>> await pid.set(p=10.0, i=5.0, d=0.5, diff_filter=100.0)
        >>> # Read current parameters
        >>> p = await pid.get_p()
        >>> i = await pid.get_i()
        >>> print(f"PID: P={p}, I={i}")
    
    Note:
        - Improper tuning causes poor performance and possible damage to actuator!
        - Start with conservative values and tune incrementally
        - Only active when closed-loop control is enabled
        - Parameter ranges are device-specific
    """
    
    CMD_P = "PID_CONTROLLER_P"
    CMD_I = "PID_CONTROLLER_I"
    CMD_D = "PID_CONTROLLER_D"
    CMD_TF = "PID_CONTROLLER_TF"

    async def set(
        self,
        p: float | None = None,
        i: float | None = None,
        d: float | None = None,
        diff_filter: float | None = None
    ) -> None:
        """Set PID controller parameters.
        
        Parameters are set independently - only provided values are updated.
        Omitted parameters remain unchanged.
        
        Args:
            p: Proportional gain (higher = faster response, more overshoot)
            i: Integral gain (eliminates steady-state error)
            d: Derivative gain (dampens oscillation)
            diff_filter: Differential filter time constant (noise reduction)
        
        Example:
            >>> # Set only P and I, leave D and filter unchanged
            >>> await channel.pid_controller.set(p=8.0, i=4.0)
            >>> 
            >>> # Fine-tune all parameters
            >>> await channel.pid_controller.set(
            ...     p=12.0, i=6.0, d=0.01, diff_filter=150.0
            ... )
        
        Note:
            - Units and ranges are device-specific
            - Test parameter changes with small movements first
            - Higher D gains amplify sensor noise (use diff_filter)
        """
        if p is not None:
            await self._write(self.CMD_P, [p])

        if i is not None:
            await self._write(self.CMD_I, [i])

        if d is not None:
            await self._write(self.CMD_D, [d])

        if diff_filter is not None:
            await self._write(self.CMD_TF, [diff_filter])

    async def get_p(self) -> float:
        """Get proportional gain parameter.
        
        Returns:
            Current P (proportional) gain value
        
        Example:
            >>> p_gain = await channel.pid_controller.get_p()
        """
        result = await self._write(self.CMD_P)
        return float(result[0])

    async def get_i(self) -> float:
        """Get integral gain parameter.
        
        Returns:
            Current I (integral) gain value
        
        Example:
            >>> i_gain = await channel.pid_controller.get_i()
        """
        result = await self._write(self.CMD_I)
        return float(result[0])

    async def get_d(self) -> float:
        """Get derivative gain parameter.
        
        Returns:
            Current D (derivative) gain value
        
        Example:
            >>> d_gain = await channel.pid_controller.get_d()
        """
        result = await self._write(self.CMD_D)
        return float(result[0])

    async def get_diff_filter(self) -> float:
        """Get differential filter time constant.
        
        Returns:
            Current differential filter value
        
        Example:
            >>> tf = await channel.pid_controller.get_diff_filter()
        """
        result = await self._write(self.CMD_TF)
        return float(result[0])