"""
Module defining LogLevel and AutoDeployOption enumerations with string conversion methods.
"""

from enum import IntEnum


class LogLevel(IntEnum):
    """
    Enum class representing different log levels.
    """

    NONE = 0
    """
    Represents the option when logging is turned off or not enabled.
    """

    TRACE = 1
    """
    Represents the option for tracing log level.
    """

    DEBUG = 2
    """
    Represents the option for debug log level.
    """

    INFORMATION = 3
    """
    Represents the option for information log level.
    """

    WARNING = 4
    """
    Represents the option for warning log level.
    """

    ERROR = 5
    """
    Represents the option for error log level.
    """

    CRITICAL = 6
    """
    Represents the option for critical log level.
    """

    def __str__(self):
        """
        Returns a title-case string representation of the enum member.

        Returns:
            str: Title-case string representation of the enum member.
        """
        return self.name.title()

    @staticmethod
    def from_string(value):
        """
        Converts a string value to the corresponding enum member.

        Args:
            value (str): The string value to convert.

        Returns:
            Enum: The corresponding enum member if the value is valid, otherwise NONE.
        """
        try:
            return LogLevel[value.upper()]
        except KeyError:
            return LogLevel.NONE


class AutoDeployOption(IntEnum):
    """
    An enumeration of auto deploy options for applications from different repositories.
    """

    NONE = 0
    """
    Represents the option to not enable auto deploy.
    """

    DEV = 1
    """
    Represents the option to auto deploy from the development repository.
    """

    TEST = 2
    """
    Represents the option to auto deploy from the testing repository.
    """

    RELEASE = 3
    """
    Represents the option to auto deploy from the release repository.
    """

    def __str__(self):
        """
        Returns a lowercase string representation of the enum member.

        Returns:
            str: Lowercase string representation of the enum member.
        """
        return self.name.lower()

    @staticmethod
    def from_string(value):
        """
        Converts a string value to the corresponding enum member.

        Args:
            value (str): The string value to convert.

        Returns:
            Enum: The corresponding enum member if the value is valid, otherwise None.
        """
        try:
            return AutoDeployOption[value.upper()]
        except KeyError:
            return AutoDeployOption.NONE
