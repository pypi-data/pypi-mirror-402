from enum import Enum

from ...base.capabilities import PiezoCapability, StaticWaveformGenerator


class DDriveWaveformType(Enum):
    """d-Drive waveform generator output types.
    
    Defines the types of waveforms available from the d-Drive's built-in
    waveform generator for scanning and modulation applications.
    
    Attributes:
        NONE: No waveform output (generator disabled)
        SINE: Sinusoidal waveform
        TRIANGLE: Triangular waveform
        RECTANGLE: Square/rectangular waveform
        NOISE: Random noise
        SWEEP: Linear frequency sweep/ramp
        UNKNOWN: Unrecognized waveform type (error condition)
    
    Example:
        >>> from psj_lib import DDriveWaveformType
        >>> await channel.waveform_generator.set_waveform_type(
        ...     DDriveWaveformType.SINE
        ... )
    """
    NONE = 0
    SINE = 1
    TRIANGLE = 2
    RECTANGLE = 3
    NOISE = 4
    SWEEP = 5
    UNKNOWN = 99


class DDriveScanType(Enum):
    """d-Drive automated scan patterns.
    
    Defines automated scan sequences for the waveform generator, providing
    single or double scan cycles with different waveform shapes.
    
    Attributes:
        OFF: No automated scanning
        SINE_ONCE: Single sinusoidal scan (one complete cycle)
        TRIANGLE_ONCE: Single triangular scan (up and down)
        SINE_TWICE: Double sinusoidal scan (two complete cycles)
        TRIANGLE_TWICE: Double triangular scan (two up/down cycles)
        UNKNOWN: Unrecognized scan type (error condition)
    
    Example:
        >>> from psj_lib import DDriveScanType
        >>> # Start single triangle scan
        >>> await channel.waveform_generator.start_scan(
        ...     DDriveScanType.TRIANGLE_ONCE
        ... )
        >>> # Wait for completion
        >>> while await channel.waveform_generator.is_scan_running():
        ...     await asyncio.sleep(0.1)
    
    Note:
        Scan automatically stops after completing specified cycles.
    """
    OFF = 0
    SINE_ONCE = 1
    TRIANGLE_ONCE = 2
    SINE_TWICE = 3
    TRIANGLE_TWICE = 4
    UNKNOWN = 99


class DDriveWaveformGenerator(PiezoCapability):
    """d-Drive multi-waveform generator for scanning and modulation.
    
    Provides built-in waveform generation with multiple waveform types for
    automated scanning, periodic motion, and signal modulation. Each waveform
    type has independent parameter configuration.
    
    Available waveforms:
    - SINE: Sinusoidal motion with amplitude, offset, and frequency control
    - TRIANGLE: Triangular scanning with adjustable duty cycle
    - RECTANGLE: Square wave with duty cycle control
    - NOISE: Random noise
    - SWEEP: Linear frequency sweep/ramp
    
    Features:
    - Multiple waveform types with independent parameters
    - Sub-generator properties for each waveform type
    - Automated scan sequences (single or double cycles)
    - Synchronous with 50 kHz control loop
    
    Example:
        >>> from psj_lib import DDriveWaveformType, DDriveScanType
        >>> wfg = channel.waveform_generator
        >>> 
        >>> # Configure sine wave for 10 Hz scanning
        >>> await wfg.sine.set(
        ...     amplitude=20.0,  # 20 µm peak-to-peak
        ...     offset=50.0,     # Center at 50 µm
        ...     frequency=10.0   # 10 Hz
        ... )
        >>> await wfg.set_waveform_type(DDriveWaveformType.SINE)
        >>> 
        >>> # Configure triangle with asymmetric duty cycle
        >>> await wfg.triangle.set(
        ...     amplitude=30.0,
        ...     offset=50.0,
        ...     frequency=5.0,
        ...     duty_cycle=70.0  # 70% rise, 30% fall
        ... )
        >>> await wfg.set_waveform_type(DDriveWaveformType.TRIANGLE)
        >>> 
        >>> # Start automated single scan
        >>> await wfg.start_scan(DDriveScanType.TRIANGLE_ONCE)
        >>> while await wfg.is_scan_running():
        ...     await asyncio.sleep(0.1)
    
    Properties:
        sine: Sine waveform sub-generator configuration
        triangle: Triangle waveform sub-generator configuration
        rectangle: Rectangle waveform sub-generator configuration
        noise: Noise generator configuration
        sweep: Sweep/ramp generator configuration
    
    Note:
        - Configure waveform parameters before activating type
        - Only one waveform type active at a time
        - Waveform generation rate synchronized with control loop (50 kHz)
    """
    CMD_WFG_TYPE = "WFG_TYPE"
    CMD_SINE_AMPLITUDE = "WFG_SINE_AMPLITUDE"
    CMD_SINE_OFFSET = "WFG_SINE_OFFSET"
    CMD_SINE_FREQUENCY = "WFG_SINE_FREQUENCY"
    CMD_TRI_AMPLITUDE = "WFG_TRIANGLE_AMPLITUDE"
    CMD_TRI_OFFSET = "WFG_TRIANGLE_OFFSET"
    CMD_TRI_FREQUENCY = "WFG_TRIANGLE_FREQUENCY"
    CMD_TRI_DUTY_CYCLE = "WFG_TRIANGLE_DUTY_CYCLE"
    CMD_REC_AMPLITUDE = "WFG_RECTANGLE_AMPLITUDE"
    CMD_REC_OFFSET = "WFG_RECTANGLE_OFFSET"
    CMD_REC_FREQUENCY = "WFG_RECTANGLE_FREQUENCY"
    CMD_REC_DUTY_CYCLE = "WFG_RECTANGLE_DUTY_CYCLE"
    CMD_NOISE_AMPLITUDE = "WFG_NOISE_AMPLITUDE"
    CMD_NOISE_OFFSET = "WFG_NOISE_OFFSET"
    CMD_SWEEP_AMPLITUDE = "WFG_SWEEP_AMPLITUDE"
    CMD_SWEEP_OFFSET = "WFG_SWEEP_OFFSET"
    CMD_SWEEP_TIME = "WFG_SWEEP_TIME"
    CMD_SCAN_START = "WFG_SCAN_START"
    CMD_SCAN_TYPE = "WFG_SCAN_TYPE"


    def __init__(
        self,
        write_cb,
        device_commands
    ) -> None:
        super().__init__(write_cb, device_commands)

        # Register waveform types
        self._sine = StaticWaveformGenerator(
            self._write_cb,
            {
                StaticWaveformGenerator.CMD_AMPLITUDE: self._device_commands[self.CMD_SINE_AMPLITUDE],
                StaticWaveformGenerator.CMD_OFFSET: self._device_commands[self.CMD_SINE_OFFSET],
                StaticWaveformGenerator.CMD_FREQUENCY: self._device_commands[self.CMD_SINE_FREQUENCY],
            }
        )

        self._triangle = StaticWaveformGenerator(
            self._write_cb,
            {
                StaticWaveformGenerator.CMD_AMPLITUDE: self._device_commands[self.CMD_TRI_AMPLITUDE],
                StaticWaveformGenerator.CMD_OFFSET: self._device_commands[self.CMD_TRI_OFFSET],
                StaticWaveformGenerator.CMD_FREQUENCY: self._device_commands[self.CMD_TRI_FREQUENCY],
                StaticWaveformGenerator.CMD_DUTY_CYCLE: self._device_commands[self.CMD_TRI_DUTY_CYCLE],
            }
        )

        self._rectangle = StaticWaveformGenerator(
            self._write_cb,
            {
                StaticWaveformGenerator.CMD_AMPLITUDE: self._device_commands[self.CMD_REC_AMPLITUDE],
                StaticWaveformGenerator.CMD_OFFSET: self._device_commands[self.CMD_REC_OFFSET],
                StaticWaveformGenerator.CMD_FREQUENCY: self._device_commands[self.CMD_REC_FREQUENCY],
                StaticWaveformGenerator.CMD_DUTY_CYCLE: self._device_commands[self.CMD_REC_DUTY_CYCLE],
            }
        )

        self._noise = StaticWaveformGenerator(
            self._write_cb,
            {
                StaticWaveformGenerator.CMD_AMPLITUDE: self._device_commands[self.CMD_NOISE_AMPLITUDE],
                StaticWaveformGenerator.CMD_OFFSET: self._device_commands[self.CMD_NOISE_OFFSET],
            }
        )

        self._sweep = StaticWaveformGenerator(
            self._write_cb,
            {
                StaticWaveformGenerator.CMD_AMPLITUDE: self._device_commands[self.CMD_SWEEP_AMPLITUDE],
                StaticWaveformGenerator.CMD_OFFSET: self._device_commands[self.CMD_SWEEP_OFFSET],
                StaticWaveformGenerator.CMD_FREQUENCY: self._device_commands[self.CMD_SWEEP_TIME],
            }
        )

    async def set_waveform_type(self, waveform_type: DDriveWaveformType) -> None:
        """Activate specific waveform type.
        
        Switches the active waveform generator to the specified type. The
        waveform parameters should be configured via the corresponding
        sub-generator property before activation.

        Args:
            waveform_type: Type of waveform to activate (SINE, TRIANGLE,
                RECTANGLE, NOISE, SWEEP, or NONE to disable).
        
        Example:
            >>> from psj_lib import DDriveWaveformType
            >>> # Configure then activate sine wave
            >>> await wfg.sine.set(amplitude=20.0, offset=50.0, frequency=10.0)
            >>> await wfg.set_waveform_type(DDriveWaveformType.SINE)
            >>> # Disable waveform
            >>> await wfg.set_waveform_type(DDriveWaveformType.NONE)
        
        Note:
            Setting to NONE disables waveform generation.
        """
        await self._write(self.CMD_WFG_TYPE, [waveform_type.value])

    async def get_waveform_type(self) -> DDriveWaveformType:
        """Query currently active waveform type.
        
        Returns:
            DDriveWaveformType: Currently active waveform type, or NONE
                if generator is disabled.
        
        Example:
            >>> wfg_type = await wfg.get_waveform_type()
            >>> print(f"Active waveform: {wfg_type.name}")
        """
        result = await self._write(self.CMD_WFG_TYPE)
        return DDriveWaveformType(int(result[0]))

    async def start_scan(self, scan_type: DDriveScanType) -> None:
        """Start automated scan sequence.
        
        Initiates an automated scan with the specified pattern. The scan
        uses the currently configured waveform parameters and runs for
        the specified number of cycles before stopping automatically.
        
        Args:
            scan_type: Type of scan to perform (SINE_ONCE, TRIANGLE_ONCE,
                SINE_TWICE, TRIANGLE_TWICE, or OFF to stop).
        
        Example:
            >>> from psj_lib import DDriveScanType
            >>> # Configure triangle waveform first
            >>> await wfg.triangle.set(
            ...     amplitude=40.0,
            ...     offset=50.0,
            ...     frequency=2.0
            ... )
            >>> await wfg.set_waveform_type(DDriveWaveformType.TRIANGLE)
            >>> # Start single scan
            >>> await wfg.start_scan(DDriveScanType.TRIANGLE_ONCE)
            >>> # Monitor progress
            >>> while await wfg.is_scan_running():
            ...     pos = await channel.position.get()
            ...     print(f"Position: {pos:.2f}")
            ...     await asyncio.sleep(0.1)
        
        Note:
            - Scan stops automatically after completing cycles
            - Check status with is_scan_running()
            - Waveform must be configured before starting scan
        """
        await self._write(self.CMD_SCAN_TYPE, [scan_type.value])
        await self._write(self.CMD_SCAN_START, [1])

    async def is_scan_running(self) -> bool:
        """Check if automated scan is currently active.
        
        Returns:
            bool: True if scan is running, False if idle or completed.
        
        Example:
            >>> await wfg.start_scan(DDriveScanType.SINE_ONCE)
            >>> # Wait for scan to complete
            >>> while await wfg.is_scan_running():
            ...     await asyncio.sleep(0.05)
            >>> print("Scan completed")
        """
        result = await self._write(self.CMD_SCAN_START)
        return int(result[0]) != 0

    @property
    def sine(self) -> StaticWaveformGenerator:
        """Sine waveform sub-generator configuration.
        
        Returns:
            StaticWaveformGenerator: Configuration interface for sinusoidal
                waveform with amplitude, offset, and frequency parameters.
        
        Example:
            >>> await wfg.sine.set(
            ...     amplitude=15.0,  # 15 µm amplitude
            ...     offset=50.0,     # Centered at 50 µm
            ...     frequency=20.0   # 20 Hz
            ... )
        """
        return self._sine

    @property
    def triangle(self) -> StaticWaveformGenerator:
        """Triangle waveform sub-generator configuration.
        
        Returns:
            StaticWaveformGenerator: Configuration interface for triangular
                waveform with amplitude, offset, frequency, and duty cycle.
        
        Example:
            >>> await wfg.triangle.set(
            ...     amplitude=30.0,
            ...     offset=50.0,
            ...     frequency=5.0,
            ...     duty_cycle=70.0  # 70% rise time, 30% fall time
            ... )
        
        Note:
            duty_cycle controls asymmetry: 50% is symmetric, >50% is
            slower rise, <50% is faster rise.
        """
        return self._triangle

    @property
    def rectangle(self) -> StaticWaveformGenerator:
        """Rectangle waveform sub-generator configuration.
        
        Returns:
            StaticWaveformGenerator: Configuration interface for rectangular
                (square) waveform with amplitude, offset, frequency, and duty cycle.
        
        Example:
            >>> await wfg.rectangle.set(
            ...     amplitude=25.0,
            ...     offset=50.0,
            ...     frequency=10.0,
            ...     duty_cycle=30.0  # 30% high, 70% low
            ... )
        
        Note:
            duty_cycle controls high/low ratio: 50% is square wave.
        """
        return self._rectangle

    @property
    def noise(self) -> StaticWaveformGenerator:
        """Noise generator configuration.
        
        Returns:
            StaticWaveformGenerator: Configuration interface for random
                noise with amplitude and offset parameters.
        
        Example:
            >>> await wfg.noise.set(
            ...     amplitude=2.0,  # ±2 µm random variation
            ...     offset=50.0     # Centered at 50 µm
            ... )
        """
        return self._noise

    @property
    def sweep(self) -> StaticWaveformGenerator:
        """Sweep (ramp) generator configuration.
        
        Returns:
            StaticWaveformGenerator: Configuration interface for linear
                sweep with amplitude, offset, and time (instead of frequency).
        
        Example:
            >>> await wfg.sweep.set(
            ...     amplitude=80.0,  # Sweep range 80 µm
            ...     offset=10.0,     # Start at 10 µm
            ...     frequency=2.0    # Actually sweep time: 2 seconds
            ... )
        
        Note:
            For sweep, 'frequency' parameter actually represents sweep
            time in seconds (linear ramp duration).
        """
        return self._sweep