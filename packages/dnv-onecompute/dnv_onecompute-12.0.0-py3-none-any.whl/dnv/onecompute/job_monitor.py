"""This module contains the JobMonitor class, which implements the IJobMonitor interface for"""

import asyncio
import contextlib
from abc import ABC, abstractmethod
from dataclasses import dataclass
from typing import Optional

from cancel_token import CancellationToken

from .event import Event
from .job_info import JobInfo
from .one_compute_client import OneComputeClient
from .work_item_info import WorkItemInfo
from .work_status import WorkStatus


@dataclass
class JobEventArgs:
    """Represents the arguments for a job event."""

    job_id: str = ""
    """
    Gets or sets the unique identifier of the job. 

    If not specified, this is set to an empty string.
    """

    work_status: WorkStatus = WorkStatus.Unknown
    """
    Gets or sets the current status of the job. 

    If not specified, this is set to WorkStatus.Unknown.
    """

    progress: float = 0.0
    """
    Gets or sets the progress of the job as a float between 0.0 and 1.0. 

    If not specified, this is set to 0.0.
    """

    message: str = ""
    """
    Gets or sets a message associated with the job event. 

    If not specified, this is set to an empty string.
    """


@dataclass
class WorkItemEventArgs:
    """Represents the arguments for a work item event."""

    job_id: str = ""
    """
    Gets or sets the unique identifier of the job associated with the work item. 

    If not specified, this is set to an empty string.
    """

    work_item_id: str = ""
    """
    Gets or sets the unique identifier of the work item. 

    If not specified, this is set to an empty string.
    """

    work_status: WorkStatus = WorkStatus.Unknown
    """
    Gets or sets the current status of the work item. 

    If not specified, this is set to WorkStatus.Unknown.
    """

    progress: float = 0.0
    """
    Gets or sets the progress of the work item as a float between 0.0 and 1.0. 

    If not specified, this is set to 0.0.
    """

    message: str = ""
    """
    Gets or sets a message associated with the work item event. 

    If not specified, this is set to an empty string.
    """


class IJobMonitor(ABC):
    """Interface for monitoring job events."""

    @property
    @abstractmethod
    def job_status_changed(self) -> Event:
        """Event that is triggered when the job status changes."""

    @property
    @abstractmethod
    def job_progress_changed(self) -> Event:
        """Event that is triggered when the job progress changes."""

    @property
    @abstractmethod
    def work_item_status_changed(self) -> Event:
        """Event that is triggered when the work item status changes."""

    @property
    @abstractmethod
    def work_item_progress_changed(self) -> Event:
        """Event that is triggered when the work item progress changes."""

    @abstractmethod
    async def await_job_termination_async(
        self, cancellation_token: Optional[CancellationToken] = None
    ) -> WorkStatus:
        """
        Asynchronously waits for the job to terminate.

        Args:
            cancellationToken (Optional[CancellationToken]): Token to cancel the operation.
                Defaults to None.

        Returns:
            WorkStatus: The status of the job.
        """


class JobMonitor(IJobMonitor):
    """Implements the IJobMonitor interface for monitoring job events."""

    def __init__(self, one_compute_platform_client: OneComputeClient):
        """
        Initializes a new instance of the JobMonitor class.

        Args:
            one_compute_platform_client (OneComputeClient): The client used to interact with the
                OneCompute platform.
        """
        super().__init__()

        self._job_termination_event = asyncio.Event()

        self._workitem_status_notified: dict[str, WorkItemEventArgs] = {}
        self._job_status_notified: dict[str, JobEventArgs] = {}

        self._job_status_changed = Event()
        self._job_progress_changed = Event()
        self._work_item_status_changed = Event()
        self._work_item_progress_changed = Event()

        self._one_compute_platform_client = one_compute_platform_client
        self._job_status = WorkStatus.Unknown
        self._job_status_changed += self.__job_status_changed

    @property
    def job_status_changed(self) -> Event:
        return self._job_status_changed

    @property
    def job_progress_changed(self) -> Event:
        return self._job_progress_changed

    @property
    def work_item_status_changed(self) -> Event:
        return self._work_item_status_changed

    @property
    def work_item_progress_changed(self) -> Event:
        return self._work_item_progress_changed

    async def await_job_termination_async(
        self, cancellation_token: Optional[CancellationToken] = None
    ) -> WorkStatus:
        if WorkStatus.is_terminal(self._job_status):
            self._workitem_status_notified.clear()
            self._job_status_notified.clear()
            return self._job_status
        while not await self.__event_wait(self._job_termination_event, 1):
            pass
        self._workitem_status_notified.clear()
        self._job_status_notified.clear()
        return self._job_status

    async def begin_monitor_job(
        self, job_id: str, cancellation_token: Optional[CancellationToken] = None
    ):
        """
        Begins monitoring a job with the given job_id. This method continuously polls the job status
        and work items info from the OneCompute platform client. It processes work items events and
        job events, and breaks the loop if the job reaches a terminal state or if an exception
        occurs.

        Args:
            job_id (str): The unique identifier of the job to monitor.
            cancellation_token (Optional[CancellationToken]): Token to cancel the operation.
                Defaults to None.

        Raises:
            Exception: Any exception raised during the execution will be printed and will cause the
                job termination event to be set.
        """

        async def wait():
            await asyncio.sleep(
                self._one_compute_platform_client.polling_interval_seconds * 1
            )

        await asyncio.sleep(1)
        while True:
            try:
                job_info = await self._one_compute_platform_client.get_job_status_async(
                    job_id
                )
                if job_info is None:
                    await wait()
                    continue

                work_items_info = (
                    await self._one_compute_platform_client.get_workitems_info_async(
                        job_id
                    )
                )
                if work_items_info is None or work_items_info == []:
                    await wait()
                    continue

                await self.__process_work_items_event(work_items_info)
                await self.__process_job_event(job_info)

                if WorkStatus.is_terminal(job_info.Status):
                    break
            except Exception as e:
                print(e)
                self._job_termination_event.set()
                break
            await wait()

    async def __process_work_items_event(self, workitems_info: list[WorkItemInfo]):
        """
        Processes work items events. For each work item in the provided list, it checks if the work
        item status is terminal. It then creates a WorkItemEventArgs object with the work item
        details. If the work item status has not been notified before or has changed, it updates the
        notified status and triggers the appropriate event based on whether the status is terminal
        or not.

        Args:
            workitems_info (list[WorkItemInfo]): List of work items to process.
        """
        for work_item in workitems_info:
            is_terminal = WorkStatus.is_terminal(work_item.Status)
            workitem_event_args = WorkItemEventArgs(
                job_id=work_item.JobId,
                work_item_id=work_item.Id,
                work_status=work_item.Status,
                message=work_item.Message,
                progress=1.0 if is_terminal else work_item.Progress,
            )

            if (
                work_item.Id in self._workitem_status_notified
                and self._workitem_status_notified[work_item.Id] == workitem_event_args
            ):
                continue

            self._workitem_status_notified[work_item.Id] = workitem_event_args
            if is_terminal:
                await self.work_item_status_changed(
                    self._one_compute_platform_client, workitem_event_args
                )
            else:
                await self.work_item_progress_changed(
                    self._one_compute_platform_client, workitem_event_args
                )

    async def __process_job_event(self, job_info: JobInfo):
        """
        Processes job events. It checks if the job status is terminal and creates a JobEventArgs
        object with the job details. If the job status has not been notified before or has changed,
        it updates the notified status and triggers the appropriate event based on whether the
        status is terminal or not.

        Args:
            job_info (JobInfo): Information about the job to process.
        """
        is_terminal = WorkStatus.is_terminal(job_info.Status)
        job_event_args = JobEventArgs(
            job_id=job_info.JobId,
            work_status=job_info.Status,
            message=job_info.Message,
            progress=1.0 if is_terminal else job_info.Progress,
        )
        if (
            job_info.JobId in self._job_status_notified
            and self._job_status_notified[job_info.JobId] == job_event_args
        ):
            return
        self._job_status_notified[job_info.JobId] = job_event_args
        if is_terminal:
            await self.job_status_changed(
                self._one_compute_platform_client, job_event_args
            )
        else:
            await self.job_progress_changed(
                self._one_compute_platform_client, job_event_args
            )

    async def __job_status_changed(self, sender: object, e: JobEventArgs):
        """
        Handles the job status changed event. It updates the job status and if the status is
        terminal,it sets the job termination event.

        Args:
            sender (object): The object that raised the event.
            e (JobEventArgs): The arguments associated with the job status changed event.
        """
        self._job_status = e.work_status
        if WorkStatus.is_terminal(self._job_status) is True:
            self._job_termination_event.set()

    async def __event_wait(self, evt: asyncio.Event, timeout: int):
        """
        Waits for the specified event to be set or for the specified timeout to elapse.

        Args:
            evt (asyncio.Event): The event to wait for.
            timeout (int): The number of seconds to wait before timing out.

        Returns:
            bool: True if the event was set, False otherwise.
        """
        with contextlib.suppress(asyncio.TimeoutError):
            await asyncio.wait_for(evt.wait(), timeout)
        return evt.is_set()
