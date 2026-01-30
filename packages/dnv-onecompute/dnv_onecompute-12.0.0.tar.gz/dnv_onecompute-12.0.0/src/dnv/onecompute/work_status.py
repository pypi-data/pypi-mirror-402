"""Defines the WorkStatus enumeration, representing various stages in a work item's lifecycle."""

# pylint: disable=invalid-name

# Include a __future__ import so that all annotations by default are forward-declared
from __future__ import annotations

from enum import IntEnum, unique


@unique
class WorkStatus(IntEnum):
    """
    Enumerates the possible statuses for a work item.

    Each status represents a distinct stage in the execution lifecycle of a work item.
    """

    Unknown = -1  # 0xFFFFFFFF
    """Unknown status."""

    Created = 0
    """The work item has been created."""

    Pending = 1
    """The work item has been scheduled for execution, but execution has not started."""

    Executing = 2
    """The work item is being processed."""

    Suspended = 3
    """The processing of the work item has been suspended"""

    Completed = 4
    """The processing of the work item has completed successfully and is terminated."""

    Faulting = 5
    """The processing of the work item is failing."""

    Faulted = 6
    """The processing of the work item has faulted and is terminated."""

    Aborting = 7
    """The user has requested to abort the processing of the work item."""

    Aborted = 8
    """The processing of the work item has been aborted and is terminated."""

    @staticmethod
    def is_terminal(val: WorkStatus) -> bool:
        """
        Determines if the provided work status value represents a terminal state.

        A work status is considered terminal if it is either Aborted, Faulted, or Completed.

        Args:
            val (WorkStatus): The work status value to check.

        Returns:
            bool: True if the work status is terminal, False otherwise.
        """
        return val in {WorkStatus.Aborted, WorkStatus.Faulted, WorkStatus.Completed}
