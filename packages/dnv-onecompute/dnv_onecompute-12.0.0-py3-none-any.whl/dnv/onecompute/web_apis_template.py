"""
Defines the WebAPIsTemplate class, a frozen dataclass containing immutable constants for web
API endpoints.
"""

# pylint: disable=invalid-name

from dataclasses import dataclass


@dataclass(frozen=True)
class WebAPIsTemplate:
    """
    A class containing constants for commonly used web API endpoints.
    As this class is frozen, these values are immutable and behave as constants.
    """

    JOBS: str = "/api/v1/jobs"
    """
    The endpoint for jobs.
    """

    JOBS_INFO: str = "/api/v1/jobs/{job_id}"
    """
    The endpoint for retrieving job information.
    """

    JOBS_CANCEL: str = "/api/v1/jobs/{job_id}/cancel"
    """
    The endpoint for cancelling jobs.
    """

    JOBS_DELETE: str = "/api/v1/jobs/{job_id}/delete"
    """
    The endpoint for deleting jobs.
    """

    WORK_ITEMS: str = "/api/v1/jobs/{job_id}/workitems"
    """
    The endpoint for retrieving work items for a job.
    """

    WORK_ITEM_PROPERTIES_FOR_JOB: str = "/api/v1/jobs/{job_id}/workitemproperties"
    """
    The endpoint for retrieving work item properties for a job.
    """

    WORK_ITEM_PROPERTIES: str = "/api/v1/jobs/{job_id}/workitemproperties/{workitem_id}"
    """
    The endpoint for retrieving properties of a specific work item.
    """

    WORK_ITEM_RESULTS: str = "/api/v1/jobs/{job_id}/workitemresults"
    """
    The endpoint for retrieving work item results for a job.
    """

    WORK_ITEM_RESULT: str = "/api/v1/jobs/{job_id}/workitemresults/{workitem_id}"
    """
    The endpoint for retrieving the result of a specific work item.
    """

    WORK_ITEM_STORAGE_INFO: str = "/api/v1/jobs/job/{job_id}/container/{container_name}"
    """
    The endpoint for retrieving storage information for a work item.
    """

    WORK_ITEM_STORAGE_CONTAINER_URI: str = (
        "/api/v1/jobs/{job_id}/{workitem_id}/{container_name}"
    )
    """
    The endpoint for retrieving the storage container URI for a work item.
    """

    BLOBS: str = "/api/v1/blobs/{container_name}"
    """
    The endpoint for retrieving blobs in a container.
    """

    CONTAINERS: str = "/api/v1/containers"
    """
    The endpoint for retrieving containers.
    """

    CONTAINER_URI: str = "/api/v1/containers/{container_name}/{days}"
    """
    The endpoint for retrieving a container URI.
    """

    @staticmethod
    def work_item_properties(job_id: str, workitem_id: str) -> str:
        """
        Returns the API endpoint for retrieving properties of a work item.

        If workitem_id is provided and not empty, the endpoint for the specified
        work item is returned. Otherwise, the endpoint for retrieving properties
        of all work items in the specified job is returned.

        Args:
            job_id (str): The ID of the job containing the work item(s).
            workitem_id (str): The ID of the work item to retrieve properties for,
                or an empty string to retrieve properties for all work items in the job.

        Returns:
            str: The API endpoint for retrieving work item properties.
        """
        return (
            WebAPIsTemplate.WORK_ITEM_PROPERTIES.format(
                job_id=job_id, workitem_id=workitem_id
            )
            if workitem_id and workitem_id.strip()
            else WebAPIsTemplate.WORK_ITEM_PROPERTIES_FOR_JOB.format(job_id=job_id)
        )
