"""
This module defines the JobInfo dataclass, encapsulating key details about a job in the system.
"""

# pylint: disable=invalid-name

from dataclasses import dataclass

from .work_status import WorkStatus


@dataclass
class JobInfo:
    """Represents information about a job."""

    JobId: str = ""
    """
    Gets or sets the unique identifier of the job. 

    If not specified, this is set to an empty string.
    """

    JobName: str = ""
    """
    Gets or sets the name of the job. 

    If not specified, this is set to an empty string.
    """

    UserId: str = ""
    """
    Gets or sets the user identifier associated with the job. 

    If not specified, this is set to an empty string.
    """

    ServiceName: str = ""
    """
    Gets or sets the name of the service that the job is associated with. 

    If not specified, this is set to an empty string.
    """

    PoolId: str = ""
    """
    Gets or sets the pool identifier that the job is associated with. 

    If not specified, this is set to an empty string.
    """

    EnvironmentId: str = ""
    """
    Gets or sets the environment identifier where the job is executed.

    If not specified, this is set to an empty string.
    """

    Progress: float = 0.0
    """
    Gets or sets the progress of the job, defined as a float between 0.0 and 1.0, where 0 indicates
    no progress and 1 represents completion.

    If not specified, this is set to 0.0.
    """

    Status: WorkStatus = WorkStatus.Unknown
    """
    Gets or sets the current status of the job. 

    If not specified, this is set to WorkStatus.Unknown.
    """

    Message: str = ""
    """
    Gets or sets a message associated with the job. 

    If not specified, this is set to an empty string.
    """

    StartTime: str = ""
    """
    Gets or sets the start time of the job in UTC. 

    If not specified, this is set to an empty string.
    """

    CompletionTime: str = ""
    """
    Gets or sets the completion time of the job in UTC. 

    If not specified, this is set to an empty string.
    """

    TotalComputeSeconds: int = 0
    """
    Gets or sets the total compute seconds consumed by the job. 

    If not specified, this is set to 0.
    """

    ClientReference: str = ""
    """
    Gets or sets the client reference associated with the job. 

    If not specified, this is set to an empty string.
    """
