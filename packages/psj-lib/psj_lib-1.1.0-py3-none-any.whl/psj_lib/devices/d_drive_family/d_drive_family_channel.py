"""d-Drive amplifier channel implementation with all capabilities.

Each d-Drive channel is an independent piezo amplifier with digital control,
providing high-precision positioning with 20-bit resolution and 50 kHz sampling.
"""

from ..base.piezo_channel import PiezoChannel
from ..base.capabilities import *
from .capabilities.d_drive_closed_loop_controller import DDriveClosedLoopController
from .capabilities.d_drive_data_recorder import DDriveDataRecorder
from .capabilities.d_drive_modulation_source import DDriveModulationSourceTypes
from .capabilities.d_drive_setpoint import DDriveSetpoint
from .capabilities.d_drive_status_register import DDriveStatusRegister
from .capabilities.d_drive_trigger_out import DDriveTriggerOut
from .capabilities.d_drive_waveform_generator import DDriveWaveformGenerator

class DDriveFamilyChannel(PiezoChannel):
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
        - Hardware-specific enums defined in d_drive/capabilities/
    """

    SAMPLE_PERIOD: int = 20  # Sample period in microseconds of control loop
    """Control loop sample period in microseconds.
    
    The d-Drive control loop runs at 50 kHz (20µs period). This timing
    affects:
    - PID controller update rate
    - Data recorder maximum sample rate (50 kHz)
    - Waveform generator resolution
    - Trigger output timing
    
    Note:
        - 20µs period = 50 kHz sampling frequency
        - Actual system bandwidth depends on actuator and filters
    """

    BACKUP_COMMANDS: set[str] = {
        "modon",
        "monsrc",
        "cl",
        "sr",
        "pcf",
        "errlpf",
        "elpor",
        "kp",
        "ki",
        "kd",
        "tf",
        "notchon",
        "notchf",
        "notchb",
        "lpon",
        "lpf",
        "gfkt",
        "gasin",
        "gosin",
        "gfsin",
        "gatri",
        "gotri",
        "gftri",
        "gstri",
        "garec",
        "gorec",
        "gfrec",
        "gsrec",
        "ganoi",
        "gonoi",
        "gaswe",
        "goswe",
        "gtswe",
        "sct",
        "trgss",
        "trgse",
        "trgsi",
        "trglen",
        "trgedge",
        "trgsrc",
        "trgos",
    }
    """d-Drive commands to include in backup operations.
    
    These commands represent channel configuration that should be saved
    and restored during backup/restore operations. Includes:
    - Control parameters (PID, slew rate, PCF)
    - Filter settings (notch, low-pass, error filter)
    - Waveform generator configuration
    - Trigger and recorder settings
    - Display and monitoring configuration
    
    Note:
        - Dynamic state (position, setpoint) not included
        - Only configuration parameters are backed up
    """
    
    # Capability descriptors
    status_register: Status = CapabilityDescriptor(
        Status, {
            Status.CMD_STATUS: "stat"
        },
        register_type=DDriveStatusRegister
    )
    """d-Drive status register with hardware state information.
    
    Provides real-time status including:
    - actor_plugged: Whether actuator is connected
    - sensor_type: Type of position sensor (STRAIN_GAUGE, CAPACITIVE, etc.)
    - piezo_voltage_enabled: Output voltage enable state
    - closed_loop: Closed-loop control active status
    - waveform_generator_status: Current waveform type (SINE, TRIANGLE, etc.)
    - notch_filter_active: Notch filter enable state
    - low_pass_filter_active: Low-pass filter enable state
    
    Example:
        >>> status = await channel.status_register.get()
        >>> if status.actor_plugged:
        ...     print(f"Sensor: {status.sensor_type.name}")
        ...     print(f"Closed-loop: {status.closed_loop}")
    """

    actuator_description: ActuatorDescription = CapabilityDescriptor(
        ActuatorDescription, {
            ActuatorDescription.CMD_DESCRIPTION: "acdescr"
        }
    )
    """Actuator description and identification.
    
    Retrieves human-readable description of connected piezo actuator.
    
    Example:
        >>> desc = await channel.actuator_description.get()
        >>> print(f"Actuator: {desc}")
    """

    setpoint: DDriveSetpoint = CapabilityDescriptor(
        DDriveSetpoint, {
            DDriveSetpoint.CMD_SETPOINT: "set"
        }
    )
    """Target position control (commanded position).
    
    Set and read the desired actuator position. In closed-loop mode,
    the controller actively drives to this position. In open loop mode,
    the setpoint acts as the voltage output to the actuator.
    
    Example:
        >>> await channel.setpoint.set(75.0)  # Move to 75 µm
        >>> target = await channel.setpoint.get()
    """

    position: Position = CapabilityDescriptor(
        Position, {
            Position.CMD_POSITION: "mess"
        }
    )
    """Actual position readback from sensor.
    
    Reads the current measured position from the actuator's position sensor.
    In closed-loop mode, this is the feedback value.
    In open loop mode, this is the output voltage.

    Please note that for d-Drive devices, the position value is only updated every 500ms.

    Example:
        >>> pos = await channel.position.get()
        >>> print(f"Current position: {pos:.3f} µm")
    """

    temperature: Temperature = CapabilityDescriptor(
        Temperature, {
            Temperature.CMD_TEMPERATURE: "ktemp"
        }
    )
    """Channel electronics temperature monitoring.
    
    Reads internal temperature of the amplifier electronics for
    thermal management and diagnostics.
    
    Example:
        >>> temp = await channel.temperature.get()
        >>> print(f"Temperature: {temp:.1f}°C")
    """

    fan: Fan = CapabilityDescriptor(
        Fan, {
            Fan.CMD_ENABLE: "fan"
        }
    )
    """Cooling fan control for thermal management.
    
    Enable or disable the channel's cooling fan.
    
    Example:
        >>> await channel.fan.set(True)  # Enable fan
        >>> is_on = await channel.fan.get_enabled()
    """

    modulation_source: ModulationSource = CapabilityDescriptor(
        ModulationSource, {
            ModulationSource.CMD_SOURCE: "modon"
        },
        sources=DDriveModulationSourceTypes
    )
    """Modulation input source selection.
    
    Select modulation source from d-Drive specific options:
    - SERIAL_ENCODER: Serial encoder input
    - SERIAL_ENCODER_ANALOG: Analog serial encoder
    
    Example:
        >>> from psj_lib import DDriveModulationSourceTypes
        >>> await channel.modulation_source.set_source(
        ...     DDriveModulationSourceTypes.SERIAL_ENCODER
        ... )
    """

    monitor_output: MonitorOutput = CapabilityDescriptor(
        MonitorOutput, {
            MonitorOutput.CMD_OUTPUT_SRC: "monsrc"
        }
    )
    """Analog monitor output source routing.
    
    Route internal signals to analog monitor output connector.
    Available sources:
    - CLOSED_LOOP_POSITION: Closed-loop position value
    - SETPOINT: Commanded setpoint
    - CONTROLLER_VOLTAGE: PID controller output
    - POSITION_ERROR: Setpoint - position error
    - POSITION_ERROR_ABS: Absolute position error
    - ACTUATOR_VOLTAGE: Output voltage to actuator
    - OPEN_LOOP_POSITION: Open-loop position estimate
    
    Example:
        >>> from psj_lib import DDriveMonitorOutputSource
        >>> await channel.monitor_output.set_source(
        ...     DDriveMonitorOutputSource.POSITION_ERROR
        ... )
    """

    closed_loop_controller: DDriveClosedLoopController = CapabilityDescriptor(
        DDriveClosedLoopController, {
            DDriveClosedLoopController.CMD_ENABLE: "cl",
            DDriveClosedLoopController.CMD_STATUS: "stat"
        },
        sample_period=SAMPLE_PERIOD
    )
    """Closed-loop position control enable/disable.
    
    Enable sensor-based feedback control for precise positioning.

    To configure the closed-loop PID controller, use the `pid_controller` property.
    
    Example:
        >>> await channel.closed_loop_controller.set(True)
        >>> is_closed = await channel.closed_loop_controller.get_enabled()
    """

    slew_rate: SlewRate = CapabilityDescriptor(
        SlewRate, {
            SlewRate.CMD_RATE: "sr"
        }
    )
    """Maximum rate of change limiting.
    
    Limits how fast the actuator can change position, providing
    smooth motion and protecting actuators and samples.
    
    Example:
        >>> await channel.slew_rate.set(10.0)  # 10 V/ms
        >>> rate = await channel.slew_rate.get()
    """

    pcf: PreControlFactor = CapabilityDescriptor(
        PreControlFactor, {
            PreControlFactor.CMD_VALUE: "pcf"
        }
    )
    """Pre-control factor for feedforward compensation.
    
    Provides feedforward control to improve response speed and
    reduce tracking error in closed-loop operation.
    
    Example:
        >>> await channel.pcf.set(0.5)  # 50% feedforward
        >>> pcf_val = await channel.pcf.get()
    """

    error_lpf: ErrorLowPassFilter = CapabilityDescriptor(
        ErrorLowPassFilter, {
            ErrorLowPassFilter.CMD_CUTOFF_FREQUENCY: "errlpf",
            ErrorLowPassFilter.CMD_ORDER: "elpor"
        }
    )
    """Error signal low-pass filter for PID input.
    
    Filters the position error signal before PID controller to
    reduce noise and improve stability.
    
    Example:
        >>> await channel.error_lpf.set(
        ...     cutoff_frequency=200.0,  # 200 Hz
        ...     order=2  # 2nd order filter
        ... )
    """

    pid_controller: PIDController = CapabilityDescriptor(
        PIDController, {
            PIDController.CMD_P: "kp",
            PIDController.CMD_I: "ki",
            PIDController.CMD_D: "kd",
            PIDController.CMD_TF: "tf"
        }
    )
    """PID controller parameter configuration.
    
    Configure Proportional, Integral, Derivative, and differential
    filter (TF) parameters for closed-loop control.
    
    Example:
        >>> await channel.pid_controller.set(
        ...     p=10.0,  # Proportional gain
        ...     i=5.0,   # Integral gain
        ...     d=0.5,   # Derivative gain
        ...     diff_filter=100.0  # Diff filter time constant
        ... )
    """

    notch: NotchFilter = CapabilityDescriptor(
        NotchFilter, {
            NotchFilter.CMD_ENABLE: "notchon",
            NotchFilter.CMD_FREQUENCY: "notchf",
            NotchFilter.CMD_BANDWIDTH: "notchb"
        }
    )
    """Notch filter for mechanical resonance suppression.
    
    Attenuates specific frequencies to suppress resonances that
    can cause instability in closed-loop systems.
    
    Example:
        >>> await channel.notch.set(
        ...     enabled=True,
        ...     frequency=500.0,  # Suppress 500 Hz resonance
        ...     bandwidth=50.0    # 50 Hz bandwidth
        ... )
    """

    lpf: LowPassFilter = CapabilityDescriptor(
        LowPassFilter, {
            LowPassFilter.CMD_ENABLE: "lpon",
            LowPassFilter.CMD_CUTOFF_FREQUENCY: "lpf"
        }
    )
    """Low-pass filter for signal conditioning.
    
    Reduces high-frequency noise in position or control signals.
    
    Example:
        >>> await channel.lpf.set(
        ...     enabled=True,
        ...     cutoff_frequency=100.0  # 100 Hz cutoff
        ... )
    """

    trigger_out: DDriveTriggerOut = CapabilityDescriptor(
        DDriveTriggerOut, {
            DDriveTriggerOut.CMD_START: "trigstart",
            DDriveTriggerOut.CMD_STOP: "trigstop",
            DDriveTriggerOut.CMD_INTERVAL: "trigint",
            DDriveTriggerOut.CMD_LENGTH: "triglen",
            DDriveTriggerOut.CMD_EDGE: "trigedge",
            DDriveTriggerOut.CMD_SRC: "trigsrc",
            DDriveTriggerOut.CMD_OFFSET: "trigoffset"
        }
    )
    """Hardware trigger output generation.
    
    d-Drive specific trigger output with additional offset parameter. 
    Generates TTL pulses synchronized with actuator position or setpoint.
    
    Example:
        >>> from psj_lib import TriggerEdge, TriggerDataSource
        >>> await channel.trigger_out.set(
        ...     start_value=20.0,  # Start at 20 µm
        ...     stop_value=80.0,   # Stop at 80 µm
        ...     interval=10.0,     # Trigger every 10 µm
        ...     length=1000,       # 1000 µs pulse
        ...     edge=TriggerEdge.BOTH,
        ...     src=TriggerDataSource.POSITION,
        ...     offset=0.0  # d-Drive specific offset parameter
        ... )
    """

    data_recorder: DDriveDataRecorder = CapabilityDescriptor(
        DDriveDataRecorder, {
            DataRecorder.CMD_START_RECORDING: "recstart",
            DataRecorder.CMD_STRIDE: "recstride",
            DataRecorder.CMD_MEMORY_LENGTH: "reclen",
            DataRecorder.CMD_PTR: "recrdptr",
            DataRecorder.CMD_GET_DATA_1: "m",
            DataRecorder.CMD_GET_DATA_2: "u"
        },
        sample_period=SAMPLE_PERIOD
    )
    """Two-channel data recorder for signal capture.
    
    Records position (channel 1) and voltage (channel 2) at up to
    50 kHz (20 µs period). Maximum 500,000 samples per channel.
    
    Channel mapping:
    - Channel 1: Position sensor signal
    - Channel 2: Actuator voltage
    
    The waveform generator is automatically started when sending a new setpoint,
    starting a waveform output or starting a scan.

    Example:
        >>> from psj_lib import DDriveDataRecorderChannel
        >>> # Configure for 1 second at 50 kHz
        >>> await channel.data_recorder.set(
        ...     memory_length=50000,
        ...     stride=1  # No decimation
        ... )
        >>> await channel.data_recorder.start()
        >>> # ... perform motion ...
        >>> position_data = await channel.data_recorder.get_all_data(
        ...     DDriveDataRecorderChannel.POSITION
        ... )
        >>> voltage_data = await channel.data_recorder.get_all_data(
        ...     DDriveDataRecorderChannel.VOLTAGE
        ... )
    
    Note:
        - Sample period = 20 µs (50 kHz max rate)
        - Both channels always record same length
        - Use stride for longer durations at lower rate
    """

    waveform_generator: DDriveWaveformGenerator = CapabilityDescriptor(
        DDriveWaveformGenerator, {
            DDriveWaveformGenerator.CMD_WFG_TYPE: "gfkt",
            DDriveWaveformGenerator.CMD_SINE_AMPLITUDE: "gasin",
            DDriveWaveformGenerator.CMD_SINE_OFFSET: "gosin",
            DDriveWaveformGenerator.CMD_SINE_FREQUENCY: "gfsin",
            DDriveWaveformGenerator.CMD_TRI_AMPLITUDE: "gatri",
            DDriveWaveformGenerator.CMD_TRI_OFFSET: "gotri",
            DDriveWaveformGenerator.CMD_TRI_FREQUENCY: "gftri",
            DDriveWaveformGenerator.CMD_TRI_DUTY_CYCLE: "gstri",
            DDriveWaveformGenerator.CMD_REC_AMPLITUDE: "garec",
            DDriveWaveformGenerator.CMD_REC_OFFSET: "gorec",
            DDriveWaveformGenerator.CMD_REC_FREQUENCY: "gfrec",
            DDriveWaveformGenerator.CMD_REC_DUTY_CYCLE: "gsrec",
            DDriveWaveformGenerator.CMD_NOISE_AMPLITUDE: "ganoi",
            DDriveWaveformGenerator.CMD_NOISE_OFFSET: "gonoi",
            DDriveWaveformGenerator.CMD_SWEEP_AMPLITUDE: "gaswe",
            DDriveWaveformGenerator.CMD_SWEEP_OFFSET: "goswe",
            DDriveWaveformGenerator.CMD_SWEEP_TIME: "gtswe",
            DDriveWaveformGenerator.CMD_SCAN_START: "ss",
            DDriveWaveformGenerator.CMD_SCAN_TYPE: "sct"
        }
    )
    """Multi-waveform generator for scanning and modulation.
    
    d-Drive waveform generator supporting multiple waveform types:
    - SINE: Sinusoidal waveform
    - TRIANGLE: Triangular waveform with adjustable duty cycle
    - RECTANGLE: Square/rectangle wave with duty cycle
    - NOISE: Random noise for dithering
    - SWEEP: Linear sweep (ramp)
    
    Each waveform type has dedicated configuration via properties:
    - waveform_generator.sine: Sine wave parameters
    - waveform_generator.triangle: Triangle wave parameters
    - waveform_generator.rectangle: Rectangle wave parameters
    - waveform_generator.noise: Noise parameters
    - waveform_generator.sweep: Sweep/ramp parameters

    For sweep waveform, the frequency parameter acts as the time in seconds
    to complete one full sweep cycle (0.1 Hz to 10kHz).
    
    Scan function for automated single or double scans.

    Example:
        >>> from psj_lib import DDriveWaveformType, DDriveScanType
        >>> # Configure sine wave
        >>> await channel.waveform_generator.sine.set(
        ...     amplitude=20.0,  # 20 µm peak-to-peak
        ...     offset=50.0,     # Centered at 50 µm
        ...     frequency=10.0   # 10 Hz
        ... )
        >>> # Activate sine waveform
        >>> await channel.waveform_generator.set_waveform_type(
        ...     DDriveWaveformType.SINE
        ... )
        >>> 
        >>> # Configure triangle with asymmetric duty cycle
        >>> await channel.waveform_generator.triangle.set(
        ...     amplitude=30.0,
        ...     offset=50.0,
        ...     frequency=5.0,
        ...     duty_cycle=70.0  # 70% rise, 30% fall
        ... )
        >>> await channel.waveform_generator.set_waveform_type(
        ...     DDriveWaveformType.TRIANGLE
        ... )
        >>> 
        >>> # Start automated scan
        >>> from psj_lib import DDriveScanType
        >>> await channel.waveform_generator.start_scan(
        ...     DDriveScanType.TRIANGLE_ONCE
        ... )
    
    Note:
        - Set waveform parameters before activating type
        - By setting a waveform type, the generator is started. To stop, set type to NONE.
        - Only one waveform type active at a time
        - Scan function provides automated scanning sequences
        - Check status with get_waveform_type() or is_scan_running()
    """

    async def backup(self) -> dict[str, list[str]]:
        data = await super().backup()

        # Override cl command to use status register
        data["cl"] = [str(int(await self.closed_loop_controller.get_enabled()))]

        return data