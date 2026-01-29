from ...base.capabilities import MonitorOutputSource


class DDriveMonitorOutputSource(MonitorOutputSource):
    """d-Drive analog monitor output source selection.
    
    Defines internal signals that can be routed to the analog monitor
    output connector for real-time observation with oscilloscopes or
    other measurement equipment.
    
    Attributes:
        CLOSED_LOOP_POSITION: Closed-loop position value from sensor feedback.
        SETPOINT: Commanded target position (setpoint value).
        CONTROLLER_VOLTAGE: Internal amplifier control voltage.
        POSITION_ERROR: Position error signal (setpoint - actual position).
        POSITION_ERROR_ABS: Absolute value of position error.
        ACTUATOR_VOLTAGE: Actual voltage at piezo actuator.
        OPEN_LOOP_POSITION: Open-loop position value from sensor feedback.
    
    Example:
        >>> from psj_lib import DDriveMonitorOutputSource
        >>> # Monitor position error for tuning
        >>> await channel.monitor_output.set_source(
        ...     DDriveMonitorOutputSource.POSITION_ERROR
        ... )
        >>> # Monitor final output voltage
        >>> await channel.monitor_output.set_source(
        ...     DDriveMonitorOutputSource.ACTUATOR_VOLTAGE
        ... )
    
    Note:
        - Monitor output is a 0-10V analog signal
        - Useful for debugging, tuning PID, and system analysis
        - See device manual for detailed signal descriptions
    """
    CLOSED_LOOP_POSITION = 0
    SETPOINT = 1
    CONTROLLER_VOLTAGE = 2
    POSITION_ERROR = 3
    POSITION_ERROR_ABS = 4
    ACTUATOR_VOLTAGE = 5
    OPEN_LOOP_POSITION = 6