"""Data recorder capability for capturing device signals."""

from enum import Enum

from .piezo_capability import PiezoCapability, ProgressCallback


class DataRecorderChannel(Enum):
    """Data recorder input channels.
    
    Identifies which recorder channel to access for configuration
    or data retrieval.

    Subclasses may define specific channel meanings.
    """
    pass

class DataRecorder(PiezoCapability):
    """Record device signals to internal memory for later retrieval.
    
    The data recorder captures signals (position, setpoint, voltage, etc.)
    at high speed into device memory. Data can be retrieved after
    recording completes for analysis and plotting.
    
    Features:
    - Multiple channels (device dependent, typically 2)
    - Configurable memory length
    - Stride (decimation) for longer time spans
    
    Typical workflow:
    1. Configure memory length and stride
    2. Start recording with start() or by using device specific autostart modes 
       (setpoint, waveform generator)
    3. Wait for recording to complete
    4. Retrieve data with get_all_data() or get_data()
    
    Example:
        >>> recorder = device.data_recorder
        >>> # Configure for 10000 samples, no decimation
        >>> await recorder.set(memory_length=10000, stride=1)
        >>> # Start recording
        >>> await recorder.start()
        >>> # ... perform motion ...
        >>> # Retrieve channel 1 data with progress callback
        >>> def progress(current, total):
        ...     print(f"Downloaded {current}/{total} samples")
        >>> data = await recorder.get_all_data(
        ...     DataRecorderChannel.CHANNEL_1,
        ...     callback=progress
        ... )
        >>> print(f"Captured {len(data)} samples")
    
    Note:
        - Memory length limits total capture time
        - Stride reduces data rate (stride=10 keeps only every 10th sample)
        - Channels record different signals (device-specific)
        - Data units depend on recorded signal type
        - Large data transfers may take several seconds
    """
    
    CMD_MEMORY_LENGTH = "DATA_RECORDER_MEMORY_LENGTH"
    CMD_STRIDE = "DATA_RECORDER_RECORD_STRIDE"
    CMD_START_RECORDING = "DATA_RECORDER_START_RECORDING"
    CMD_PTR = "DATA_RECORDER_POINTER"
    CMD_GET_DATA_1 = "DATA_RECORDER_GET_DATA_1"
    CMD_GET_DATA_2 = "DATA_RECORDER_GET_DATA_2"

    CHANNEL_1_IDX = 1
    CHANNEL_2_IDX = 2

    def __init__(
        self, 
        write_cb, 
        device_commands,
        sample_period: int
    ) -> None:
        super().__init__(write_cb, device_commands)
        self._sample_period = sample_period  # in microseconds

    async def set(
        self,
        memory_length: int | None = None,
        stride: int | None = None,
    ) -> None:
        """Configure data recorder parameters.
        
        Args:
            memory_length: Number of samples to record per channel
            stride: Decimation factor (1=all samples, 10=every 10th sample)
        
        Example:
            >>> # Record 5000 samples at full rate
            >>> await recorder.set(memory_length=5000, stride=1)
            >>> # Record 50000 samples, keeping every 100th
            >>> await recorder.set(memory_length=50000, stride=100)
        
        Note:
            - Maximum memory_length is device-specific
            - Stride>1 allows longer time spans at lower data rate
            - Effective sample period = sample_period * stride
        """
        if memory_length is not None:
            await self._write(self.CMD_MEMORY_LENGTH, [memory_length])

        if stride is not None:
            await self._write(self.CMD_STRIDE, [stride])

    async def get_memory_length(self) -> int:
        """Get configured recording length.
        
        Returns:
            Number of samples per channel
        
        Example:
            >>> length = await recorder.get_memory_length()
            >>> print(f"Will record {length} samples")
        """
        result = await self._write(self.CMD_MEMORY_LENGTH)
        return int(result[0])

    async def get_stride(self) -> int:
        """Get decimation stride factor.
        
        Returns:
            Current stride value (1=no decimation)
        
        Example:
            >>> stride = await recorder.get_stride()
            >>> print(f"Recording every {stride} sample(s)")
        """
        result = await self._write(self.CMD_STRIDE)
        return int(result[0])

    async def start(self) -> None:
        """Start data recording.
        
        Begins capturing data to device memory. Recording continues
        until memory is full or device is reset.

        Some devices may support automatic recording start based on
        setpoint changes or waveform generator activity.
        
        Example:
            >>> await recorder.start()
            >>> # Recording now active
            >>> await asyncio.sleep(1.0)  # Record for 1 second
            >>> # Retrieve data...
        
        Note:
            - Previous recording data is overwritten
            - Recording may stop automatically when buffer full
            - Check device status to determine if still recording
        """
        await self._write(self.CMD_START_RECORDING, None)

    async def get_data(
        self,
        channel: DataRecorderChannel,
        index: int | None = None
    ) -> float:
        """Read a single data sample from specified channel.
        
        Args:
            channel: Which channel to read from
            index: Sample index (0 to memory_length-1), or None to read
                  next sequential sample
        
        Returns:
            Single data sample value
        
        Example:
            >>> # Read sample at index 100
            >>> value = await recorder.get_data(
            ...     DataRecorderChannel.CHANNEL_1,
            ...     index=100
            ... )
            >>> # Read next sequential sample
            >>> value2 = await recorder.get_data(
            ...     DataRecorderChannel.CHANNEL_1
            ... )
        
        Note:
            - Setting index resets read pointer
            - Omitting index reads sequentially
            - More efficient to use get_all_data() for bulk retrieval
        """
        # Check if index pointer needs to be set
        if index is not None:
            await self._write(self.CMD_PTR, [index])

        channel_idx = channel.value

        cmd = self.CMD_GET_DATA_1 if channel_idx == self.CHANNEL_1_IDX else self.CMD_GET_DATA_2
        return await self._write(cmd)[0]

    async def get_all_data(
        self,
        channel: DataRecorderChannel,
        max_length: int | None = None,
        callback: ProgressCallback | None = None,
    ) -> list[float]:
        """Retrieve all recorded data from specified channel.
        
        Downloads entire recording buffer from device memory. This may
        take several seconds for large datasets.
        
        Args:
            channel: Which channel to retrieve
            max_length: Maximum number of samples to retrieve. If None,
                        retrieves full configured length.
            callback: Optional progress callback function(current, total)
        
        Returns:
            List of all recorded samples
        
        Example:
            >>> # Simple retrieval
            >>> data = await recorder.get_all_data(
            ...     DataRecorderChannel.CHANNEL_1
            ... )
            >>> 
            >>> # With progress updates
            >>> def show_progress(current, total):
            ...     percent = 100 * current / total
            ...     print(f"\rDownload: {percent:.0f}%", end="")
            >>> 
            >>> data = await recorder.get_all_data(
            ...     DataRecorderChannel.CHANNEL_2,
            ...     callback=show_progress
            ... )
            >>> print(f"\nRetrieved {len(data)} samples")
        
        Note:
            - Transfer time depends on memory_length
            - Progress callback useful for long transfers
            - Returns data in chronological order
            - Units depend on recorded signal type
        """
        # Get total length of recorded data
        length = max_length if max_length is not None else await self.get_memory_length()
        data = []

        # Retrieve all data points for the specified channel
        for i in range(length):
            data.append(await self.get_data(channel, 0 if i == 0 else None))

            # Call progress callback if provided
            if callback is not None:
                callback(i + 1, length)

        return data

    @property
    def sample_period(self) -> int:
        """Get base sample period in microseconds.
        
        Returns:
            Sample period in microseconds
        
        Example:
            >>> period = recorder.sample_period
            >>> print(f"Base sample period: {period} µs")
        """
        return self._sample_period
    
    @property
    def sample_rate(self) -> float:
        """Get base sample rate in Hz.
        
        Returns:
            Sample rate in Hz
        """
        return 1000000 / self._sample_period