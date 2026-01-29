"""Trigger output generation capability."""

from enum import Enum

from .piezo_capability import PiezoCapability


class TriggerDataSource(Enum):
    """Data source for trigger generation.
    
    Determines which signal is monitored for trigger condition.
    
    Attributes:
        POSITION: Monitor actual position sensor value
        SETPOINT: Monitor commanded setpoint value
    """
    POSITION = 0
    SETPOINT = 1


class TriggerEdge(Enum):
    """Trigger edge detection mode.
    
    Configures which signal transitions generate trigger pulses.
    
    Attributes:
        DISABLED: No trigger output
        RISING: Trigger on upward crossings only
        FALLING: Trigger on downward crossings only
        BOTH: Trigger on both upward and downward crossings
    """
    DISABLED = 0
    RISING = 1
    FALLING = 2
    BOTH = 3


class TriggerOut(PiezoCapability):
    """Configure hardware trigger output generation.
    
    Generates digital trigger pulses when monitored signal crosses
    threshold values. Useful for synchronizing external equipment
    (cameras, data acquisition, etc.) with actuator movement.
    
    Trigger Options:
    - Window: Triggers when signal enters/exits range [start, stop]
    - Interval: Periodic triggers at fixed intervals within window
    - Edge sensitivity: Rising, falling, or both edges
    
    Example:
        >>> trigger = channel.trigger_out
        >>> # Trigger every 10µm from 20µm to 80µm
        >>> await trigger.set(
        ...     start_value=20.0,
        ...     stop_value=80.0,
        ...     interval=10.0,
        ...     length=100,  # 100 cycles pulse
        ...     edge=TriggerEdge.BOTH,
        ...     src=TriggerDataSource.POSITION
        ... )
        >>> # Query configuration
        >>> start = await trigger.get_start_value()
        >>> interval = await trigger.get_interval()
        >>> print(f"Trigger every {interval}µm from {start}µm")
    
    Note:
        - Trigger output is typically 0V/5V TTL signal
        - Pulse length in cycles (device-specific)
        - Interval generates periodic pulses in window
        - DISABLED edge stops all trigger output
    """
    
    CMD_START = "TRIGGER_OUT_START"
    CMD_STOP = "TRIGGER_OUT_STOP"
    CMD_INTERVAL = "TRIGGER_OUT_INTERVAL"
    CMD_LENGTH = "TRIGGER_OUT_LENGTH"
    CMD_EDGE = "TRIGGER_OUT_EDGE"
    CMD_SRC = "TRIGGER_OUT_SRC"
    
    async def set(
        self,
        start_value: float | None = None,
        stop_value: float | None = None,
        interval: float | None = None,
        length: int | None = None,
        edge: TriggerEdge | None = None,
        src: TriggerDataSource | None = None
    ) -> None:
        """Configure trigger output parameters.
        
        Args:
            start_value: Window start threshold (units match source)
            stop_value: Window stop threshold (units match source)
            interval: Periodic trigger spacing within window
            length: Trigger pulse duration cycles
            edge: Trigger edge detection mode
            src: Data source to monitor (position or setpoint)
        
        Example:
            >>> # Periodic triggers every 5µm
            >>> await channel.trigger_out.set(
            ...     start_value=0.0,
            ...     stop_value=100.0,
            ...     interval=5.0,
            ...     length=500  # 500 cycles pulse
            ... )
        
        Note:
            - Only provided parameters are updated
            - start_value should be less than stop_value
            - interval=0 disables periodic triggers
            - Units depend on selected source (typically µm or V)
        """
        if start_value is not None:
            await self._write(self.CMD_START, [start_value])

        if stop_value is not None:
            await self._write(self.CMD_STOP, [stop_value])

        if interval is not None:
            await self._write(self.CMD_INTERVAL, [interval])

        if length is not None:
            await self._write(self.CMD_LENGTH, [length])

        if edge is not None:
            await self._write(self.CMD_EDGE, [edge])

        if src is not None:
            await self._write(self.CMD_SRC, [src])

    async def get_start_value(self) -> float:
        """Get trigger window start threshold.
        
        Returns:
            Start value in source signal units
        """
        result = await self._write(self.CMD_START)
        return float(result[0])

    async def get_stop_value(self) -> float:
        """Get trigger window stop threshold.
        
        Returns:
            Stop value in source signal units
        """
        result = await self._write(self.CMD_STOP)
        return float(result[0])

    async def get_interval(self) -> float:
        """Get periodic trigger interval.
        
        Returns:
            Interval spacing in source signal units
        """
        result = await self._write(self.CMD_INTERVAL)
        return float(result[0])

    async def get_length(self) -> int:
        """Get trigger pulse duration.
        
        Returns:
            Pulse length in cycles
        """
        result = await self._write(self.CMD_LENGTH)
        return int(result[0])

    async def get_edge(self) -> TriggerEdge:
        """Get trigger edge detection mode.
        
        Returns:
            Current edge detection mode
        """
        result = await self._write(self.CMD_EDGE)
        return TriggerEdge(int(result[0]))

    async def get_src(self) -> TriggerDataSource:
        """Get trigger data source.
        
        Returns:
            Current monitored signal source
        """
        result = await self._write(self.CMD_SRC)
        return TriggerDataSource(int(result[0]))