from enum import Enum

from ...base.capabilities import StatusRegister
from ...base.piezo_types import SensorType


class DDriveWaveformGeneratorStatus(Enum):
    """d-Drive waveform generator status from hardware status register.
    
    Indicates which waveform type is currently active in the waveform
    generator. This is read from bits 9-11 of the d-Drive status register.
    
    Attributes:
        INACTIVE: No waveform generation active
        SINE: Sinusoidal waveform active
        TRIANGLE: Triangle waveform active
        RECTANGLE: Rectangle/square waveform active
        NOISE: Noise waveform active
        SWEEP: Sweep/ramp waveform active
        UNKNOWN: Status value not recognized (error condition)
    
    Example:
        >>> status = await channel.status_register.get()
        >>> if status.waveform_generator_status == DDriveWaveformGeneratorStatus.SINE:
        ...     print("Sine wave is running")
    """
    INACTIVE = 0
    SINE = 1
    TRIANGLE = 2
    RECTANGLE = 3
    NOISE = 4
    SWEEP = 5
    UNKNOWN = 99


class DDriveStatusRegister(StatusRegister):
    """d-Drive hardware status register with bit-mapped state information.
    
    Decodes the d-Drive status register word into individual boolean and
    enumerated properties representing the amplifier channel's current state.
    
    The status register provides real-time information about:
    - Actuator connection status
    - Position sensor type
    - Output voltage enable state
    - Closed-loop control activation
    - Active waveform type
    - Filter enable states
    
    Properties:
        actor_plugged (bool): Actuator physically connected
        sensor_type (SensorType): Position sensor type (STRAIN_GAUGE, CAPACITIVE, etc.)
        piezo_voltage_enabled (bool): High voltage output enabled
        closed_loop (bool): Closed-loop control active
        waveform_generator_status (DDriveWaveformGeneratorStatus): Active waveform type
        notch_filter_active (bool): Notch filter enabled
        low_pass_filter_active (bool): Low-pass filter enabled
    
    Example:
        >>> status = await channel.status_register.get()
        >>> print(f"Actuator plugged: {status.actor_plugged}")
        >>> print(f"Sensor type: {status.sensor_type.name}")
        >>> print(f"Closed-loop: {status.closed_loop}")
        >>> print(f"Waveform: {status.waveform_generator_status.name}")
        >>> print(f"Notch filter: {status.notch_filter_active}")
    
    Note:
        - Status is read-only (reports hardware state)
        - Decoded from 16-bit status register word
        - Bit positions defined by d-Drive firmware
    """

    @property
    def actor_plugged(self) -> bool:
        """Actuator connection status (bit 0).
        
        Returns:
            bool: True if piezo actuator is physically connected and detected.
        
        Note:
            The d-Drive automatically detects actuator connection on power-up
            or when an actuator is plugged in.
        """
        val = int(self._raw[0])
        return bool(val & 0x0001)

    @property
    def sensor_type(self) -> SensorType:
        """Position sensor type identification (bits 1-2).
        
        Returns:
            SensorType: Type of position sensor in connected actuator.
                Common types: STRAIN_GAUGE, CAPACITIVE, LVDT, etc.
        
        Note:
            Sensor type is auto-detected from actuator's identification.
            Different sensor types may have different characteristics
            (resolution, linearity, temperature sensitivity).
        """
        val = int(self._raw[0])
        return SensorType((val & 0x0006) >> 1)

    @property
    def piezo_voltage_enabled(self) -> bool:
        """High voltage output enable status (bit 6).
        
        Returns:
            bool: True if amplifier output stage is enabled and driving
                the piezo actuator.
        
        Note:
            When False, the output is disabled for safety. This may occur:
            - After power-up when no actuator is detected
            - On error conditions
            - When explicitly disabled by user
        """
        val = int(self._raw[0])
        return bool(val & 0x0040)

    @property
    def closed_loop(self) -> bool:
        """Closed-loop control activation status (bit 7).
        
        Returns:
            bool: True if sensor-based feedback control is active.
        
        Note:
            - When True: PID controller drives actuator to match setpoint
            - When False: Open-loop operation (direct voltage control)
            - Requires valid sensor signal to enable
        """
        val = int(self._raw[0])
        return bool(val & 0x0080)

    @property
    def waveform_generator_status(self) -> DDriveWaveformGeneratorStatus:
        """Active waveform generator type (bits 9-11).
        
        Returns:
            DDriveWaveformGeneratorStatus: Currently active waveform type.
                INACTIVE if no waveform is running, otherwise SINE, TRIANGLE,
                RECTANGLE, NOISE, or SWEEP.
        
        Example:
            >>> status = await channel.status_register.get()
            >>> wfg = status.waveform_generator_status
            >>> if wfg != DDriveWaveformGeneratorStatus.INACTIVE:
            ...     print(f"Active waveform: {wfg.name}")
        
        Note:
            Returns UNKNOWN if hardware reports unrecognized value.
        """
        val = int(self._raw[0])
        wg_status = (val & 0x0E00) >> 9

        try:
            return DDriveWaveformGeneratorStatus(wg_status)
        except ValueError:
            return DDriveWaveformGeneratorStatus.UNKNOWN

    @property
    def notch_filter_active(self) -> bool:
        """Notch filter enable status (bit 12).
        
        Returns:
            bool: True if notch filter is enabled and actively filtering.
        
        Note:
            Notch filter suppresses specific frequencies (typically
            mechanical resonances) to improve closed-loop stability.
        """
        val = int(self._raw[0])
        return bool(val & 0x1000)

    @property
    def low_pass_filter_active(self) -> bool:
        """Low-pass filter enable status (bit 13).
        
        Returns:
            bool: True if low-pass filter is enabled and actively filtering.
        
        Note:
            Low-pass filter reduces high-frequency noise in position or
            control signals for smoother operation.
        """
        val = int(self._raw[0])
        return bool(val & 0x2000)