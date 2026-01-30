"""This module various classes that define the flow model for the One Compute platform."""

# pylint: disable=invalid-name

from __future__ import annotations

import uuid
from abc import ABC, abstractmethod
from dataclasses import dataclass, field
from enum import Enum, unique
from typing import Any, Optional, Union


@unique
class TaskRoles(int, Enum):
    """
    Enumerates various task roles for the work units.
    """

    Normal = 0
    """Indicates that the work unit performs a normal task."""

    ReductionTask = 1
    """Indicates that the work unit performs a reduction task."""

    JobPreparationTask = 2
    """Indicates that the work unit is responsible for job preparation."""

    JobReleaseTask = 3
    """Indicates that the work unit is responsible for job release."""

    JobControllerTask = 4
    """Indicates that the work unit acts as a job controller task."""


@unique
class FailureStrategy(int, Enum):
    """
    An enumeration of failure strategies for a process.
    """

    FailOnError = 1
    """ A strategy where the work unit will fail immediately on encountering an error."""

    ContinueOnError = 2
    """A strategy where the work unit will continue despite encountering errors."""


class Encode(ABC):
    """
    Abstract Base Class for encoding objects.

    This class provides a blueprint for encoding objects into dictionaries.
    Concrete subclasses are expected to implement the `encode` method.
    """

    @abstractmethod
    def encode(self) -> dict[str, Any]:
        """
        Encode an object into a dictionary.

        This method must be implemented by concrete subclasses.

        Returns:
            A dictionary representation of the object.
        """


class TypeMeta(Encode):
    """
    Class for encoding objects with type information.

    This class extends the `Encode` abstract base class and adds type information to the encoded
    dictionary. Concrete subclasses are expected to implement the `type` property.
    """

    def __init__(self):
        """
        Initializes the object and adds type information to the encoded dictionary.
        """
        if self.type.strip():
            self.__dict__["$type"] = self.type

    def __str__(self) -> str:
        """
        Returns the string representation of the encoded dictionary.

        Returns:
            A string representation of the encoded dictionary.
        """
        return str(self.encode())

    def encode(self) -> dict[str, Any]:
        """
        Encodes an object into a dictionary and filters properties that are 'None'.

        Returns:
            A dictionary representation of the object without properties that are 'None'.
        """
        filtered: dict[str, Any] = {
            k: v for k, v in self.__dict__.items() if v is not None and not k[0] == "_"
        }
        return filtered

    @property
    @abstractmethod
    def type(self) -> str:
        """
        Abstract property to retrieve the type of the object.

        Returns:
            The type of the object as a string.
        """


class SchedulingOptions(TypeMeta):
    """
    A data class representing scheduling options for a process.
    """

    def __init__(
        self,
        failure_strategy: FailureStrategy = FailureStrategy.FailOnError,
        max_task_retry_count: int = 0,
        work_unit_batch_size: int = 1,
    ):
        """
        Initializes a new instance of the SchedulingOptions class.

        Args:
            max_task_retry_count (int): The maximum number of times to retry a failed task.
                It controls the number of retries for the task executable due to a nonzero exit
                code. The Batch service will try the task once, and may then retry up to this
                limit. For example, if the maximum retry count is 3, Batch tries the task up to
                4 times (one initial try and 3 retries). If the maximum retry count is 0, the Batch
                service does not retry the task after the first attempt. If the maximum retry count
                is -1, the Batch service retries the task without limit. Resource files and
                application packages are only downloaded again if the task is retried on a new
                compute node.
            failure_strategy (FailureStrategy): The strategy to use when encountering failures.
            work_unit_batch_size (int): It is the proposed number of work units that each worker
                will be assigned. Default is 1.
        """
        super().__init__()
        self.FailureStrategy: FailureStrategy = failure_strategy
        self.MaxTaskRetryCount: int = max_task_retry_count
        self.WorkUnitBatchSize: int = work_unit_batch_size

    @property
    def type(self) -> str:
        return (
            "DNV.One.Compute.Core.FlowModel.SchedulingOptions, DNV.One.Compute.Core"
        )


@dataclass
class FileSelectionOptions:
    """A class for selecting and filtering files within a folder."""

    directory: str
    """A string representing the directory where files will be searched."""

    include_files: list[str] = field(default_factory=lambda: ["**/*.*"])
    """
    A list of strings representing file patterns to include in the search. Defaults to ["**/*.*"].
    """

    exclude_files: list[str] = field(default_factory=lambda: [])
    """
    A list of strings representing file patterns to exclude fromthe search. Defaults to [].
    """


class DataContainer(TypeMeta):
    """General purpose serializable data container."""

    def __init__(self, data: object = None):
        """
        Initialize a new instance of DataContainer.

        Args:
            data (object, optional): The initial data to store in the container. Defaults to None.
        """
        super().__init__()
        self.Version = 1
        self.Content = data

    @property
    def type(self) -> str:
        """
        Gets the type of the DataContainer. This property is intended to be overridden in subclasses
        to return the specific type of data contained.
        """
        return ""

    @property
    def content(self) -> object:
        """
        Gets or sets the content of the DataContainer.
        """
        return self.Content

    @content.setter
    def content(self, value: object):
        self.Content = value

    @property
    def version(self) -> int:
        """
        Gets or sets the version of the DataContainer.
        """
        return self.Version

    @version.setter
    def version(self, value: int):
        self.Version = value


class StorageSpecification(TypeMeta):
    """
    A base class that defines the storage specification.
    """

    def __init__(self, directory: str = ""):
        """
        Initializes StorageSpecification with a directory.

        Args:
            directory (str, optional): The directory of the StorageSpecification.
                Defaults to an empty string.
        """
        super().__init__()
        self.Directory = directory

    @property
    def directory(self) -> str:
        """
        Gets or sets directory of the StorageSpecification..
        """
        return self.Directory

    @directory.setter
    def directory(self, value: str):
        self.Directory = value


class BlobDirectorySpecification(StorageSpecification):
    """Specifies a directory within a BLOB container."""

    def __init__(self, container_url: str = "", directory: str = ""):
        """
        Initializes a BlobDirectorySpecification instance.

        Args:
            container_url (str, optional): The URL of the container for the
                BlobDirectorySpecification.Defaults to an empty string.
            directory (str, optional): The directory of the BlobDirectorySpecification.
                Defaults to an empty string.
        """
        super().__init__(directory=directory)
        self.ContainerUrl = container_url

    @property
    def type(self) -> str:
        """
        Retrieves the fully qualified type name of the BlobDirectorySpecification.
        """
        return "DNV.One.Compute.Core.FlowModel.DataTransfer.BlobDirectorySpecification, DNV.One.Compute.Core"

    @property
    def container_url(self) -> str:
        """
        Gets or sets the BLOB container URL.
        """
        return self.ContainerUrl

    @container_url.setter
    def container_url(self, value: str):
        self.ContainerUrl = value


class FileSystemDirectorySpecification(StorageSpecification):
    """
    A class that defines the file system directory specification.
    """

    def __init__(self, directory: str = ""):
        """
        Initializes FileSystemDirectorySpecification with a directory.

        Args:
            directory (str, optional): The directory of the FileSystemDirectorySpecification.
                Defaults to an empty string.
        """
        super().__init__(directory=directory)

    @property
    def type(self) -> str:
        """
        Retrieves the fully qualified type name of the FileSystemDirectorySpecification.
        """
        return "DNV.One.Compute.Core.FlowModel.DataTransfer.FileSystemDirectorySpecification, DNV.One.Compute.Core"


class ResultLakeStorageSpecification(StorageSpecification):
    """
    A class that represents the specifications for a Result Lake storage.
    """

    @property
    def type(self) -> str:
        """
        Retrieves the fully qualified type name of the ResultLakeStorageSpecification.
        """
        return "DNV.One.Compute.Core.FlowModel.DataTransfer.ResultLakeStorageSpecification, DNV.One.Compute.Core"


class FileTransferSpecification(TypeMeta):
    """
    A class that specifies files to be transferred between two different storage specifications.
    """

    def __init__(
        self,
        source_specification: Optional[StorageSpecification] = None,
        destination_specification: Optional[StorageSpecification] = None,
        selected_files: Optional[list[str]] = None,
        excluded_files: Optional[list[str]] = None,
    ):
        """
        Initializes a FileTransferSpecification with source and destination specifications, and
        lists of selected and excluded files.

        Args:
            source_specification (Optional[StorageSpecification]): The source storage specification.
                Defaults to None.
            destination_specification (Optional[StorageSpecification]): The destination storage
                specification.Defaults to None.
            selected_files (Optional[list[str]]): The list of selected files.
                Defaults to an empty list.
            excluded_files (Optional[list[str]]): The list of excluded files.
                Defaults to an empty list.
        """
        super().__init__()
        self.SourceSpecification = source_specification
        self.DestinationSpecification = destination_specification
        self.SelectedFiles = selected_files or []
        self.ExcludedFiles = excluded_files or []

    @property
    def type(self) -> str:
        """
        Retrieves the fully qualified type name of the FileTransferSpecification.
        """
        return "DNV.One.Compute.Core.FlowModel.DataTransfer.FileTransferSpecification, DNV.One.Compute.Core"

    @property
    def source_specification(self) -> Union[StorageSpecification, None]:
        """
        Gets or sets the source specification.
        """
        return self.SourceSpecification

    @source_specification.setter
    def source_specification(self, value: Optional[StorageSpecification]):
        self.SourceSpecification = value

    @property
    def destination_specification(self) -> Union[StorageSpecification, None]:
        """
        Gets or sets the destination specification.
        """
        return self.DestinationSpecification

    @destination_specification.setter
    def destination_specification(self, value: Optional[StorageSpecification]):
        self.DestinationSpecification = value

    @property
    def selected_files(self) -> list[str]:
        """
        Gets or sets the relative paths of files chosen for data transfer. These paths should be
        relative to the source specification. File patterns, such as **/*.txt, can be used to match
        any .txt file in any subdirectory from the root. This property supports the Glob standard
        (https://en.wikipedia.org/wiki/Glob_(programming)).
        """
        return self.SelectedFiles

    @selected_files.setter
    def selected_files(self, value: list[str]):
        self.SelectedFiles = value

    @property
    def excluded_files(self) -> list[str]:
        """
        Gets or sets the relative paths to files that should be excluded from data transfer. Paths
        must be relative to the source specification. File patterns can be used, e.g. **/*.txt to
        match any .txt file in any subdirectory of the root. The Glob standard
        (https://en.wikipedia.org/wiki/Glob_(programming)) is supported.
        """
        return self.ExcludedFiles

    @excluded_files.setter
    def excluded_files(self, value: list[str]):
        self.ExcludedFiles = value


class FlowModelObject(TypeMeta):
    """Base class for flow model objects."""

    def __init__(self):
        """Initializes a new instance of the FlowModelObject class."""
        super().__init__()
        self.properties: dict[str, Any] = {}

    @property
    def property_dictionary(self) -> dict[str, Any]:
        """Gets or sets the properties dictionary of the FlowModelObject."""
        return self.properties

    @property_dictionary.setter
    def property_dictionary(self, value: dict[str, Any]):
        self.properties = value

    @property
    def batch_number(self) -> int:
        """Gets or sets the batch number."""
        return self.BatchNumber

    @batch_number.setter
    def batch_number(self, value: int):
        self.BatchNumber = value


class WorkItem(FlowModelObject):
    """Defines a unit of computational work within a workflow."""

    def __init__(self, work_item_id: str = ""):
        """
        Initializes a new instance of the WorkItem class.

        Args:
            work_item_id (str, optional): The unique identifier for the work item. If not provided,
                a new UUID will be generated.
        """
        super().__init__()
        self.Tag: Optional[str] = None
        self.JobId: Optional[str] = None
        self.ParentId: Optional[str] = None
        self.id = work_item_id or str(uuid.uuid4())

    @property
    def type(self) -> str:
        """
        Gets the type of the WorkItem.

        This is an abstract property and should be overridden in subclasses to return the
        appropriate type.
        """
        return ""

    @property
    def tag(self) -> Optional[str]:
        """
        Gets or sets the tag.

        This is a client-specified tag that does not need to be unique. It is used as a recognizable
        prefix for the job identifier.
        """
        return self.Tag

    @tag.setter
    def tag(self, value: str):
        self.Tag = value

    @property
    def job_id(self) -> Optional[str]:
        """Gets or sets the job identifier."""
        return self.JobId

    @job_id.setter
    def job_id(self, value: str):
        self.JobId = value

    @property
    def parent_id(self) -> Optional[str]:
        """
        Gets or sets the parent identifier.

        Identifier of the parent WorkItem. None if this is the root of the WorkItem hierarchy.
        """
        return self.ParentId

    @parent_id.setter
    def parent_id(self, value: str):
        self.ParentId = value


class WorkUnit(WorkItem):
    """Represents a unit of work within a workflow. Inherits from the WorkItem class."""

    def __init__(
        self,
        data: object = None,
        work_unit_id: str = "",
    ):
        """
        Initializes a new instance of the WorkUnit class.

        Args:
            data (object, optional): The data associated with the work unit. Defaults to None.
            work_unit_id (str, optional): The unique identifier for the work unit. If not provided,
                a new UUID will be generated. Defaults to "".
        """
        super().__init__(work_unit_id)
        self.TaskRole = TaskRoles.Normal
        self.Data = DataContainer(data)
        self._input_file_selectors = list[FileSelectionOptions]()
        self._output_file_selectors = list[FileSelectionOptions]()

    @property
    def type(self) -> str:
        """
        Retrieves the fully qualified type name of the WorkUnit.
        """
        return "DNV.One.Compute.Core.FlowModel.WorkUnit, DNV.One.Compute.Core"

    @property
    def command(self) -> str:
        """
        Gets or sets the command-line used by the backend to process this work unit (optional).

        This is an optional property. If set, it will be transmitted directly to the backend.
        It is specific to the backend. For an Azure Batch backend, this command line should start
        with 'cmd /c' on Windows, or '/bin/sh' on Linux.
        """
        return self.Command

    @command.setter
    def command(self, value: str):
        self.Command = value

    @property
    def request(self) -> str:
        """
        Gets or sets the application request.

        This property can be used by the client application to communicate an application specific
        request to the application worker. It is not used by One Compute.
        """
        return self.Request

    @request.setter
    def request(self, value: str):
        self.Request = value

    @property
    def service_name(self) -> str:
        """
        Gets or sets the name of the service.

        In the context of OneCompute Platform, this is the name of the application. If set, this
        value will override the 'Job.ServiceName' set on the job. In general, it is recommended to
        set 'Job.ServiceName' and only set `WorkUnit.ServiceName` forwork that mustbe done by a
        different application.
        """
        return self.ServiceName

    @service_name.setter
    def service_name(self, value: str):
        self.ServiceName = value

    @property
    def dependencies(self) -> list[str]:
        """
        Gets or sets the dependencies.

        This is a list of ids of WorkUnit's that this work unit depends on.
        """
        return self.Dependencies

    @dependencies.setter
    def dependencies(self, value: list[str]):
        self.Dependencies = value

    @property
    def input_files(self) -> list[str]:
        """Gets or sets the resources."""
        return self.InputFiles

    @input_files.setter
    def input_files(self, value: list[str]):
        self.InputFiles = value

    @property
    def input_file_specifications(self) -> list[FileTransferSpecification]:
        """Gets or sets the input file specifications."""
        return self.InputFileSpecifications

    @input_file_specifications.setter
    def input_file_specifications(self, value: list[FileTransferSpecification]):
        self.InputFileSpecifications = value

    @property
    def output_file_specifications(self) -> list[FileTransferSpecification]:
        """Gets or sets the output file specifications."""
        return self.OutputFileSpecifications

    @output_file_specifications.setter
    def output_file_specifications(self, value: list[FileTransferSpecification]):
        self.OutputFileSpecifications = value

    @property
    def task_role(self) -> TaskRoles:
        """Gets or sets the task role of the work unit."""
        return self.TaskRole

    @task_role.setter
    def task_role(self, value: TaskRoles):
        self.TaskRole = value

    @property
    def worker_contract_name(self) -> str:
        """
        Gets or sets the name of the IWorker export contract.

        Optionally, a discriminator that constrains the selection of the IWorker export for
        executing this work unit. The standard empty string will just expect a single worker to
        be located within the working directory. It is valid to leave this field as null. This
        is only required if you want to support multiple named MEF IWorker's through a single
        Worker Host."""
        return self.WorkerContractName

    @worker_contract_name.setter
    def worker_contract_name(self, value: str):
        self.WorkerContractName = value

    @property
    def worker_assembly_filename(self) -> str:
        """
        Gets or sets the file name of the assembly that exposes the IWorker export contract that
        will be loaded by the worker host.

        Optionally, the specific name of the assembly to be loaded as the IWorker.
        This prevents MEF doing a sweep of the entire working directory and is useful to limit
        the scope of the MEF container. It is valid to leave this field as null. In which case
        MEF will load all assemblies in the working directory into the container.
        """
        return self.WorkerAssemblyFileName

    @worker_assembly_filename.setter
    def worker_assembly_filename(self, value: str):
        self.WorkerAssemblyFileName = value

    @property
    def data(self) -> DataContainer:
        """Gets or sets the container of input data."""
        return self.Data

    @data.setter
    def data(self, value: DataContainer):
        self.Data = value

    @property
    def input_file_selectors(self) -> list[FileSelectionOptions]:
        """
        Gets the list of input file selectors.

        These selectors are used to determine which files should be included as input files.

        Returns:
            list[FileSelectionOptions]: The list of input file selectors.
        """
        return self._input_file_selectors

    @property
    def output_file_selectors(self) -> list[FileSelectionOptions]:
        """
        Gets the list of output file selectors.

        These selectors are used to determine which files should be included as output files.

        Returns:
            list[FileSelectionOptions]: The list of output file selectors.
        """
        return self._output_file_selectors

    @property
    def working_directory(self) -> str:
        """
        Gets or sets the working directory (for the local run) of this work unit.

        The working directory can be used to specify the working directory of the worker
        when running locally. It can be a directory path relative to the current directory of
        the worker process or an absolute path.

        If the working directory already contains the necessary input files, it is recommended
        to let `WorkUnit.InputFileSpecifications` be null. Similarly, if there is no need to
        transfer output files from this directory, it is recommended to let
        'WorkUnit.OutputFileSpecifications' be null.
        """
        return self.workingDirectory

    @working_directory.setter
    def working_directory(self, value: str):
        self.workingDirectory = value

    def input_directory(
        self,
        directory: str,
        include_files: Optional[list[str]] = None,
        exclude_files: Optional[list[str]] = None,
    ) -> WorkUnit:
        """
        Adds an input directory to the work unit.

        Args:
            directory (str): The directory to add.
            include_files (list[str], optional): List of files to include.
                Defaults to all files in the directory.
            exclude_files (list[str], optional): List of files to exclude. Defaults to no files.

        Returns:
            WorkUnit: The current work unit instance.
        """
        include_files = include_files or ["**/*.*"]
        exclude_files = exclude_files or []
        self._input_file_selectors.append(
            FileSelectionOptions(directory, include_files, exclude_files)
        )
        return self

    def output_directory(
        self,
        directory: str,
        include_files: Optional[list[str]] = None,
        exclude_files: Optional[list[str]] = None,
    ) -> WorkUnit:
        """
        Adds an output directory to the work unit.

        Args:
            directory (str): The directory to add.
            include_files (list[str], optional): List of files to include.
                Defaults to all files in the directory.
            exclude_files (list[str], optional): List of files to exclude. Defaults to no files.

        Returns:
            WorkUnit: The current work unit instance.
        """
        include_files = include_files or ["**/*.*"]
        exclude_files = exclude_files or []
        self._output_file_selectors.append(
            FileSelectionOptions(directory, include_files, exclude_files)
        )
        return self


class CompositeWork(WorkItem):
    """
    CompositeWork is a class that encapsulates a collection of WorkItems. It can represent workflows
    that are either sequential or parallel in nature.
    """

    def __init__(self, parallel: bool, work_items: Optional[list[WorkItem]] = None):
        """
        Initializes a new instance of the CompositeWork class.

        Args:
            parallel (bool): A flag indicating whether the work items should be processed
                in parallel.
            work_items (list[WorkItem], optional): A list of work items to be processed.
                Defaults to an empty list if not provided.
        """
        super().__init__()
        self.Parallel = parallel
        self.WorkItems = work_items or []

    @property
    def type(self) -> str:
        """
        Retrieves the fully qualified type name of the CompositeWork.
        """
        return "DNV.One.Compute.Core.FlowModel.CompositeWork, DNV.One.Compute.Core"

    @property
    def parallel(self) -> bool:
        """
        Gets a value indicating whether this instance of CompositeWork can be executed in parallel.
        """
        return self.Parallel

    @parallel.setter
    def parallel(self, value: bool):
        self.Parallel = value

    @property
    def work_items(self) -> list[WorkItem]:
        """Gets or sets the compute tasks of this group."""
        return self.WorkItems

    @work_items.setter
    def work_items(self, value: list[WorkItem]):
        self.WorkItems = value


class ParallelWork(CompositeWork):
    """Models parallel work."""

    def __init__(self, work_items: Optional[list[WorkItem] | list[WorkUnit]] = None):
        """
        Initializes a new instance of the ParallelWork class.

        Args:
            work_items (Optional[list[WorkItem] | list[WorkUnit]], optional): A list of work items
                or work units to be processed in parallel. Defaults to None.
        """
        super().__init__(True, work_items)
        self.ReductionTask: Optional[WorkUnit] = None

    @property
    def type(self) -> str:
        """
        Retrieves the fully qualified type name of the ParallelWork.
        """
        return "DNV.One.Compute.Core.FlowModel.ParallelWork, DNV.One.Compute.Core"

    @property
    def reduction_task(self) -> Optional[WorkUnit]:
        """
        Gets or sets the reduction task.

        The reduction task, if non-null, is a WorkUnit that will execute after all the tasks of this
        instance have completed.
        """
        return self.ReductionTask

    @reduction_task.setter
    def reduction_task(self, value: Optional[WorkUnit]):
        self.ReductionTask = value
        if self.ReductionTask:
            self.ReductionTask.TaskRole = TaskRoles.ReductionTask

    def add(
        self,
        item: list[TypeMeta] | TypeMeta,
        work_unit_id: str = "",
    ) -> WorkUnit:
        """
        Adds a new work unit to the list of work items.

        Args:
            item (list[TypeMeta] | TypeMeta): The work item or list of work items to be added.
            work_unit_id (str, optional): The ID of the work unit. Defaults to an empty string.
        """
        work_unit = WorkUnit(item, work_unit_id)
        self.WorkItems.append(work_unit)
        return work_unit


class Job(FlowModelObject):
    """Represents a batch job."""

    def __init__(self, job_id: str | None = None, user_id: str | None = None):
        """
        Initializes a new instance of the class.

        Args:
            job_id (str | None, optional): The ID of the job. If not provided, a new UUID will be
                generated. Defaults to None.
            user_id (str | None, optional): The ID of the user. Defaults to None.
        """
        super().__init__()
        self.UserId = user_id
        self.JobId = str(uuid.uuid4()) if job_id is None else job_id
        self.JobPreparationWork: Optional[WorkUnit] = None
        self.JobReleaseWork: Optional[WorkUnit] = None
        # Below item is there in the corresponding class of C# code
        # DeploymentModel

    @property
    def type(self) -> str:
        """
        Retrieves the fully qualified type name of the Job.
        """
        return "DNV.One.Compute.Core.FlowModel.Job, DNV.One.Compute.Core"

    @property
    def user_id(self) -> str | None:
        """Gets or sets the identifier of the user submitting the job."""
        return self.UserId

    @user_id.setter
    def user_id(self, value: str):
        self.UserId = value

    @property
    def work(self) -> WorkItem:
        """Gets or sets the work."""
        return self.Work

    @work.setter
    def work(self, value: WorkItem):
        self.Work = value

    @property
    def client_reference(self) -> str:
        """
        Gets or sets the client job reference.

        This property is reserved for use by the client for referencing purposesand will not be used
        by One Compute.
        """
        return self.ClientReference

    @client_reference.setter
    def client_reference(self, value: str):
        self.ClientReference = value

    @property
    def name(self) -> str:
        """
        Gets or sets the name of the job.

        This property is reserved for use by the client for description purposes and will not be
        used by One Compute.
        """
        return self.Name

    @name.setter
    def name(self, value: str):
        self.Name = value

    @property
    def service_name(self) -> str:
        """
        Gets or sets the requested service name.

        In the context of OneCompute Platform, this is the name of the application.
        """
        return self.ServiceName

    @service_name.setter
    def service_name(self, value: str):
        self.ServiceName = value

    @property
    def tags(self) -> str:
        """
        Gets or sets the tags of the job.

        Tags are represented as a semicolon-separated string.
        """
        return self.Tags

    @tags.setter
    def tags(self, value: str):
        self.Tags = value

    @property
    def pool_id(self) -> Optional[str]:
        """Gets or sets the requested pool id."""
        return self.PoolId

    @pool_id.setter
    def pool_id(self, value: Optional[str]):
        self.PoolId = value

    @property
    def timeout_seconds(self) -> Optional[str]:
        """
        Gets or sets the job timeout in seconds.

        If set to a value greater than 0, the job will be cancelled if it has not completed within
        this number of seconds. If set to 0 (default) or less, the job will never time out.
        """
        return self.TimeoutSeconds

    @timeout_seconds.setter
    def timeout_seconds(self, value: Optional[str]):
        self.TimeoutSeconds = value

    @property
    def message_queues(self) -> list[str]:
        """
        Gets or sets the message queues that can be used freely to communicate amongst the workers
        in the job while the Job is running.
        """
        return self.MessageQueues

    @message_queues.setter
    def message_queues(self, value: list[str]):
        self.MessageQueues = value

    @property
    def job_preparation_work(self) -> Optional[WorkUnit]:
        """Gets or sets the Job Preparation Task for preparing the nodes to execute this Job."""
        return self.JobPreparationWork

    @job_preparation_work.setter
    def job_preparation_work(self, value: Optional[WorkUnit]):
        self.JobPreparationWork = value
        if self.JobPreparationWork:
            self.JobPreparationWork.TaskRole = TaskRoles.JobPreparationTask

    @property
    def job_release_work(self) -> Optional[WorkUnit]:
        """Gets or sets the Job Release Task to execute on the nodes after this Job completes."""
        return self.JobReleaseWork

    @job_release_work.setter
    def job_release_work(self, value: Optional[WorkUnit]):
        self.JobReleaseWork = value
        if self.JobReleaseWork:
            self.JobReleaseWork.TaskRole = TaskRoles.JobReleaseTask

    @property
    def scheduling_options(self) -> Optional[SchedulingOptions]:
        """Gets or sets the scheduling options for scheduling the work inside this Job."""
        return self.SchedulingOptions

    @scheduling_options.setter
    def scheduling_options(self, value: Optional[SchedulingOptions]):
        self.SchedulingOptions = value
