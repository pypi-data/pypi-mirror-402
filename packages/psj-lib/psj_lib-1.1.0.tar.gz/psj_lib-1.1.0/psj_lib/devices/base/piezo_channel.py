import logging
from typing import Awaitable, Callable, List, Optional

# Global module locker
logger = logging.getLogger(__name__)


class PiezoChannel:
    """Base class representing a single channel in a multi-channel piezo device.
    
    A PiezoChannel encapsulates the functionality for a single actuator channel
    in devices that support multiple independent piezo outputs. Each channel can
    typically be controlled independently with its own voltage, position, PID
    settings, and other parameters.
    
    The channel communicates with the parent device via a write callback function,
    which handles the low-level command transmission. This design allows channels
    to be device-agnostic while providing a consistent interface.

    Specific device implementations typically define PiezoCapability instances
    as attributes of the channel class to expose functionality like setpoint, 
    position, and PID control.

    Type Aliases:
        ChannelID: Integer identifier for the channel (typically 0-based)
        Command: String representing a device command name
        Param: Union type for command parameters (float | int | bool | str)
        WriteCallback: Async function signature for sending commands to the device
    
    Attributes:
        BACKUP_COMMANDS: Set of command names that should be backed up when
            saving channel configuration. Subclasses should override this to
            specify which commands preserve channel state.
    
    Example:
        >>> # Typically created by device class, not directly by users
        >>> channel = device.channels[0]  # Get first channel
        >>> backup = await channel.backup()  # Save channel settings
        >>> channel_id = channel.id  # Get channel identifier
    
    Note:
        This is a base class. Device-specific implementations should inherit
        from this and add capability-specific methods and properties.
    """
    type ChannelID = int
    type Command = str
    type Param = float | int | bool | str
    type WriteCallback = Callable[
        [Command, List[Param], ChannelID], 
        Awaitable[List[Param]]
    ]

    BACKUP_COMMANDS: set[str] = set()  # Commands to backup channel settings

    def __init__(self, channel_id: int, write_cb: WriteCallback):
        """Initialize a piezo channel.
        
        Args:
            channel_id: Numeric identifier for this channel. Typically corresponds
                to the physical channel number on the device (0-based indexing).
            write_cb: Async callback function that transmits commands to the device.
                The callback receives the command string, parameter list, and channel
                ID, and returns the device's response as a list of strings.
        
        Example:
            >>> async def device_write(cmd, params, ch_id):
            ...     return await device.write_channel(ch_id, cmd, params)
            >>> channel = PiezoChannel(channel_id=0, write_cb=device_write)
        """
        self._channel_id = channel_id
        self._write_cb = write_cb

    async def _write(self, cmd: str, params: Optional[List[Param]]) -> Awaitable[List[str]]:
        """Internal method to send a command through the channel's write callback.
        
        This is the primary communication method used by capabilities and channel
        methods to interact with the device. It delegates to the write callback
        provided during initialization.
        
        Args:
            cmd: Command name to send to the device
            params: Optional list of parameters for the command. Pass None for
                commands that have no parameters (typically read operations).
        
        Returns:
            Device response as a list of string values
        
        Raises:
            RuntimeError: If no write callback was provided during initialization
        
        Note:
            This is an internal method (indicated by _ prefix). Capabilities and
            subclasses should use this for device communication.
        """
        if not self._write_cb:
            raise RuntimeError("No write callback defined for this channel.")

        return await self._write_cb(self._channel_id, cmd, params)

    async def _capability_write(
        self,
        device_commands: dict[str, str],
        cmd: Command,
        params: list[Param]
    ) -> list[str]:
        """Write method for capabilities with command validation.
        
        This helper method is used by capability implementations to send commands
        with automatic validation against a device's supported command set. If the
        command is not found in the device_commands dictionary, it logs a warning
        and returns None instead of raising an exception.
        
        Args:
            device_commands: Dictionary mapping capability command names to actual
                device command strings. This allows capabilities to remain generic
                while device-specific implementations map to actual hardware commands.
            cmd: The capability-level command name to send
            params: List of parameters for the command
        
        Returns:
            Device response as a list of strings, or None if command not supported
        
        Example:
            >>> # In a capability implementation:
            >>> commands = {'set_voltage': 'xsvoltage', 'get_voltage': 'xgvoltage'}
            >>> result = await self._capability_write(commands, 'set_voltage', [10.0])
        
        Note:
            This is designed for use by capability classes that may be used with
            different device types having different command sets.
        """
        # Check if command can be found in cmd dictionary
        if cmd not in device_commands:
            logger.warning(f"Capability requested to send unknown command: {cmd}.")
            return
        
        return await self._write(device_commands[cmd], params)

    async def backup(self) -> dict[str, list[str]]:
        """Backup current channel configuration by reading all backup commands.
        
        This method queries all commands listed in the BACKUP_COMMANDS class attribute
        and returns their current values as a dictionary. The backup can later be
        restored using the parent device class's restore functionality.
        
        The BACKUP_COMMANDS set should be defined in device-specific channel subclasses
        and typically includes commands for:
        - Voltage/position setpoints
        - PID controller parameters
        - Filter settings
        - Control mode configurations
        
        Returns:
            Dictionary mapping command names to their response values (as string lists).
            The dictionary can be passed to the device's restore method to recreate
            this channel configuration.
        
        Example:
            >>> backup = await channel.backup()
            >>> # backup = {'voltage': ['10.5'], 'pid_p': ['5.0'], ...}
            >>> # ... later, restore the configuration ...
            >>> await device.restore_channel(channel.id, backup)
        
        Note:
            Base class has an empty BACKUP_COMMANDS set. Subclasses must override
            this attribute to specify which commands should be backed up.
        """
        backup: dict[str, list[str]] = {}

        for cmd in self.BACKUP_COMMANDS:
            result = await self._write(cmd, None)
            backup[cmd] = result

        return backup
    
    @property
    def id(self) -> int:
        """Get the numeric identifier for this channel.
        
        The channel ID typically corresponds to the physical channel number on
        the device hardware. Most devices use 0-based indexing (0, 1, 2, etc.).
        
        Returns:
            Integer channel identifier
        
        Example:
            >>> channel = device.channels[0]
            >>> print(f"Channel ID: {channel.id}")  # Channel ID: 0
        """
        return self._channel_id