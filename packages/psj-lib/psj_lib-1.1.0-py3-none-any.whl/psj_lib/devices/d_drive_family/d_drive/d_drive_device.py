"""Piezosystem Jena d-Drive modular piezo amplifier device implementation.

The d-Drive is a modular, expandable piezoelectric amplifier system designed
for high-precision nanopositioning. It features:

- 20-bit resolution with 50 kHz sampling rate (50 kSPS)
- 1 to 6 amplifier channels per system
- Digital PID controllers with several filter stages
- Integrated waveform generator (sine, triangle, rectangle, sweep, noise)
- Two-channel data recorder (500k maximum samples per channel)
- Modular architecture with hot-swappable amplifier modules
- RS-232/USB connectivity options

For detailed hardware specifications, refer to the d-Drive Instruction Manual.
(https://www.piezosystem.com/products/amplifiers/modular/50ma-300ma-ddrive-digital-systems/)
"""

from ..d_drive_family_device import DDriveFamilyDevice
from .d_drive_channel import DDriveChannel


class DDriveDevice(DDriveFamilyDevice):
    """Piezosystem Jena d-Drive modular amplifier system.
    
    Represents a complete d-Drive system with 1-6 amplifier channels.
    Each channel provides independent control of a piezoelectric actuator
    with digital PID control, waveform generation, and data recording.
    
    The d-Drive system features:
    - 20-bit resolution
    - 50 kHz sampling rate (20µs control loop period)
    - Digital PID controllers with feedforward
    - Multiple filter stages (notch, low-pass, error filter)
    - Integrated waveform generator (sine, triangle, rectangle, sweep, noise)
    - Two-channel data recorder (500k samples per channel)
    - Hardware trigger output
    - Analog monitor output
    - Modulation input
    
    Attributes:
        DEVICE_ID: Device type identifier string
        BACKUP_COMMANDS: Commands excluded from backup operations
        CACHEABLE_COMMANDS: Commands whose responses can be cached
    
    Example:
        >>> from psj_lib import DDriveDevice, TransportType
        >>> # Connect to d-Drive via serial port
        >>> device = DDriveDevice(TransportType.SERIAL, 'COM3')
        >>> await device.connect()
        >>> print(f"Found {len(device.channels)} channels")
        >>> 
        >>> # Access channel 0
        >>> channel = device.channels[0]
        >>> # Enable closed-loop control
        >>> await channel.closed_loop_controller.set(True)
        >>> # Move to position
        >>> await channel.setpoint.set(50.0)  # 50 µm
        >>> # Read actual position
        >>> pos = await channel.position.get()
        >>> print(f"Position: {pos:.3f} µm")
    
    Note:
        - System supports 1-6 channels (hardware dependent)
        - Channels are numbered 0-5
        - Not all channel numbers may be populated
        - Use device.channels dict to access available channels
    """

    DEVICE_ID = "d-Drive"
    """Device type identifier used for device discovery and type checking."""

    D_DRIVE_IDENTIFIER = "DSM"
    """Internal identifier string used to recognize different d-Drive family devices."""

    async def _discover_channels(self):
        """Discover and initialize all available amplifier channels.
        
        Queries the device for channel status and creates DDriveChannel
        instances for each detected amplifier module.
        
        Note:
            - Called automatically during device connection
            - Detects channels 0-5 (hardware dependent)
            - Only populated slots are initialized
            - Internal method, not typically called by users
        """
        response = await self.write_raw("stat")
        self._parse_channel_status(response)

        # Set channel output to scientific notation for accuracy
        for channel in self._channels.values():
            await channel._write("setf", [1])

    def _parse_channel_status(self, response: str):
        """Parse device status response to identify active channels.
        
        Args:
            response: Raw status command response from device
        
        Note:
            - Parses "stat,X" patterns where X is channel number (0-5)
            - Initializes DDriveChannel objects for detected channels
            - Clears channel dict before populating with discovered channels
        """
        lines = response.split("\n")

        # Reset all channels
        self._channels = {}

        # Go through every line in the response
        for line in lines:
            # Check if line is empty
            if len(line) == 0:
                continue

            index = line.find("stat,")

            # Check if channel was not detected
            if index < 0:
                continue

            # Extract channel number from detected channel
            index += len("stat,")
            channel_number = int(line[index])

            self.channels[channel_number] = DDriveChannel(
                channel_number, 
                self._write_channel
            )

    # Override to provide typed channels
    @property
    def channels(self) -> dict[int, DDriveChannel]:
        """Get dictionary of available d-Drive amplifier channels.
        
        Returns:
            Dictionary mapping channel number (0-5) to DDriveChannel instance,
            or None for unpopulated slots
        
        Example:
            >>> # Iterate over all available channels
            >>> for ch_num, channel in device.channels.items():
            ...     if channel is not None:
            ...         pos = await channel.position.get()
            ...         print(f"Channel {ch_num}: {pos} µm")
            >>> 
            >>> # Access specific channel
            >>> if device.channels[0] is not None:
            ...     await device.channels[0].setpoint.set(75.0)
        
        Note:
            - Channel numbers 0-5
            - None values indicate empty amplifier slots
            - Check for None before accessing channel
        """
        return self._channels