"""Defines the WorkItemStorageInfo dataclass, representing storage information for a work item."""

# pylint: disable=invalid-name

from dataclasses import dataclass


@dataclass
class WorkItemStorageInfo:
    """
    Represents storage information for a work item.
    """

    WorkItemId: str = ""
    """
    Gets or sets the unique identifier for the work item.

    By default, this is set to an empty string, indicating no associated work item.
    """

    ContainerUri: str = ""
    """
    Gets or sets the URI of the container storing the output files of the work item.

    The default value is an empty string, indicating that no container has been specified.
    """
