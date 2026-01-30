# OneCompute

Python package for integration with the OneCompute cloud platform. Streamline job management, workflows, and file operations over REST APIs. Monitor job progress and efficiently handle file uploads and downloads.

Empower your Python workflows with seamless integration using our advanced OneCompute cloud platform package. Effortlessly manage complex jobs, streamline workflows, and facilitate efficient file operations through our user-friendly REST APIs. Process workflows both locally and on the cloud to optimize performance and resource utilization. Stay on top of job progress with real-time monitoring capabilities and experience hassle-free handling of file uploads and downloads for a truly streamlined cloud computing experience.

# Usage

## Introduction

This project demonstrates how to run a workflow locally using the OneCompute platform. The provided code snippet utilizes the `dnv-oneworkflow` Python package to interact with the OneCompute platform and execute a simple workflow locally. The example showcases the setup of the local workflow runtime service and the submission of a job for execution.

## Prerequisites

Make sure you have the following prerequisites installed:

- Python 3.10.x or higher
- Pip (Python package manager)
- [dnv-oneworkflow](https://test.pypi.org/project/dnv-oneworkflow/) Python package for the `PythonCommand` module.

  Use the following command to install the `dnv.oneworkflow` package:

  ```bash
  pip install dnv.oneworkflow
  ```

- Install the LocalWorkflowRuntimeService using the following command within your Python environment:
  ```python
  await PackageManager().install_package_async(
      "LocalWorkflowRuntime", "win-x64", PackageManager.Repository.DEV
  )
  ```

## Code

```python
import asyncio
import os

from dnv.onecompute import (
    AutoDeployOption,
    Job,
    LocalWorkflowRuntimeServiceManager,
    OneComputeClient,
    WorkUnit,
)
from dnv.oneworkflow.python_command import PythonCommand


async def run_workflow_locally_async():
    """
    Run a workflow locally using the OneCompute platform.
    """
    # Define constants
    OC_APPS_PATH = os.path.join(os.environ["LOCALAPPDATA"], "OneCompute")
    RUNTIME_SERVICE_PATH = os.path.join(OC_APPS_PATH, "LocalWorkflowRuntime", "wc.exe")
    WORKSPACE_ID = "MyWorkspace"
    SERVICE_NAME = "OneWorkflowWorkerHost"

    # Configure the local workflow runtime service
    workflow_runtime_service = LocalWorkflowRuntimeServiceManager(
        workspace_id=WORKSPACE_ID,
        worker_host_apps_path=OC_APPS_PATH,
        workflow_runtime_executable_path=RUNTIME_SERVICE_PATH,
        console_window_visible=True,
        auto_deploy_option=AutoDeployOption.DEV,
        startup_wait_time=10,
    )

    # Set up the OneCompute client
    url = workflow_runtime_service.workflow_runtime_service_endpoint
    oc_client = OneComputeClient(base_url=url, authenticator=None)

    # Start the local workflow runtime service
    workflow_runtime_service.start_service()

    # Define the Python command for the work unit
    py_cmd = PythonCommand(inline_script="print('Hello OneCompute')")
    work_unit = WorkUnit(py_cmd)
    work_unit.command = SERVICE_NAME

    # Define the job with necessary configurations
    job = Job()
    job.work = work_unit
    job.service_name = SERVICE_NAME
    job.properties = {"OW_WorkspaceId": WORKSPACE_ID}

    # Submit the job and await its termination
    job_monitor = await oc_client.submit_job_async(job)
    await job_monitor.await_job_termination_async()

    # Stop the local workflow runtime service
    workflow_runtime_service.stop_service()


if __name__ == "__main__":
    # Run the main asynchronous function
    asyncio.run(run_workflow_locally_async())
```

## License

[MIT](https://choosealicense.com/licenses/mit/)

## Support

If you encounter any issues, have questions, or want to provide feedback, please get in touch with our support team at software.support@dnv.com. We are committed to continuously improving OneCompute and providing timely assistance to our users.
