"""
This module defines the OneComputeClient class, facilitating interactions with the OneCompute API.
"""

import asyncio
import json
from http import HTTPStatus
from typing import Any, Optional

import httpx

from .authenticator import IAuthenticator
from .bearer_auth import BearerAuth
from .flowmodel import Job
from .httpx_client import AsyncRetryClient, RetryClient
from .job_info import JobInfo
from .json_utils import from_data
from .result import Result
from .web_apis_template import WebAPIsTemplate as WebApi
from .work_item_info import WorkItemInfo
from .work_item_properties import WorkItemProperties
from .work_item_storage_info import WorkItemStorageInfo


class OneComputeClient:
    """
    A client for the OneCompute platform, providing methods for creating blob URIs, retrieving work
    item properties, logging in to the platform, submitting and monitoring jobs, etc.
    """

    def __init__(self, base_url: str, authenticator: Optional[IAuthenticator] = None):
        """
        Initializes a OneComputeClient instance with the provided authenticator and base URL.

        Args:
            base_url (str): The base URL for the HTTP requests.

            authenticator (Optional[IAuthenticator]): The authenticator for bearer token
                authentication. Default to None.
        """
        self.authenticator = authenticator
        self._polling_interval_seconds = 10
        self._http_config: dict[str, Any] = {
            "timeout": None,
            "base_url": base_url,
            "auth": BearerAuth(authenticator) if authenticator else None,
        }

    @property
    def polling_interval_seconds(self) -> int:
        """
        Gets or sets the polling interval in seconds.

        Returns:
            The current polling interval in seconds.
        """
        return self._polling_interval_seconds

    @polling_interval_seconds.setter
    def polling_interval_seconds(self, value: int) -> None:
        """
        Sets the polling interval in seconds.

        Args:
            value: The new polling interval in seconds.
        """
        self._polling_interval_seconds = value

    def create_blob_uris(self, container_name: str, blob_paths: list[str]) -> list[str]:
        """
        Creates a list of blob URIs for the given container and blob paths.

        Args:
            container_name (str): The name of the container to use.
            blob_paths (list of str): A list of blob paths to create URIs for.

        Returns:
            list[str]: A list of blob URIs corresponding to the given container and blob paths.
        """
        resp = self.__post(
            WebApi.BLOBS.format(container_name=container_name),
            data=blob_paths,
        )
        json_resp = self.__get_content(resp, err_msg="Could not create BLOB URIs.")
        return json_resp

    async def create_blob_uris_async(
        self, container_name: str, blob_paths: list[str]
    ) -> list[str]:
        """
        Asynchronously creates a list of blob URIs for the given container and blob paths.

        Args:
            container_name (str): The name of the container to use.
            blob_paths (list of str): A list of blob paths to create URIs for.

        Returns:
            list[str]: A list of blob URIs corresponding to the given container and blob paths.
        """
        resp = await self.__post_async(
            WebApi.BLOBS.format(container_name=container_name),
            data=blob_paths,
        )
        json_resp = self.__get_content(resp, err_msg="Could not create BLOB URIs.")
        return json_resp

    def get_workitem_properties(
        self, job_id: str, workitem_id: str = ""
    ) -> list[WorkItemProperties] | None:
        """
        Gets the properties of the specified work item or work items.

        Args:
            job_id (str): The ID of the job that the work item belongs to.
            workitem_id (str, optional): The ID of the work item to retrieve properties for.
                If not specified, all work items in the job will be returned. Defaults to "".

        Returns:
            list[WorkItemProperties] or None: A list of work item properties or None if no work
            items are found or if the json response is none.
        """
        json_resp = self.__get(WebApi.work_item_properties(job_id, workitem_id))
        return (
            None
            if json_resp is None
            else (
                [from_data(WorkItemProperties, json_resp)]
                if workitem_id
                else [from_data(WorkItemProperties, json_wip) for json_wip in json_resp]
            )
        )

    async def get_workitem_properties_async(
        self, job_id: str, workitem_id: str = ""
    ) -> list[WorkItemProperties] | None:
        """
        Asynchronously gets the properties of the specified work item or work items.

        Args:
            job_id (str): The ID of the job that the work item belongs to.
            workitem_id (str, optional): The ID of the work item to retrieve properties for.
                If not specified, all work items in the job will be returned. Defaults to "".

        Returns:
            list[WorkItemProperties] or None: A list of work item properties or None if no work
            items are found or if the json response is none.
        """
        json_resp = await self.__get_async(
            WebApi.work_item_properties(job_id, workitem_id)
        )
        return (
            None
            if json_resp is None
            else (
                [from_data(WorkItemProperties, json_resp)]
                if workitem_id
                else [from_data(WorkItemProperties, json_wip) for json_wip in json_resp]
            )
        )

    def get_workitem_results(self, job_id: str) -> list[Result] | None:
        """
        Gets the results of all work items in the specified job.

        Args:
            job_id (str): The ID of the job to get work item results for.

        Returns:
            list[Result] or None: A list of Result objects representing the results of all work
            items in the job, or None if no results are found.
        """
        json_resp = self.__get(WebApi.WORK_ITEM_RESULTS.format(job_id=job_id))
        return (
            None
            if json_resp is None
            else [from_data(Result, result) for result in json_resp]
        )

    async def get_workitem_results_async(self, job_id: str) -> list[Result] | None:
        """
        Asynchronously gets the results of all work items in the specified job.

        Args:
            job_id (str): The ID of the job to get work item results for.

        Returns:
            list[Result] or None: A list of Result objects representing the results of all work
            items in the job, or None if no results are found.
        """
        json_resp = await self.__get_async(
            WebApi.WORK_ITEM_RESULTS.format(job_id=job_id)
        )
        return (
            None
            if json_resp is None
            else [from_data(Result, result) for result in json_resp]
        )

    def get_workitem_result(self, job_id: str, workitem_id: str) -> Result | None:
        """
        Gets the result of the specified work item.

        Args:
            job_id (str): The ID of the job that the work item belongs to.
            workitem_id (str): The ID of the work item to retrieve the result for.

        Returns:
            Result or None: The result of the specified work item, or None if no result is found.
        """
        json_resp = self.__get(
            WebApi.WORK_ITEM_RESULT.format(job_id=job_id, workitem_id=workitem_id)
        )
        return None if json_resp is None else from_data(Result, json_resp)

    async def get_workitem_result_async(
        self, job_id: str, workitem_id: str
    ) -> Result | None:
        """
        Asynchronously gets the result of the specified work item.

        Args:
            job_id (str): The ID of the job that the work item belongs to.
            workitem_id (str): The ID of the work item to retrieve the result for.

        Returns:
            Result or None: The result of the specified work item, or None if no result is found.
        """
        json_resp = await self.__get_async(
            WebApi.WORK_ITEM_RESULT.format(job_id=job_id, workitem_id=workitem_id)
        )
        return None if json_resp is None else from_data(Result, json_resp)

    def get_job_status(self, job_id: str) -> JobInfo | None:
        """
        Gets the status of the specified job identifier.

        Args:
            job_id (str): The ID of the job.

        Returns:
            JobInfo or None: The job info of the specified job, or None if no job info is found.
        """
        json_resp = self.__get(WebApi.JOBS_INFO.format(job_id=job_id))
        return None if json_resp is None else from_data(JobInfo, json_resp)

    async def get_job_status_async(self, job_id: str) -> JobInfo | None:
        """
        Asynchronously gets the status of the specified job identifier.

        Args:
            job_id (str): The ID of the job.

        Returns:
            JobInfo or None: The job info of the specified job, or None if no job info is found.
        """
        json_resp = await self.__get_async(WebApi.JOBS_INFO.format(job_id=job_id))
        return None if json_resp is None else from_data(JobInfo, json_resp)

    def get_workitems_info(self, job_id: str) -> list[WorkItemInfo] | None:
        """
        Gets the information of all the work items that belong to the specified job.

        Args:
            job_id (str): The ID of the job.

        Returns:
            list[WorkItemInfo] or None: The list of work item info of the specified job, or None if
            no job or work items do not exist.
        """
        json_resp = self.__get(WebApi.WORK_ITEMS.format(job_id=job_id))
        return (
            None
            if json_resp is None
            else [from_data(WorkItemInfo, json_wii) for json_wii in json_resp]
        )

    async def get_workitems_info_async(self, job_id: str) -> list[WorkItemInfo] | None:
        """
        Asynchronously gets the information of all the work items that belong to the specified job.

        Args:
            job_id (str): The ID of the job.

        Returns:
            list[WorkItemInfo] or None: The list of work item info of the specified job, or None if
            no job or work items do not exist.
        """
        json_resp = await self.__get_async(WebApi.WORK_ITEMS.format(job_id=job_id))
        return (
            None
            if json_resp is None
            else [from_data(WorkItemInfo, json_wii) for json_wii in json_resp]
        )

    def get_containers(self) -> list[str] | None:
        """
        Gets a list of container names.

        Returns:
            list[str] or None: A list of container names, or None if the request was unsuccessful.
        """
        json_resp = self.__get(WebApi.CONTAINERS)
        return json_resp

    async def get_containers_async(self) -> list[str] | None:
        """
        Asynchronously gets a list of container names.

        Returns:
            list[str] or None: A list of container names, or None if the request was unsuccessful.
        """
        json_resp = await self.__get_async(WebApi.CONTAINERS)
        return json_resp

    def get_container_uri(self, container_name: str, days: int = 1) -> str | None:
        """
        Gets the URI for the specified container.

        Args:
            container_name (str): The name of the container to get the URI for.
                days (int): The number of days the URI is valid for (default is 1).

        Returns:
            str or None: The URI for the specified container, or None if the request was
            unsuccessful.
        """
        text_resp = self.__get(
            WebApi.CONTAINER_URI.format(container_name=container_name, days=days),
            False,
        )
        return text_resp

    async def get_container_uri_async(
        self, container_name: str, days: int = 1
    ) -> str | None:
        """
        Asynchronously gets the URI for the specified container.

        Args:
            container_name (str): The name of the container to get the URI for.
                days (int): The number of days the URI is valid for (default is 1).

        Returns:
            str or None: The URI for the specified container, or None if the request was
            unsuccessful.
        """
        text_resp = await self.__get_async(
            WebApi.CONTAINER_URI.format(container_name=container_name, days=days),
            False,
        )
        return text_resp

    def get_workitem_storage_container_uri(
        self, job_id: str, work_unit_id: str, container_name: str
    ) -> str:
        """
        Returns a container URI with a valid SAS token for the specified job ID, work item ID,
        and container for the job submitted with the Result Lake storage option.

        Args:
            job_id (str): The ID of the job to retrieve storage information for.
            work_unit_id (str): The ID of the work unit to retrieve storage information for.
            container_name (str): The name of the container to retrieve storage information for.

        Returns:
            str: A container URI with a valid SAS token. An empty str will be returned for the job
            submitted without the Result Lake storage option.
        """
        resp = self.__get(
            WebApi.WORK_ITEM_STORAGE_CONTAINER_URI.format(
                job_id=job_id, workitem_id=work_unit_id, container_name=container_name
            ),
            json_content=False,
        )
        return resp if not resp is None else ""

    async def get_workitem_storage_container_uri_async(
        self, job_id: str, work_unit_id: str, container_name: str
    ) -> str:
        """
        Returns a container URI with a valid SAS token for the specified job ID, work item ID,
        and container for the job submitted with the Result Lake storage option.

        Args:
            job_id (str): The ID of the job to retrieve storage information for.
            work_unit_id (str): The ID of the work unit to retrieve storage information for.
            container_name (str): The name of the container to retrieve storage information for.

        Returns:
            str: A container URI with a valid SAS token. An empty str will be returned for the job
            submitted without the Result Lake storage option.
        """
        resp = await self.__get_async(
            WebApi.WORK_ITEM_STORAGE_CONTAINER_URI.format(
                job_id=job_id, workitem_id=work_unit_id, container_name=container_name
            ),
            json_content=False,
        )
        return resp if not resp is None else ""

    def get_workitem_storage_info(
        self, job_id: str, container_name: str
    ) -> list[WorkItemStorageInfo]:
        """
        Returns a list of `WorkItemStorageInfo` objects for the specified job ID and container.
        The list includes only work items that have results stored in the Result Lake storage.

        Args:
            job_id (str): The ID of the job to retrieve storage information for.
            container_name (str): The name of the container to retrieve storage information for.

        Returns:
            list[WorkItemStorageInfo]: A list of `WorkItemStorageInfo` objects for the specified
            job ID and container. Each `WorkItemStorageInfo` object contains information about a
            work item that has results stored in the Result Lake storage. An empty list will be
            returned for the job submitted without the Result Lake storage option.
        """
        json_resp = self.__get(
            WebApi.WORK_ITEM_STORAGE_INFO.format(
                job_id=job_id, container_name=container_name
            ),
        )
        return (
            list[WorkItemStorageInfo]()
            if json_resp is None
            else [from_data(WorkItemStorageInfo, json_wisi) for json_wisi in json_resp]
        )

    async def get_workitem_storage_info_async(
        self, job_id: str, container_name: str
    ) -> list[WorkItemStorageInfo]:
        """
        Returns a list of `WorkItemStorageInfo` objects for the specified job ID and container
        asynchronously.
        The list includes only work items that have results stored in the Result Lake storage.

        Args:
            job_id (str): The ID of the job to retrieve storage information for.
            container_name (str): The name of the container to retrieve storage information for.

        Returns:
            list[WorkItemStorageInfo]: A list of `WorkItemStorageInfo` objects for the specified
            job ID and container. Each `WorkItemStorageInfo` object contains information about a
            work item that has results stored in the Result Lake storage. An empty list will be
            returned for the job submitted without the Result Lake storage option.
        """
        json_resp = await self.__get_async(
            WebApi.WORK_ITEM_STORAGE_INFO.format(
                job_id=job_id, container_name=container_name
            ),
        )
        return (
            list[WorkItemStorageInfo]()
            if json_resp is None
            else [from_data(WorkItemStorageInfo, json_wisi) for json_wisi in json_resp]
        )

    def submit_job(self, job: Job) -> str | None:
        """
        Submits a job to OneCompute.

        Args:
            job (Job): The job to submit.

        Returns:
            str or None: The ID of the submitted job, or None if the request was unsuccessful.
        """
        json_str = self.__convert_job_to_json_str(job)
        if not json_str:
            raise Exception("Failed to submit the job.")
        resp = self.__post(WebApi.JOBS, content=json_str)
        job_id = self.__get_content(resp)
        return job_id

    async def submit_job_async(self, job: Job):
        """
        Asynchronously submits a job to OneCompute.

        Args:
            job (Job): The job to submit.

        Returns:
            IJobMonitor: A job monitor instance that track the progress of the job.
        """
        from .job_monitor import JobMonitor

        json_str = self.__convert_job_to_json_str(job)
        if not json_str:
            raise Exception("Failed to submit the job.")
        resp = await self.__post_async(WebApi.JOBS, content=json_str)
        job_id = self.__get_content(resp)
        job_monitor = JobMonitor(self)
        # Fire and forget
        asyncio.ensure_future(job_monitor.begin_monitor_job(str(job_id), None))
        return job_monitor

    def get_jobs(self) -> list[JobInfo] | None:
        """
        Gets a list of job information for the current user.

        Returns:
            list [JobInfo] or None: A list of JobInfo objects representing the user's jobs, or
            None if the request was unsuccessful.
        """
        json_resp = self.__get(WebApi.JOBS)
        return (
            None
            if json_resp is None
            else [from_data(JobInfo, json_ji) for json_ji in json_resp]
        )

    async def get_jobs_async(self) -> list[JobInfo] | None:
        """
        Asynchronously gets a list of job information for the current user.

        Returns:
            list [JobInfo] or None: A list of JobInfo objects representing the user's jobs, or
            None if the request was unsuccessful.
        """
        json_resp = await self.__get_async(WebApi.JOBS)
        return (
            None
            if json_resp is None
            else [from_data(JobInfo, json_ji) for json_ji in json_resp]
        )

    def cancel_job(self, job_id: str):
        """
        Cancels the specified job.

        Args:
            job_id (str): The ID of the job to delete.
        """
        resp = self.__post(WebApi.JOBS_CANCEL.format(job_id=job_id))
        if resp.status_code != HTTPStatus.OK:
            raise Exception(
                f"Could not cancel job. HTTP status code is {resp.status_code}"
            )

    async def cancel_job_async(self, job_id: str):
        """
        Asynchronously cancels the specified job.

        Args:
            job_id (str): The ID of the job to delete.
        """
        resp = await self.__post_async(WebApi.JOBS_CANCEL.format(job_id=job_id))
        if resp.status_code != HTTPStatus.OK:
            raise Exception(
                f"Could not cancel job. HTTP status code is {resp.status_code}"
            )

    def delete_job(self, job_id: str):
        """
        Deletes the specified job.

        Args:
            job_id (str): The ID of the job to delete.
        """
        resp = self.__post(WebApi.JOBS_DELETE.format(job_id=job_id))
        if resp.status_code != HTTPStatus.OK:
            raise Exception(
                f"Could not delete job. HTTP status code is {resp.status_code}"
            )

    async def delete_job_async(self, job_id: str):
        """
        Asynchronously deletes the specified job.

        Args:
            job_id (str): The ID of the job to delete.
        """
        resp = await self.__post_async(WebApi.JOBS_DELETE.format(job_id=job_id))
        if resp.status_code != HTTPStatus.OK:
            raise Exception(
                f"Could not delete job. HTTP status code is {resp.status_code}"
            )

    def __convert_job_to_json_str(self, job: Job) -> str:
        containers = self.get_containers()
        if containers is None:
            return ""
        container_uri = self.get_container_uri(containers[0], 1)
        job.properties |= {"ContainerUri": container_uri}
        job_json_str = json.dumps(job, default=lambda o: o.encode(), indent=4)
        return job_json_str

    def __get(self, web_api: str, json_content: bool = True) -> Any:
        with RetryClient(**self._http_config) as client:
            resp = client.get(web_api)
            json_resp = self.__get_content(resp, json_content=json_content)
            return json_resp

    async def __get_async(self, web_api: str, json_content: bool = True) -> Any:
        async with AsyncRetryClient(**self._http_config) as client:
            resp = await client.get(web_api)
            json_resp = self.__get_content(resp, json_content=json_content)
            return json_resp

    def __post(
        self,
        web_api: str,
        content: Optional[str] = None,
        data: Optional[Any] = None,
    ) -> httpx.Response:
        with RetryClient(**self._http_config) as client:
            resp = client.post(
                web_api, content=content, json=data, headers=self.__http_req_headers()
            )
            return resp

    async def __post_async(
        self,
        web_api: str,
        content: Optional[str] = None,
        data: Optional[Any] = None,
    ) -> httpx.Response:
        async with AsyncRetryClient(**self._http_config) as client:
            resp = await client.post(
                web_api, content=content, json=data, headers=self.__http_req_headers()
            )
            return resp

    @staticmethod
    def __http_req_headers():
        return {"Content-Type": "application/json", "accept": "application/json"}

    @staticmethod
    def __get_content(
        resp: httpx.Response, json_content: bool = True, err_msg: str = ""
    ) -> Any:
        if resp.status_code == HTTPStatus.OK:
            return resp.json() if json_content else resp.text
        if resp.status_code in (HTTPStatus.UNAUTHORIZED, HTTPStatus.FORBIDDEN):
            json_msg = OneComputeClient.__get_json(resp)
            error_msg = json_msg.get("message") if json_msg else ""
            error_msg = (
                error_msg
                if error_msg
                else "User does not have access to the OneCompute platform or its applications"
            )
            raise Exception(error_msg)
        if resp.status_code == HTTPStatus.NOT_FOUND:
            return None
        if resp.is_error and err_msg:
            raise Exception(f"{err_msg}. HTTP status code is {resp.status_code}")
        resp.raise_for_status()
        return ""

    @staticmethod
    def __get_json(resp: httpx.Response) -> Any:
        try:
            return resp.json()
        except ValueError:
            return {}
