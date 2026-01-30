"""Custom exceptions for the nibcq module."""


class BCQError(Exception):
    """Base class for all custom exceptions in the nibcq module.

    Args:
        code (int): The error code.
        message (str): Human-readable error message.

    Note:
        Prefer using a specific BCQ error subclass if available.
        Use this base class only for general or uncategorized BCQ errors.

    Example:
        >>> raise BCQError(5004, "SMU Channels were not provided in ascending order.")
    """

    def __init__(self, code: int, message: str):
        """Initialize the Base Error class with a code and message."""
        self.code = code
        self.message = message
        super().__init__(f"[Error {self.code}]: {self.message}")


class EmptySerialNumberError(BCQError):
    """Exception raised when a device is initialized with an empty serial number.

    This typically occurs when the device is simulated (not real hardware).

    Args:
        message (str, optional): Custom error message. Defaults to a standard message.

    Example:
        >>> raise EmptySerialNumberError("Device serial number cannot be empty.")
    """

    def __init__(self, message: str = "Device serial number cannot be empty."):
        """Initialize the Empty Serial Number Error with a default message."""
        super().__init__(code=5000, message=message)


class HardwareIncompatibilityError(BCQError):
    """Exception raised when there is a hardware incompatibility issue.

    Args:
        message (str, optional): Custom error message. Defaults to a standard message.

    Examples:
        The following are examples of how this error can be raised:

        - **General incompatibility** *(unknown or unsupported model)*

            >>> raise HardwareIncompatibilityError(
            >>>     f"{device.product} is not supported by the Cell Quality Toolkit."
            >>> )

        - **Specific: DCIR measurement** *(Eload required)*

            >>> raise HardwareIncompatibilityError(
            >>>     f"{device.product} is not supported for DCIR measurement.
            >>>     Supported models: {Device.SUPPORTED_ELOAD_LIST}"
            >>> )

        - **Specific: EIS/ACIR measurement** *(SMU required)*

            >>> raise HardwareIncompatibilityError(
            >>>     f"{device.product} is not supported for EIS/ACIR measurement.
            >>>     Supported models: {Device.SUPPORTED_SMU_LIST}"
            >>> )

        - **Specific: OCV measurement** *(DMM required)*

            >>> raise HardwareIncompatibilityError(
            >>>     f"{device.product} is not supported for OCV measurement.
            >>>     Supported models: {Device.SUPPORTED_DMM_LIST}"
            >>> )
    """

    def __init__(
        self,
        message: str = "The current given model is incompatible with the Cell Quality Toolkit.",
    ):
        """Initialize the Hardware Incompatibility Error with a default message."""
        super().__init__(code=5001, message=message)


class CompensationMethodError(BCQError):
    """Exception raised when an invalid compensation method is specified.

    This error occurs if:
      - No compensation or a combination of compensation methods was selected.
      - When obtaining compensation values and writing them to compensation files,
        only one compensation method can be used at a time.
      - A specific compensation value is missing for a required frequency.

    Args:
        message (str, optional): Custom error message. Defaults to a standard message.

    Examples:
        The following are examples of how this error can be raised:

        - **General: Method selection issue**

            >>> raise CompensationMethodError(
            >>>     "No compensation or a combination of compensation methods was selected.
            >>>     Only one compensation method can be used at a time."
            >>> )

        - **Specific: Missing value**

            >>> raise CompensationMethodError(
            >>>     f"Short Compensation value not found for {frequency} Hz!"
            >>> )
    """

    def __init__(self, message: str = "The specified compensation method is not supported."):
        """Initialize the Compensation Method Error with a default message."""
        super().__init__(code=5002, message=message)


class FrequencyError(BCQError):
    """Exception raised when there are issues related to test frequency.

    This error can occur in the following cases:
      - The frequency is negative or exceeds the supported maximum.
      - Too many periods have been selected for the given frequency.
      - The frequency is not supported by the API.

    Args:
        message (str, optional): Custom error message. Defaults to a standard message.

    Examples:
        The following are examples of how this error can be raised:

        - **General: Frequency issue**

            >>> raise FrequencyError("There is an issue with the specified test frequency.")

        - **Specific: Too many periods for a frequency**

            >>> raise FrequencyError(
            >>>     f"Too many periods have been selected for frequency {test_frequency} Hz.
            >>>     Lower the number of periods."
            >>> )

        - **Specific: Frequency exceeds supported maximum**

            >>> raise FrequencyError(
            >>>     f"API only supports non-negative frequencies
            >>>     up to {max_supported_frequency} Hz!"
            >>> )
    """

    def __init__(self, message: str = "There is an issue with the specified test frequency."):
        """Initialize the Frequency Issues Error with a default message."""
        super().__init__(code=5003, message=message)


class ChannelOrderError(BCQError):
    """Exception raised when SMU channels are not provided in ascending order.

    Args:
        message (str, optional): Custom error message. Defaults to a standard message.

    Example:
        >>> raise ChannelOrderError("SMU Channels were not provided in ascending order.")
    """

    def __init__(self, message: str = "SMU Channels were not provided in ascending order."):
        """Initialize the Channel Order Error with a default message."""
        super().__init__(code=5004, message=message)


class SMUParameterError(BCQError):
    """Exception raised when some parameter related to the SMU is incorrect.

    These, for example, can show that voltage or current limits are incorrect or exceeded
    or that some pre-required steps are not done yet on the SMU's workflow.

    Args:
        message (str, optional): Custom error message. Defaults to a standard message.

    Examples:
        The following are examples of how this error can be raised:

        - **General: Incorrect Parameter**

            >>> raise SMUParameterError("SMU Parameters are set incorrectly.")

        - **Specific: Measurement not finished before wanting to access it**

            >>> raise SMUParameterError("SMU Measurement is not available.")

        - **Specific: Voltage limit exceeded**

            >>> raise SMUParameterError(
            >>>     f"Voltage limit {voltage_limit_hi} V exceeds
            >>>     the allowed maximum of {max_voltage} V."
            >>> )
    """

    def __init__(self, message: str = "SMU Parameters are set incorrectly."):
        """Initialize the SMU Parameter Error with a default message."""
        super().__init__(code=5005, message=message)


class TestSessionMismatchError(BCQError):
    """Exception raised when there is a mismatch between test type and session configuration.

    This error occurs when the selected test type is incompatible with the current session settings.

    Args:
        message (str, optional): Custom error message. Defaults to a standard message.

    Example:
        >>> raise TestSessionMismatchError(
        >>>     "The selected test type is incompatible with the current session configuration."
        >>> )
    """

    def __init__(
        self,
        message: str = "The selected test type is incompatible with the current session configuration.",
    ):
        """Initialize the Test Type and Session Mismatch Error with a default message."""
        super().__init__(code=5006, message=message)


class SwitchConfigurationError(BCQError):
    """Exception raised when there is an issue with the switch configuration.

    This error occurs when the switch settings are invalid
    or incompatible with the test requirements.

    Args:
        message (str, optional): Custom error message. Defaults to a standard message.

    Examples:
        The following are examples of how this error can be raised:

        - **General configuration issue**

            >>> raise SwitchConfigurationError(
            >>>     "The switch configuration is invalid or
            >>>     incompatible with the test requirements."
            >>> )

        - **Invalid DUT channel names**

            >>> raise SwitchConfigurationError(
            >>>     f"The following DUT channel names are invalid: {invalid_dut_channels}.
            >>>     Allowed: ch0-ch63."
            >>> )

        - **Invalid sense/source channel names**

            >>> raise SwitchConfigurationError(
            >>>     f"The following sense/source channel names
            >>>     are invalid: {invalid_sense_channels}."
            >>> )

        - **Invalid channel pairs**

            >>> raise SwitchConfigurationError(
            >>>     f"The following channel pairs are invalid: {invalid_channel_pairs}."
            >>> )
    """

    def __init__(
        self,
        message: str = "The switch configuration is invalid or incompatible with the test requirements.",
    ):
        """Initialize the Switch Configuration Error with a default message."""
        super().__init__(code=5007, message=message)


class EloadParameterError(BCQError):
    """Exception raised when there is an issue with Eload parameters.

    This error occurs when the Eload parameters are invalid
    or incompatible with the test requirements.

    Args:
        message (str, optional): Custom error message. Defaults to a standard message.

    Example:
        The following are examples of how this error can be raised:

        - **General parameter issue**

        >>> raise EloadParameterError(
        >>>     "Current limit or measurement record length not configured successfully."
        >>> )

        - **Current limit exceeded**

        >>> raise EloadParameterError(
        >>>     f"Current limit {current_limit} A exceeds the allowed maximum of {max_current} A."
        >>> )

        - **Invalid measurement record length**

        >>> raise EloadParameterError(
        >>>     f"Measurement record length {record_length} is invalid for the selected mode."
        >>> )
    """

    def __init__(
        self,
        message: str = "Current limit or measurement record length not configured successfully.",
    ):
        """Initialize the Eload Parameter Error with a default message."""
        super().__init__(code=5008, message=message)


class CurrentAmplitudeError(BCQError):
    """Exception raised when the current amplitude is invalid or exceeds limits.

    This error occurs when the specified current amplitude is outside the acceptable range.

    Args:
        message (str, optional): Custom error message. Defaults to a standard message.

    Examples:
        The following are examples of how this error can be raised:

        - **General amplitude issue**

            >>> raise CurrentAmplitudeError(
            >>>     "The specified current amplitude is invalid or exceeds limits."
            >>> )

        - **Amplitude exceeds maximum limit**

            >>> raise CurrentAmplitudeError(
            >>>     f"The specified current amplitude {current_amplitude} A exceeds
            >>>     the maximum allowed limit of {max_current_amplitude} A."
            >>> )
    """

    def __init__(
        self,
        message: str = "The specified current amplitude is invalid or exceeds limits.",
    ):
        """Initialize the Current Amplitude Error with a default message."""
        super().__init__(code=5009, message=message)


class ParallelDevicesConfigurationError(BCQError):
    """Exception raised when there is an issue with parallel devices configuration.

    This error occurs when the configuration of devices connected in parallel
    is invalid or incompatible with the test requirements.

    Args:
        message (str, optional): Custom error message. Defaults to a standard message.

    Example:
        >>> raise ParallelDevicesConfigurationError(
        >>>     "Invalid channel modes. Must have exactly 1 leader channel
        >>>     and 1 or more follower channels."
        >>> )
    """

    def __init__(
        self,
        message: str = "Invalid channel modes. Must have exactly 1 leader channel and 1 or more follower channels.",
    ):
        """Initialize the Parallel Devices Configuration Error with a default message."""
        super().__init__(code=5010, message=message)


class DMMParameterError(BCQError):
    """Exception raised when some parameter related to the DMM is incorrect.

    These, for example, indicate that some pre-required steps
    are not done yet on the DMM's workflow.

    This error is specific for the NIBCQ Python API.

    Args:
        message (str, optional): Custom error message. Defaults to a standard message.

    Examples:
        The following are examples of how this error can be raised:

        - **General: Incorrect Parameter**

            >>> raise DMMParameterError("DMM Parameters are set incorrectly.")

        - **Specific: Measurement not finished before wanting to access it**

            >>> raise DMMParameterError("DMM Measurement is not available.")
    """

    def __init__(self, message: str = "DMM Parameters are set incorrectly."):
        """Initialize the DMM Parameter Error with a default message."""
        super().__init__(code=5101, message=message)


class TemperatureError(BCQError):
    """Exception raised when some check or parameter related to the temperature is incorrect.

    These indicate that a thermocouple is either set incorrectly, or there was an error
    with the measured temperature depending on the set limits, or with the limit setting.

    This error is specific for the NIBCQ Python API.

    Some temperature-related checks are only throwing error through a logger, please
    be mindful of this when implementing error handling. Warnings are logged to stderr by default.

    Args:
        message (str, optional): Custom error message. Defaults to a standard message.

    Examples:
        The following are examples of how this error can be raised:

        - **General: Thermocouple error**

            >>> raise TemperatureError("Error occurred while trying to use the thermocouple.")

        - **Specific: Settings not configured**

            >>> raise TemperatureError(
            >>>     "Thermocouple settings are not configured. Use 'setup_thermocouple' first!"
            >>> )

        - **Specific: Measured temperature and limit difference**

            >>> raise TemperatureError(
            >>>     f"Current temperature {temp} exceeds target"
            >>>     f"temperature {target_temp} ± {actual_delta}."
            >>> )

        - **Specific: The device does not support Temperature measurements**

            >>> raise TemperatureError("Device has no temperature capability configured.")

    """

    def __init__(self, message: str = "Error occurred while trying to use the thermocouple."):
        """Initialize the Temperature Error with a default message."""
        super().__init__(code=5102, message=message)
