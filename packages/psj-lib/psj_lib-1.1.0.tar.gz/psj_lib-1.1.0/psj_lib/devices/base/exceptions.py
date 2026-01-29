from enum import Enum
from typing import Type


class DeviceError(Exception):
    """Base exception class for all device-related errors.
    
    This is the parent exception for all errors that occur during device
    communication and operation. Catch this exception to handle any device
    error generically, or catch specific subclasses for targeted error handling.
    
    Device errors typically result from:
    - Invalid commands or parameters sent to the device
    - Hardware conditions (overload, underload)
    - Communication protocol violations
    - Device configuration issues
    
    Example:
        >>> try:
        ...     await device.write("invalid_command")
        ... except DeviceError as e:
        ...     print(f"Device error occurred: {e}")
    """

    pass


class ErrorNotSpecified(DeviceError):
    """Generic error when the device does not provide specific error details.
    
    Raised when the device reports an error condition but does not provide
    a specific error code. This typically indicates an internal device error
    or a communication protocol issue.
    """

    pass


class UnknownCommand(DeviceError):
    """The device does not recognize the command sent.
    
    Raised when attempting to send a command that is not supported by the
    device or is not valid for the current device firmware version.
    
    Common causes:
    - Typo in command name
    - Command not supported by device model
    - Firmware version incompatibility
    """

    pass


class ParameterMissing(DeviceError):
    """Required parameter was not provided with the command.
    
    Raised when a command that requires one or more parameters is sent
    without the necessary parameter values.
    
    Example:
        A command expecting a channel number was sent without specifying
        which channel to operate on.
    """

    pass


class AdmissibleParameterRangeExceeded(DeviceError):
    """Parameter value is outside the acceptable range for the command.
    
    Raised when a parameter value exceeds the valid range defined by the
    device for that particular command. Check device documentation for
    valid parameter ranges.
    
    Example:
        Setting a voltage beyond the device's maximum output capability.
    """

    pass


class CommandParameterCountExceeded(DeviceError):
    """Too many parameters were provided for the command.
    
    Raised when more parameters are sent than the command expects.
    Each command has a defined number of parameters; sending extra
    parameters results in this error.
    """

    pass


class ParameterLockedOrReadOnly(DeviceError):
    """Attempted to modify a read-only or locked parameter.
    
    Raised when trying to write to a parameter that:
    - Is inherently read-only (e.g., hardware status, sensor values)
    - Is currently locked by device configuration or security settings
    - Cannot be changed in the current device operation mode
    
    Example:
        Attempting to change a factory calibration value that is locked.
    """

    pass


class Underload(DeviceError):
    """Device detected an underload condition.
    """

    pass


class Overload(DeviceError):
    """Device detected an overload condition.
    """

    pass


class ParameterTooLow(DeviceError):
    """Parameter value is below the minimum acceptable value.
    
    Raised when a parameter value is below the lower bound of the
    acceptable range for that parameter.
    
    This is more specific than AdmissibleParameterRangeExceeded,
    indicating specifically that the value is too low.
    """

    pass


class ParameterTooHigh(DeviceError):
    """Parameter value exceeds the maximum acceptable value.
    
    Raised when a parameter value exceeds the upper bound of the
    acceptable range for that parameter.
    
    This is more specific than AdmissibleParameterRangeExceeded,
    indicating specifically that the value is too high.
    """

    pass


class UnknownChannel(DeviceError):
    """Specified channel does not exist on the device.
    
    Raised when attempting to access or configure a channel number
    that is not present on the connected device.
    
    Example:
        Accessing channel 3 on a single-channel device.
    """

    pass


class ActuatorNotConnected(DeviceError):
    """Piezo actuator is not physically connected to the device.
    
    Raised when the device detects that the piezo actuator is not
    plugged in or properly connected. This may prevent certain
    operations that require an active actuator connection.
    """

    pass


class ErrorCode(Enum):
    """Enumeration of device error codes with exception class mapping.
    
    This enum defines all possible error codes that can be returned by
    piezoelectric devices. Each error code corresponds to a specific
    DeviceError exception subclass.
    
    Error codes are returned by the device in response to invalid commands,
    parameter violations, or hardware conditions. The ErrorCode class provides
    utilities to convert error codes to exceptions and raise appropriate errors.
    
    Attributes:
        ERROR_NOT_SPECIFIED (int): Generic unspecified error (code 1)
        UNKNOWN_COMMAND (int): Command not recognized by device (code 2)
        PARAMETER_MISSING (int): Required parameter not provided (code 3)
        ADMISSIBLE_PARAMETER_RANGE_EXCEEDED (int): Parameter outside valid range (code 4)
        COMMAND_PARAMETER_COUNT_EXCEEDED (int): Too many parameters provided (code 5)
        PARAMETER_LOCKED_OR_READ_ONLY (int): Cannot modify locked/read-only parameter (code 6)
        UNDERLOAD (int): Device detected underload condition (code 7)
        OVERLOAD (int): Device detected overload condition (code 8)
        PARAMETER_TOO_LOW (int): Parameter below minimum value (code 9)
        PARAMETER_TOO_HIGH (int): Parameter above maximum value (code 10)
        ACTUATOR_NOT_CONNECTED (int): Actuator not physically connected (code 98)
        UNKNOWN_CHANNEL (int): Specified channel does not exist (code 99)
    
    Example:
        >>> error_code = ErrorCode.from_value(2)
        >>> print(error_code)  # ErrorCode.UNKNOWN_COMMAND
        >>> ErrorCode.raise_error(error_code)  # Raises UnknownCommand exception
    """
    ERROR_NOT_SPECIFIED = 1
    UNKNOWN_COMMAND = 2
    PARAMETER_MISSING = 3
    ADMISSIBLE_PARAMETER_RANGE_EXCEEDED = 4
    COMMAND_PARAMETER_COUNT_EXCEEDED = 5
    PARAMETER_LOCKED_OR_READ_ONLY = 6
    UNDERLOAD = 7
    OVERLOAD = 8
    PARAMETER_TOO_LOW = 9
    PARAMETER_TOO_HIGH = 10
    ACTUATOR_NOT_CONNECTED = 98
    UNKNOWN_CHANNEL = 99

    @classmethod
    def from_value(cls, value: int) -> 'ErrorCode':
        """
        Converts an integer value to its corresponding ErrorCode enum member.

        Args:
            value (int): The integer value representing the error code.

        Returns:
            ErrorCode: The corresponding ErrorCode enum member.

        Raises:
            ValueError: If the value does not correspond to any ErrorCode member.
        """
        for member in cls:
            if member.value == value:
                return member

        raise ValueError(f"No ErrorCode member with value {value}")

    @classmethod
    def get_exception_class(cls, error_code) -> Type[DeviceError]:
        """
        Returns the appropriate exception class for a given error code.

        Args:
            error_code (ErrorCode or int): The error code for which to get the exception class.

        Returns:
            Type[DeviceError]: The exception class corresponding to the error code.
        """
        # Convert int to ErrorCode if needed
        if isinstance(error_code, int):
            error_code = cls.from_value(error_code)

        exception_map = {
            cls.ERROR_NOT_SPECIFIED: ErrorNotSpecified,
            cls.UNKNOWN_COMMAND: UnknownCommand,
            cls.PARAMETER_MISSING: ParameterMissing,
            cls.ADMISSIBLE_PARAMETER_RANGE_EXCEEDED: AdmissibleParameterRangeExceeded,
            cls.COMMAND_PARAMETER_COUNT_EXCEEDED: CommandParameterCountExceeded,
            cls.PARAMETER_LOCKED_OR_READ_ONLY: ParameterLockedOrReadOnly,
            cls.UNDERLOAD: Underload,
            cls.OVERLOAD: Overload,
            cls.PARAMETER_TOO_LOW: ParameterTooLow,
            cls.PARAMETER_TOO_HIGH: ParameterTooHigh,
            cls.ACTUATOR_NOT_CONNECTED: ActuatorNotConnected,
            cls.UNKNOWN_CHANNEL: UnknownChannel,
        }

        return exception_map.get(error_code, ErrorNotSpecified)

    @classmethod
    def raise_error(cls, error_code, message=None):
        """
        Raises the appropriate exception for a given error code.

        Args:
            error_code (ErrorCode or int): The error code to raise.
            message (str, optional): Custom error message. If not provided, uses default description.

        Raises:
            DeviceError: The specific exception corresponding to the error code.
        """
        
        descriptions = {
            ErrorCode.ERROR_NOT_SPECIFIED: "Error not specified",
            ErrorCode.UNKNOWN_COMMAND: "Unknown command",
            ErrorCode.PARAMETER_MISSING: "Parameter missing",
            ErrorCode.ADMISSIBLE_PARAMETER_RANGE_EXCEEDED: "Admissible parameter range exceeded",
            ErrorCode.COMMAND_PARAMETER_COUNT_EXCEEDED: "Command's parameter count exceeded",
            ErrorCode.PARAMETER_LOCKED_OR_READ_ONLY: "Parameter is locked or read only",
            ErrorCode.UNDERLOAD: "Underload",
            ErrorCode.OVERLOAD: "Overload",
            ErrorCode.PARAMETER_TOO_LOW: "Parameter too low",
            ErrorCode.PARAMETER_TOO_HIGH: "Parameter too high",
            ErrorCode.ACTUATOR_NOT_CONNECTED: "Actuator not connected",
            ErrorCode.UNKNOWN_CHANNEL: "Channel does not exist"
        }

        # Convert int to ErrorCode if needed
        if isinstance(error_code, int):
            error_code = cls.from_value(error_code)

        actual_message = message or descriptions.get(error_code, "Unknown error")

        exception_class = cls.get_exception_class(error_code)
        raise exception_class(actual_message)