"""Defines the WorkItemInfo dataclass, encapsulating details about a work item."""

# pylint: disable=invalid-name

# Include a __future__ import so that all annotations by default are forward-declared
from __future__ import annotations

from dataclasses import dataclass, field

from .work_status import WorkStatus


@dataclass
class WorkItemInfo:
    """Represents information about a work item."""

    Id: str = ""
    """
    Gets or sets the ID of the work item. 

    If not specified, this is set to an empty string.
    """

    ParentId: str = ""
    """
    Gets or sets the ID of the parent work item. 

    If not specified, this is set to an empty string.
    """

    JobId: str = ""
    """
    Gets or sets the ID of the job. 

    If not specified, this is set to an empty string.
    """

    Progress: float = 0.0
    """
    Gets or sets the progress of the work item, defined as a fraction of 1 where 0 = no progress and
    1 = complete. 

    If not specified, this is set to 0.0.
    """

    Status: WorkStatus = WorkStatus.Unknown
    """
    Gets or sets the status of the work item. 

    If not specified, this is set to WorkStatus.Unknown.
    """

    Message: str = ""
    """
    Gets or sets a message associated with the work item. 

    If not specified, this is set to an empty string.
    """

    WorkDuration: int = 0
    """
    Gets or sets the duration of the work in milliseconds. 

    If not specified, this is set to 0.
    """

    WorkItemErrorInfo: list[WorkItemInfo] = field(default_factory=list)
    """
    Gets or sets a list of error information associated with the work item. 

    If not specified, this is set to an empty list.
    """
