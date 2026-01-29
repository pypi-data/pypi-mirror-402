from ...base.capabilities import DataRecorderChannel, DataRecorder


class DDriveDataRecorderChannel(DataRecorderChannel):
    """d-Drive data recorder channel aliases with semantic names.
    
    Provides meaningful names for the two hardware data recorder channels
    in d-Drive amplifiers. The d-Drive always records position on channel 1
    and actuator voltage on channel 2.
    
    Attributes:
        POSITION: Position sensor signal (alias for CHANNEL_1).
            Records actual measured position from the sensor.
        VOLTAGE: Actuator voltage signal (alias for CHANNEL_2).
            Records the output voltage applied to the piezo actuator.
    
    Example:
        >>> from psj_lib import DDriveDataRecorderChannel
        >>> # Configure recorder
        >>> await channel.data_recorder.set(
        ...     memory_length=50000,  # 1 second at 50 kHz
        ...     stride=1
        ... )
        >>> await channel.data_recorder.start()
        >>> # ... perform motion ...
        >>> # Retrieve position data using semantic name
        >>> pos_data = await channel.data_recorder.get_all_data(
        ...     DDriveDataRecorderChannel.POSITION
        ... )
        >>> # Retrieve voltage data
        >>> vol_data = await channel.data_recorder.get_all_data(
        ...     DDriveDataRecorderChannel.VOLTAGE
        ... )
        >>> print(f\"Recorded {len(pos_data)} position samples\")\n        >>> print(f\"Recorded {len(vol_data)} voltage samples\")
    
    Note:
        - Both channels always record simultaneously
        - Sample rate: 50 kHz (20 µs period) maximum
        - Maximum 500,000 samples per channel
        - POSITION and VOLTAGE are semantic aliases for hardware channels
    """
    POSITION = DataRecorder.CHANNEL_1_IDX
    VOLTAGE = DataRecorder.CHANNEL_2_IDX


class DDriveDataRecorder(DataRecorder):
    """d-Drive specific data recorder implementation.
    
    The d-Drive data recorder captures two channels simultaneously:
    - Channel 1 (POSITION): Position sensor signal in device units (µm, mrad, etc.)
    - Channel 2 (VOLTAGE): Actuator voltage in volts
    
    Recording specifications:
    - Maximum 500,000 samples per channel
    - 50 kHz sample rate (20 µs period) maximum
    - Stride (decimation) from 1 to 65535
    - Both channels always record the same length
    
    The d-Drive returns data in a device-specific format that requires
    special parsing, which this class handles automatically.
    
    Example:
        >>> recorder = channel.data_recorder
        >>> # Configure for 1 second at full rate
        >>> await recorder.set(memory_length=50000, stride=1)
        >>> await recorder.start()
        >>> # ... perform motion ...
        >>> # Get position data
        >>> pos_data = await recorder.get_all_data(
        ...     DDriveDataRecorderChannel.POSITION
        ... )
        >>> # Get voltage data
        >>> vol_data = await recorder.get_all_data(
        ...     DDriveDataRecorderChannel.VOLTAGE
        ... )
    
    Note:
        - get_memory_length() and get_stride() not supported by d-Drive
        - Use the values you configured with set() to track settings
        - Data format is automatically parsed from d-Drive response
    """
    
    async def get_memory_length(self) -> int:
        """Get configured recording length.
        
        Returns:
            Always returns 500000 (hardware maximum) as d-Drive does not support
            reading back this configuration value.
        
        Note:
            The d-Drive hardware does not provide a read command for
            memory length. This returns the maximum hardware capacity.
            Use recorder.sample_rate to calculate recording duration.
        """
        return 500000
    
    async def get_stride(self) -> int:
        """Get decimation stride factor.
        
        Returns:
            Always returns 0 as d-Drive does not support reading back
            this configuration value. Track the value you set manually.
        
        Note:
            The d-Drive hardware does not provide a read command for
            stride. Use the value you configured with set().
        """
        return 0
    
    async def get_data(
        self,
        channel: DataRecorderChannel,
        index: int | None = None
    ) -> float:
        """Read a single data sample from specified channel.
        
        The d-Drive returns data in format "m,value" (position) or
        "u,value" (voltage) which is automatically parsed.
        
        Args:
            channel: Which channel to read (POSITION or VOLTAGE)
            index: Sample index (0 to memory_length-1), or None for
                  next sequential sample
        
        Returns:
            Single data sample value as float
        
        Example:
            >>> # Read position at index 100
            >>> pos = await recorder.get_data(
            ...     DDriveDataRecorderChannel.POSITION,
            ...     index=100
            ... )
            >>> # Read next voltage sample
            >>> voltage = await recorder.get_data(
            ...     DDriveDataRecorderChannel.VOLTAGE
            ... )
        
        Note:
            The d-Drive returns "m,value" or "u,value" format.
            This method automatically extracts the numeric value.
        """
        # Check if index pointer needs to be set
        if index is not None:
            await self._write(self.CMD_PTR, [index])

        channel_idx = channel.value

        # Select appropriate command for channel
        cmd = self.CMD_GET_DATA_1 if channel_idx == self.CHANNEL_1_IDX else self.CMD_GET_DATA_2
        
        # d-Drive specific parameters:
        # - 0: Return full command with prefix ("m,xxx" or "u,xxx")
        # - 1: Return single value
        result = await self._write(cmd, [0, 1])
        
        # Result is ["value"] - parse to appropriate type
        if channel_idx == DDriveDataRecorderChannel.POSITION.value:
            return self._parse_pos_value(result[0])


        return self._parse_voltage_value(result[0])

    def _parse_pos_value(self, raw_str: str) -> float:
        """Parse hexadecimal position value from d-Drive.
        
        The d-Drive returns position as hexadecimal values (0x0000-0xFFFF)
        representing percentage of full range with ±30% overshoot capability.
        
        Args:
            raw_str: Hexadecimal string from device (e.g., "8000")
        
        Returns:
            Position as percentage of full range (-30% to +130%)
            - 0x0000 → -30% (max negative overshoot)
            - 0x8000 → 50% (center position)
            - 0xFFFF → 130% (max positive overshoot)
        
        Formula:
            position = (160 / 65535) * hex_value - 30
        
        Example:
            >>> pos = self._parse_pos_value("8000")  # 0x8000 = 32768
            >>> print(f"{pos:.1f}%")  # 50.0%
        """
        # Parse value as hex integer
        value = int(raw_str, 16)

        # Convert to percentage of full closed loop motion range (with overshoot of +30%/-30%)
        pos = (160 / 65535) * value - 30

        return pos
    
    def _parse_voltage_value(self, raw_str: str) -> float:
        """Parse hexadecimal voltage value from d-Drive.
        
        The d-Drive returns voltage as hexadecimal values (0x0000-0xFFFF)
        representing the actuator output voltage.
        
        Args:
            raw_str: Hexadecimal string from device (e.g., "8000")
        
        Returns:
            Voltage in volts (-27.5V to +137.5V, 165V total span)
            - 0x0000 → -27.5V (minimum)
            - 0x8000 → 55V (mid-range)
            - 0xFFFF → 137.5V (maximum)
        
        Formula:
            voltage = (165 / 65535) * hex_value - 27.5
        
        Example:
            >>> voltage = self._parse_voltage_value("8000")  # 0x8000 = 32768
            >>> print(f"{voltage:.1f}V")  # 55.0V
        
        Note:
            This includes a debug print statement for development.
        """
        # Parse value as hex integer
        value = int(raw_str, 16)

        # Convert to voltage in volts (Range: -27.5V to +137.5V)
        voltage = (165 / 65535) * value - 27.5

        return voltage