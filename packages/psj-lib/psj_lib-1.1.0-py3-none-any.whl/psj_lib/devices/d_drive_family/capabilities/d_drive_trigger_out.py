from ...base.capabilities import TriggerDataSource, TriggerEdge, TriggerOut


class DDriveTriggerOut(TriggerOut):
    """d-Drive hardware trigger output with offset compensation.
    
    Extends base TriggerOut capability with an additional offset parameter
    for phase compensation. Generates TTL pulses synchronized with actuator
    position or setpoint values.
    
    The trigger output can generate pulses:
    - At specific position or voltage ranges
    - At regular intervals within those ranges
    - On rising, falling, or both edges
    - With configurable pulse width
    - With offset for phase/timing adjustment (d-Drive specific for setpoints)
    
    Example:
        >>> from psj_lib import TriggerEdge, TriggerDataSource
        >>> # Generate trigger every 10 µm from 20 to 80 µm
        >>> await channel.trigger_out.set(
        ...     start_value=20.0,
        ...     stop_value=80.0,
        ...     interval=10.0,  # Trigger every 10 µm
        ...     length=1000,    # 1000 cycle width (20 ms)
        ...     edge=TriggerEdge.BOTH,  # Trigger on up and down motion
        ...     src=TriggerDataSource.POSITION,
        ...     offset=0.5  # 0.5 µm phase compensation
        ... )
        >>> 
        >>> # Read current offset
        >>> current_offset = await channel.trigger_out.get_offset()
    
    Note:
        - Offset parameter is d-Drive specific extension
        - Trigger timing resolution depends on control loop rate (50 kHz)
        - Length specified in cycles (actual time = cycles * 20µs)
    """

    CMD_OFFSET = "TRIGGER_OUT_OFFSET"

    async def set(
        self,
        start_value: float | None = None,
        stop_value: float | None = None,
        interval: float | None = None,
        length: int | None = None,
        edge: TriggerEdge | None = None,
        src: TriggerDataSource | None = None,
        offset: float | None = None
    ) -> None:
        """Configure trigger output parameters including d-Drive offset.
        
        Args:
            start_value: Starting position/voltage for trigger window (in current units).
            stop_value: Ending position/voltage for trigger window (in current units).
            interval: Spacing between triggers within window (in current units).
                If None, single trigger at start_value.
            length: Trigger pulse width in microseconds.
            edge: Trigger on RISING, FALLING, or BOTH position crossings.
            src: Data source for trigger comparison (POSITION or SETPOINT).
            offset: Phase/timing offset in position units (d-Drive specific, see device manual).
        
        Example:
            >>> from psj_lib import TriggerEdge, TriggerDataSource
            >>> # Trigger every 5 µm during upward scan
            >>> await trigger_out.set(
            ...     start_value=10.0,
            ...     stop_value=90.0,
            ...     interval=5.0,
            ...     length=500,  # 500 cycle width (10 ms)
            ...     edge=TriggerEdge.RISING,
            ...     src=TriggerDataSource.POSITION,
            ...     offset=0.2  # Compensate 0.2 µm delay
            ... )
        
        Note:
            - All parameters optional; only specified values are updated
            - Offset unique to d-Drive
            - Trigger activates automatically when actuator enters window
        """
        await super().set(
            start_value=start_value,
            stop_value=stop_value,
            interval=interval,
            length=length,
            edge=edge,
            src=src
        )

        if offset is not None:
            await self._write(self.CMD_OFFSET, [offset])

    async def get_offset(self) -> float:
        """Read current trigger offset value.
        
        Returns:
            float: Trigger offset in position units.
        
        Example:
            >>> offset = await channel.trigger_out.get_offset()
            >>> print(f"Trigger offset: {offset:.3f} µm")
        
        Note:
            Offset is d-Drive specific parameter for phase compensation.
        """
        result = await self._write(self.CMD_OFFSET)
        return float(result[0])