"""d-Drive amplifier channel implementation with all capabilities.

Each d-Drive channel is an independent piezo amplifier with digital control,
providing high-precision positioning with 20-bit resolution and 50 kHz sampling.
"""

from ..d_drive_family_channel import DDriveFamilyChannel

class DDriveChannel(DDriveFamilyChannel):
    """Single d-Drive amplifier channel with all control capabilities.
    
    Each d-Drive channel provides complete control of one piezoelectric
    actuator with:
    
    Hardware Specifications (from d-Drive manual):
    - 20-bit resolution
    - 50 kHz sampling rate (20µs control loop period)
    - Digital PID controller with feedforward (PCF)
    - Multiple filter stages:
      * Notch filter (resonance suppression)
      * Low-pass filter (noise reduction)
      * Error low-pass filter (PID stability)
    
    Signal Generation:
    - Waveform generator (sine, triangle, rectangle, sweep, noise)
    - Modulation input (external analog or internal waveform)
    - Analog monitor output (configurable signal routing)
    
    Data Acquisition:
    - Two-channel data recorder
    - 500,000 samples per channel maximum
    - 50 kHz max sample rate with stride (decimation) support
    - Channel 1: position signal, Channel 2: actuator voltage
    
    Trigger System:
    - Hardware trigger output (TTL)
    - Window mode with start/stop thresholds
    - Periodic triggers with configurable interval
    - Edge detection (rising, falling, both)
    
    Attributes:
        SAMPLE_PERIOD: Control loop period in microseconds (20µs = 50kHz)
        BACKUP_COMMANDS: Channel-specific commands included in backup
    
    Example:
        >>> channel = device.channels[0]
        >>> 
        >>> # Configure closed-loop control with PID tuning
        >>> await channel.closed_loop_controller.set(True)
        >>> await channel.pid_controller.set(p=10.0, i=5.0, d=0.5)
        >>> 
        >>> # Enable notch filter to suppress 500 Hz resonance
        >>> await channel.notch.set(
        ...     enabled=True,
        ...     frequency=500.0,
        ...     bandwidth=50.0
        ... )
        >>> 
        >>> # Generate 10 Hz sine wave for scanning
        >>> await channel.waveform_generator.sine.set(
        ...     amplitude=20.0,
        ...     offset=50.0,
        ...     frequency=10.0
        ... )
        >>> await channel.waveform_generator.set_waveform_type(
        ...     WaveformType.SINE
        ... )
        >>> 
        >>> # Configure data recorder for 1 second capture
        >>> await channel.data_recorder.set(
        ...     memory_length=50000,  # 50k samples at 50kHz = 1 sec
        ...     stride=1  # No decimation
        ... )

    
    Note:
        - Sample period defines control loop and data recorder timing
        - Capabilities are accessed as properties (e.g., channel.setpoint)
        - Hardware-specific enums defined in d_drive_family/capabilities/
    """
