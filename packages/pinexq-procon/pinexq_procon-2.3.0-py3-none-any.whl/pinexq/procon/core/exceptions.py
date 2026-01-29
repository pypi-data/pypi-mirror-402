"""
Module-specific exceptions

Exceptions for all defined error cases and wrapper for ProblemJSON-formatted
error reporting.
"""


class ProConException(Exception):
    """Parent class for all module-specific Exceptions

    Attributes:
        user_message: Custom message visible to the end user.

    """
    user_message: str | None = None

    def __init__(self, *args, user_message: str = "", **kwargs):
        super().__init__(*args, **kwargs)
        self.user_message = user_message


class ProConUnknownFunctionError(ProConException):
    """A function of the requested name could not be found

    Attributes:
        function_name: Name of the *unknown* function.
    """
    function_name: str

    def __init__(self, *args, func_name: str = "", **kwargs):
        super().__init__(*args, **kwargs)
        self.function_name = func_name


class ProConMessageRejected(ProConException):
    """Invalid or malformed message received"""


class ProConBadMessage(ProConException):
    """Received message can not be processed"""


class ProConSchemaValidationError(ProConException):
    """The data does not match the function annotation"""


class ProConSchemaError(ProConException):
    """Function schema can not be generated """


class ProConDataslotError(ProConException):
    """There's a problem with the dataslots """


class ProConWorkerNotAvailable(ProConException):
    """Already processing or no resources available to process a job"""


class ProConJobExecutionError(ProConException):
    """Custom exception raised to stop the execution."""

class ProConShutdown(ProConException):
    """Custom exception that triggers a clean shutdown of ProCon."""
