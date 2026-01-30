"""Module containing the Environment enumeration."""

# pylint: disable=invalid-name
from enum import Enum, unique


@unique
class Environment(Enum):
    """
    Enumeration of possible environments.

    Each environment is represented by a unique constant value that can be accessed as an attribute
    of the class.
    """

    Development = 0
    """Development environment."""

    Testing = 1
    """Testing environment."""

    Staging = 2
    """Staging environment."""

    Production = 3
    """Production environment."""

    DevCore = 4
    """DevCore environment."""
