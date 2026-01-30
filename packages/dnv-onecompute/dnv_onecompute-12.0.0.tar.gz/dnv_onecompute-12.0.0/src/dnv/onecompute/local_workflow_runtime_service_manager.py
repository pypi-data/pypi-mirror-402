"""Manages the local workflow runtime service for executing workflows."""

import atexit
import os
import platform
import shutil
import socket
import tempfile
import threading
import time
from dataclasses import dataclass
from subprocess import CREATE_NEW_CONSOLE, CREATE_NO_WINDOW, PIPE, Popen, TimeoutExpired
from typing import Optional
from urllib.parse import urlparse

import psutil

from .enums import AutoDeployOption, LogLevel


class ProcessNotRunningException(Exception):
    """
    Exception raised when a specified process is not running, and it was expected to be running.

    Attributes:
        process_name (str): The name of the process that is not running.

    Message:
        "The process '{process_name}' is not running."
    """

    def __init__(self, process_name):
        self.process_name = process_name
        super().__init__(f"The process '{process_name}' is not running.")


class MaxPortTestingAttemptsReached(Exception):
    """
    Exception raised when the maximum number of attempts to test a port is reached, and the port is
    still not ready.

    Attributes:
        max_attempts (int): The maximum number of testing attempts that were made.

    Message:
        "Maximum port testing attempts ({max_attempts}) reached."
    """

    def __init__(self, max_attempts):
        self.max_attempts = max_attempts
        super().__init__(f"Maximum port testing attempts ({max_attempts}) reached.")


@dataclass
class LocalWorkflowRuntimeServiceManager:
    """
    Manages the local workflow runtime service for executing workflows.

    This class is responsible for managing the configuration and execution of a local workflow
    runtime service, which can execute workflows within a specified workspace. It allows control
    over various runtime options, including logging level, debugging, and deployment options.
    """

    workspace_id: str
    """
    Gets or sets the identifier for the workspace where workflows will be executed.
    """

    worker_host_apps_path: str
    """
    Gets or sets the path to the worker host applications path.
    """

    workflow_runtime_executable_path: str
    """
    Gets or sets the path to the workflow runtime executable.
    """

    workflow_runtime_service_endpoint: Optional[str] = ""
    """
    Gets or sets the endpoint URL for the workflow runtime service.

    If not explicitly specified, the default value is set to 'http://localhost:{port}', where
    '{port}' represents an available and unoccupied port number. This default configuration ensures
    that the workflow runtime service is accessible locally on an automatically assigned port.
    """

    workflow_runtime_log_level: LogLevel = LogLevel.NONE
    """The log level for the workflow runtime service. Default is LogLevel.NONE."""

    workflow_runtime_log_filename: Optional[str] = None
    """
    Gets or sets the name of the log file.

    If provided, logs will be saved to this file. If not specified (set to 'None'), a default file
    named "WC.LOG" will be created in the working directory of the LocalWorkflowRuntime Service
    started with. This option can also be an absolute path to the file, in which case it will be
    saved at the desired location.
    """

    workflow_debugging: bool = False
    """
    Gets or sets whether to enable debugging for workflows.

    Default is False.
    """

    auto_deploy_option: AutoDeployOption = AutoDeployOption.RELEASE
    """
    Gets or sets the auto-deployment option for workflows.

    Default is AutoDeployOption.RELEASE.
    """

    max_concurrent_workers: Optional[int] = None
    """
    Gets or sets the maximum number of concurrent workers.

    Default is None.
    """

    blob_storage_path: Optional[str] = ""
    """
    Gets or sets the optional path where blob data is stored.

    If not specified, the default path on Windows is under the '%TEMP%' directory
    ('$userprofile\\AppData\\Local\\Temp'). The folder is named with a prefix of 'oc_' followed by a
    unique identifier and suffixed with '_blob'. The specified blob storage path must be a valid and
    writable directory on the filesystem, accessible by the user running the workflow runtime.
    """

    jobs_root_path: Optional[str] = ""
    """
    Gets or sets the optional path where the root directory for jobs is set up.

    If not specified, the default path on Windows is located within the '%TEMP%' directory
    ('$userprofile\\AppData\\Local\\Temp'). This default folder is named with a prefix of 'oc_',
    followed by a unique identifier, and suffixed with '_jobs'. The provided 'jobs_root_path' must
    be a valid and writable directory on the filesystem, accessible by the user running the
    workflow runtime.
    """

    temp_folder_path: Optional[str] = None
    """
    Gets or sets the path for storing temporary files.

    If not specified, a system-dependent default directory is used.
    On Windows, it's typically within '%TEMP%' ('$userprofile\\AppData\\Local\\Temp').
    On Unix-based systems, it's often within '/tmp'.
    """

    startup_wait_time: int = 5
    """
    Gets or sets the startup wait time in seconds.

    Default is 5 seconds.
    """

    console_window_visible: bool = False
    """
    Gets or sets a boolean flag indicating whether the LocalWorkflowRuntime service should run with
    or without a visible console window. 

    Defaults to False, indicating that the console window is not visible.
    """

    redirect_console_logs_to_terminal: bool = True
    """
    Gets or sets a flag indicating whether to redirect console logs to the terminal.

    Default is True.
    """

    clean_temporary_directories_on_exit: bool = True
    """
    Gets or sets a flag indicating whether to clean up the local temporary directories on exit.
    
    Default to True.
    """

    _job_working_directory: str = ""
    """
    Gets or sets the working directory formed by combining 'jobs_root_path' and 'workspace-id'.
    This directory is used for managing job-specific files and resources within the context of
    a workspace. It is created by combining the 'jobs_root_path' with the unique 'workspace-id'.
    """

    _proc: Optional[Popen] = None
    """
    Gets or sets an optional attribute that holds a reference to the 'subprocess.Popen' object.
    This object represents a child process. It will be None if the child process is not currently
    running.
    """

    def __post_init__(self):
        """
        Initializes an instance of this class.
        """

        # The temporary path is a flexible setting that designates the location of the temporary
        # folder.When not specified, the Python SDK on Windows automatically selects the %TEMP%
        # directory (%userprofile%\AppData\Local\Temp).
        # This option is provided to address a potential problem that can arise when the combination
        # of the temporary path based on the user profile and the temporary sub-folder for jobs
        # results in a path length that exceeds the MAX_PATH limit of 260 characters.
        # This can cause difficulties for applications that are not equipped to handle long paths.
        # By specifying a shorter temporary path, this configuration can help resolve issues related
        # to lengthy paths, such as difficulty accessing, reading, or copying files.
        if self.temp_folder_path:
            if not os.path.isdir(self.temp_folder_path):
                os.makedirs(self.temp_folder_path, True)

        folder_prefix = "oc_"

        if not (
            self.workflow_runtime_service_endpoint
            and self.workflow_runtime_service_endpoint.strip()
        ):
            port = self._get_free_random_port()
            self.workflow_runtime_service_endpoint = f"http://localhost:{port}"

        # Local Blob Storage Directory
        if not (self.blob_storage_path and self.blob_storage_path.strip()):
            self.blob_storage_path = tempfile.mkdtemp(
                prefix=folder_prefix, suffix="_blob", dir=self.temp_folder_path
            )
            print(f"The temporary blob storage directory is: {self.blob_storage_path}")

        # Jobs Root Directory
        if not (self.jobs_root_path and self.jobs_root_path.strip()):
            self.jobs_root_path = tempfile.mkdtemp(
                prefix=folder_prefix, suffix="_jobs", dir=self.temp_folder_path
            )
            print(f"The temporary jobs root directory is: {self.jobs_root_path}")

        # A Job Working Directory
        self._job_working_directory = os.path.join(
            self.jobs_root_path, self.workspace_id
        )
        os.makedirs(self._job_working_directory, exist_ok=True)

        atexit.register(self.stop_service)

    def get_job_working_path(self) -> Optional[str]:
        """
        Get the working directory path of job.

        Returns:
            Optional[str]: The job's working directory path if specified or predefined,
            otherwise None.
        """
        return self._job_working_directory

    def get_blob_storage_path(self) -> Optional[str]:
        """
        Get the path for storing blob data.

        Returns:
            Optional[str]: The path for storing blob data if specified or predefined,
            otherwise None.
        """
        return self.blob_storage_path

    def start_service(self):
        """
        Start the local workflow runtime service.

        This method starts the local workflow runtime service as a subprocess, based on the
        configured parameters and options.

        Returns:
            None
        """
        self._start_service()

    def stop_service(self):
        """
        Stop the local workflow runtime service.

        This method stops the local workflow runtime service subprocess.

        Returns:
            None
        """
        self._stop_service()

        # Remove the temporary folders
        if self.clean_temporary_directories_on_exit:
            self._remove_directory(self.jobs_root_path, "jobs root directory")
            self._remove_directory(self.blob_storage_path, "BLOB storage directory")

    def _start_service(self):
        plt = platform.system()
        url = self.workflow_runtime_service_endpoint
        service_exe_path = self.workflow_runtime_executable_path
        apps_directory = self.worker_host_apps_path
        local_blob_storage_directory = self.blob_storage_path

        port = urlparse(url).port
        assert port is not None, "The port is not specified in the URL."

        hostname = urlparse(url).hostname
        assert hostname is not None, "The hostname is not specified in the URL."

        env = dict(os.environ, OC_LOCAL_EXECUTION="true")

        # The environment variable Logging__Console__LogLevel__Default sets the console log level
        # for the local worker host. It should be set to one of the following values: "Trace",
        # "Debug", "Information", "Warning", "Error", or "Critical".
        #
        # Changing this variable will affect the level of detail printed to the console.
        #
        # Note that the log levels for "System" and "Microsoft" are also affected by this variable,
        # since they inherit their log levels from the default log level.
        env = dict(
            env,
            Logging__Console__LogLevel__Default=str(self.workflow_runtime_log_level),
        )

        service_args = [
            service_exe_path,
            "openapi",
            "--url",
            url,
            "--working-directory",
            local_blob_storage_directory,
            "--rest-port",
            str(port),
            "--application-directory",
            apps_directory,
            "--isolate-workunits",
        ]

        if self.max_concurrent_workers is not None and self.max_concurrent_workers != 0:
            service_args.extend(
                ["--concurrency-limit", str(self.max_concurrent_workers)]
            )

        if self.auto_deploy_option != AutoDeployOption.NONE:
            release_type = str(self.auto_deploy_option)
            service_args.extend(["--auto-deploy", release_type])

        if (
            self.workflow_runtime_log_filename
            and self.workflow_runtime_log_filename.strip()
        ):
            service_args.extend(["--log-file", self.workflow_runtime_log_filename])

        if self.workflow_debugging:
            service_args.append("--debug-worker")

        process_creation_flags = (
            CREATE_NEW_CONSOLE if self.console_window_visible else CREATE_NO_WINDOW
        )

        # Set the working directory of the Local Workflow Runtime to match the job's working
        # directory. This ensures that the Local Workflow Runtime consistently operates within
        # the correct directory. Without this adjustment, the working directory defaulted to the
        # BLOB directory, potentially causing issues with workflows and violating the assumption
        # that the job and BLOB directories are separate locations.
        if plt == "Windows":
            stdout = stderr = PIPE if self.redirect_console_logs_to_terminal else None

            self._proc = Popen(
                service_args,
                cwd=self._job_working_directory,  # See the comment above
                env=env,
                stdout=stdout,
                stderr=stderr,
                close_fds=True,
                creationflags=process_creation_flags,
                bufsize=0,  # Set the bufsize to 0 to disable buffering
            )

            # This code monitors the status of the 'LocalWorkflowRuntime' service to ensure it is
            # started and running, ready to accept requests. A workaround is implemented because
            # the service does not currently provide a notification to the client indicating its
            # readiness to receive requests.
            # The workaround involves periodically checking if the service's port is open for
            # listening and if the process associated with the service is running, effectively
            # simulating the missing notification mechanism.
            self._wait_for_process_ready(
                self._proc,
                hostname,
                port,
                delay=self.startup_wait_time,
            )
            print(
                f"Info: The LocalWorkflowRuntime service (PID '{self._proc.pid}') is ready."
            )

            if self.redirect_console_logs_to_terminal:
                # Setting the 'daemon' flag to True makes sure that the threads terminate when the
                # main program ends, preventing any potential hanging threads.
                thread_stdout = threading.Thread(
                    target=LocalWorkflowRuntimeServiceManager._display_output,
                    args=(self._proc.stdout,),
                    daemon=True,
                )
                thread_stderr = threading.Thread(
                    target=LocalWorkflowRuntimeServiceManager._display_output,
                    args=(self._proc.stderr,),
                    daemon=True,
                )
                thread_stdout.start()
                thread_stderr.start()

        elif plt == "Linux":
            pass
        elif plt == "Darwin":
            pass
        else:
            print("Unidentified system")

    def _stop_service(self):
        if not self._proc:
            return
        try:
            self._proc.terminate()
            self._proc.wait(timeout=10)
        except TimeoutExpired:
            pass

    @staticmethod
    def _display_output(stream):
        for line in iter(stream.readline, b""):
            # Decode the byte-like object into a string
            line = line.decode("utf-8")
            print(line.rstrip(), flush=True)

    @staticmethod
    def _wait_for_process_ready(
        proc: Popen,
        host: str,
        port: int,
        max_attempts: int = 10,
        delay: int = 2,
    ):
        # Extract the name of the executable from the arguments
        args = proc.args  # type: list[str]
        executable_name = os.path.basename(str(args[0]))

        # Try to connect to the process for a specified number of attempts
        for attempt in range(1, max_attempts + 1):
            # Check if the process is not running
            if not LocalWorkflowRuntimeServiceManager._is_process_running(proc):
                raise ProcessNotRunningException(executable_name)

            # Return if the port is open, indicating the service is ready and no further checks
            # are needed.
            if LocalWorkflowRuntimeServiceManager._is_port_open(host, port):
                return

            print(
                f"Info: Attempt {attempt}/{max_attempts}."
                f"LocalWorkflowRuntime service (PID '{proc.pid}') is not ready yet. "
                f"Retrying in {delay} seconds."
            )

            time.sleep(delay)

        # If the maximum number of attempts has been reached and the port is still not open,
        # raise Exception
        raise MaxPortTestingAttemptsReached(max_attempts)

    @staticmethod
    def _is_port_open(host, port) -> bool:
        try:
            # Create a socket object and attempt to connect to the specified host and port
            with socket.socket(socket.AF_INET, socket.SOCK_STREAM) as soc:
                soc.settimeout(1)  # Adjust the timeout as needed
                soc.connect((host, port))
            return True
        except (ConnectionRefusedError, socket.timeout):
            return False

    @staticmethod
    def _is_process_running(proc: Popen) -> bool:
        return proc.poll() is None

    @staticmethod
    def _get_free_random_port() -> int:
        with socket.socket() as soc:
            soc.bind(("", 0))
            return soc.getsockname()[1]

    @staticmethod
    def _find_pids_by_name(name: str) -> list[int]:
        pids = []
        for proc in psutil.process_iter(["pid", "name"]):
            if proc.info["name"] == name:  # type: ignore
                pids.append(proc.info["pid"])  # type: ignore
        return pids

    @staticmethod
    def _remove_directory(path, description):
        try:
            if path and os.path.exists(path):
                print(f"Removing the temporary {description}: {path}")
                shutil.rmtree(path)
        except Exception as ex:
            print(ex)
