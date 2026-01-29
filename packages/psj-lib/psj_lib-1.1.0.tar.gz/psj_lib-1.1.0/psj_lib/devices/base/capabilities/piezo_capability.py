"""Base capability class and type definitions for piezoelectric device features.

This module provides the abstract base class for all device capabilities and
defines common type aliases used throughout the capability system.
"""

from typing import Callable

type Command = str
"""Command identifier string for device operations."""

type DeviceCommands = dict[Command, str]
"""Mapping of command identifiers to device-specific command strings."""

type Param = float | int | bool | str
"""Parameter value types supported by device commands."""

type WriteCallback = Callable[[DeviceCommands, Command, list[Param] | None], list[str]]
"""Callback function for writing commands to device.

Args:
    DeviceCommands: Command mapping dictionary
    Command: Command identifier string
    list[Param] | None: Optional list of command parameters

Returns:
    list[str]: Response lines from device
"""

type ProgressCallback = Callable[[int, int], None]
"""Callback function for reporting progress of long-running operations.

Args:
    int: Current progress value (items completed)
    int: Total items to process
"""


class PiezoCapability:
    """Abstract base class for all piezoelectric device capabilities.
    
    Provides a common interface for device features by wrapping command
    execution with a write callback. All specific capabilities (position,
    setpoint, PID control, etc.) inherit from this class.
    
    This class handles the communication abstraction, allowing capability
    implementations to focus on their specific functionality without
    dealing with low-level command details.
    
    Attributes:
        _write_cb: Callback function for writing commands to device
        _device_commands: Device-specific command mapping
    
    Example:
        >>> # Used as base class for specific capabilities
        >>> class CustomCapability(PiezoCapability):
        ...     async def get_value(self) -> float:
        ...         result = await self._write("CUSTOM_CMD")
        ...         return float(result[0])
    
    Note:
        - Not intended for direct instantiation
        - Subclasses implement specific device functionality
        - _write method provides abstraction for command execution
    """
    
    def __init__(
        self, 
        write_cb: WriteCallback,
        device_commands: DeviceCommands,
    ):
        """Initialize the capability with command execution callback.
        
        Args:
            write_cb: Function to execute device commands
            device_commands: Mapping of command IDs to device strings
        """
        self._write_cb = write_cb
        self._device_commands = device_commands

    async def _write(self, command: str, params: list[Param] | None = None) -> list[str]:
        """Execute a device command with optional parameters.
        
        Args:
            command: Command identifier to execute
            params: Optional list of parameters for the command
        
        Returns:
            List of response strings from the device
        
        Note:
            - Used by subclasses to implement specific operations
            - Delegates actual execution to write_cb
        """
        return await self._write_cb(self._device_commands, command, params)