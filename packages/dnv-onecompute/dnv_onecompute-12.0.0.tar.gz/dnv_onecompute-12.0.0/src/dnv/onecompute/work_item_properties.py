"""
Defines the WorkItemProperties dataclass and ResultStorageTypes enum, utilized for handling work
item properties and result storage types.
"""

# pylint: disable=invalid-name

from collections import defaultdict
from dataclasses import dataclass, field
from enum import IntEnum, unique
from typing import Any


@unique
class ResultStorageTypes(IntEnum):
    """Enumerates types of result stores."""

    Unknown = 0
    """The storage of results from the work item is unknown."""

    UserContainer = 1
    """Results from the work item is stored in the user's container."""

    ResultLake = 2
    """Results from the work item is stored in the Result Lake."""


@dataclass
class WorkItemProperties:
    """Contains application properties for work items."""

    JobId: str = ""
    """
    Gets or sets the unique identifier for the job associated with the work item. 

    If not specified, this is set to an empty string.
    """

    Id: str = ""
    """
    Gets or sets the unique identifier of the work item. 

    If not specified, this is set to an empty string.
    """

    Tag: str = ""
    """
    Gets or sets a client-specified tag serving as a recognizable prefix for the job ID. This tag
    does not need to be unique.

    If not specified, this is set to an empty string.
    """

    ParentId: str = ""
    """
    Gets or sets the unique identifier for the parent work item. 

    If not specified, this is set to an empty string, indicating no parent work item.
    """

    BatchNumber: int = 0
    """
    Gets or sets the batch number for the work item. 

    If not specified, this is set to 0.
    """

    ResultStorageType: ResultStorageTypes = ResultStorageTypes.Unknown
    """
    Gets or sets the type of storage used for the results of the work item.

    If not specified, this is set to ResultStorageTypes.Unknown, indicating an unknown storage type.
    """

    WorkItemDirectory: str = ""
    """
    Gets or sets the directory for the work item.

    If not specified, this is set to an empty string, indicating no specified directory.
    """

    Properties: dict[str, Any] = field(default_factory=lambda: defaultdict(dict))
    """
    Gets or sets a dictionary of properties for the work item.

    If not specified, this is set to an empty dictionary.
    """
