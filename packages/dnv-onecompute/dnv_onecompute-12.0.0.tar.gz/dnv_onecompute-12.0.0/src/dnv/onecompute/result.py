"""This module defines the Result class, which encapsulates the outcome of a processed WorkUnit."""

# pylint: disable=invalid-name

from dataclasses import dataclass, field
from typing import Optional


@dataclass
class DataContainer:
    """A container for data."""

    Version: int = 1
    """
    Gets or sets the version of the data. 

    If not specified, this is set to 1.
    """

    Content: Optional[object] = None
    """
    Gets or sets the actual data. Can be any object or None. 

    If not specified, this is set to None.
    """


@dataclass
class Result:
    """
    Wraps the application result from processing a WorkUnit.

    The Result class wraps an application result object in the same way as WorkUnit wraps
    application input. The application worker processes the associated WorkUnit by taking
    the application input from it and optionally producing an application result object that
    is returned from the ExecuteAsync method of the worker.

    The WorkerHost invoking the worker will then wrap the application result object in a
    Result and store it to permanent storage using an implementation of
    IFlowModelStorageService[Result].
    """

    Id: str = ""
    """
    Gets or sets the context identifier. 

    If not specified, this is set to an empty string.
    """

    JobId: str = ""
    """
    Gets or sets the job identifier. 

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
    Gets or sets the parent identifier. 

    If not specified, this is set to an empty string.
    """

    BatchNumber: int = 0
    """
    Gets or sets the batch number for the work item. 

    If not specified, this is set to 0.
    """

    Data: DataContainer = field(default_factory=DataContainer)
    """
    Gets or sets the data container of results from the processing of the WorkUnit. 

    If not specified, this is set to a new instance of DataContainer.
    """

    @property
    def WorkItemId(self) -> str:
        """
        Gets the work item identifier.

        This is equivalent to the context identifier (Id).
        """
        return self.Id
