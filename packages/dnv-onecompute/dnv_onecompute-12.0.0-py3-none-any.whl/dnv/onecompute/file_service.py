""" This module defines the abstract base class for a file service."""

from abc import ABC, abstractmethod
from dataclasses import dataclass, field
from enum import Enum
from typing import Callable, NamedTuple, Optional

from .utils._file_size import convert_to_bytes


class ProgressInfo(NamedTuple):
    """
    A named tuple used for providing progress information.
    """

    class Status(Enum):
        """An enumeration representing the status of a file operation."""

        QUEUE = 0
        """The operation is queued and waiting to be processed."""

        IGNORED = 1
        """The operation is ignored and not processed."""

        IN_PROGRESS = 2
        """The operation is in progress."""

        FAILED = 3
        """The operation failed."""

        COMPLETED = 4
        """The operation completed successfully."""

    source: str
    """The source file path that is being processed."""

    destination: str
    """The destination path where the file is being transferred to."""

    current: int
    """The current progress of the file operation, measured in bytes."""

    total: int
    """The total size of the file being processed, measured in bytes."""

    status: Status
    """The current status of the file operation."""

    message: str
    """A message providing additional details about the file operation."""


@dataclass
class FileTransferOptions:
    """
    A class for storing file options, including file patterns, size thresholds, and overwrite
    settings.
    """

    patterns: list[str] = field(default_factory=lambda: ["**/*.*"])
    """
    Gets or sets a list of file patterns to search for. Each pattern can contain wildcard characters
    such as '*' and '?'. If multiple patterns are provided, files that match any of the patterns
    will be returned.

    If not specified, it defaults to ["**/*.*"]
    """

    min_size: Optional[str] = None
    """
    Gets or sets an optional size threshold in human-readable format. Files that are smaller than
    this threshold will be excluded from the results.

    If not specified, there is no upper limit on the file size.
    """

    max_size: Optional[str] = None
    """
    Gets or sets an optional size threshold in human-readable format. Files that are bigger than
    this threshold will be excluded from the results.

    If left unspecified, the default value is None, indicating no upper limit on file size.
    """

    _min_size_in_bytes: int = 0
    _max_size_in_bytes: int = -1

    def __post_init__(self):
        """
        Initializes the FileTransferOptions object and converts size thresholds to bytes if
        provided.
        """
        if self.min_size and self.min_size.strip():
            self._min_size_in_bytes = convert_to_bytes(self.min_size)

        if self.max_size and self.max_size.strip():
            self._max_size_in_bytes = convert_to_bytes(self.max_size)

    @property
    def min_size_in_bytes(self) -> int:
        """
        Gets the minimum size threshold in bytes.

        Returns:
            int: The minimum size threshold in bytes.
        """
        return self._min_size_in_bytes

    @property
    def max_size_in_bytes(self) -> int:
        """
        Gets the maximum size threshold in bytes.

        Returns:
            int: The maximum size threshold in bytes.
        """
        return self._max_size_in_bytes


class FileService(ABC):
    """
    Abstract base class for a file service.

    This class defines the interface for a file service, which can perform operations such as
    uploading, downloading, deleting files and directories, and listing files and directories.

    Each method should be overridden by a concrete subclass that implements the specific behavior
    for a particular type of file system or storage service.
    """

    ProgressCallback = Callable[[ProgressInfo], None]
    """
    Type alias for a progress callback function. This function is intended to provide
    real-time feedback on the progress of an operation. It takes a single argument of
    type ProgressInfo.
    """

    def __init__(self, progress_callback: Optional[ProgressCallback]):
        """
        Initializes a new instance of the FileService class.

        Args:
            progress_callback (Optional[ProgressCallback]): A callback to report progress on the
                operations.
        """
        self.progress_callback = progress_callback

    @abstractmethod
    def upload(
        self,
        source: str,
        dest: str,
        file_options: Optional[FileTransferOptions] = None,
    ) -> None:
        """
        Uploads a file or directory from a source to a destination.

        Args:
            source (str): The path to the file or directory to upload.
            dest (str): The path where the file or directory should be uploaded.
            file_options (Optional[FileTransferOptions]): Options for filtering which files to
                upload.

        Returns:
            None
        """

    @abstractmethod
    def download(
        self,
        source: str,
        dest: str,
        file_options: Optional[FileTransferOptions] = None,
    ) -> None:
        """
        Downloads a file or directory from a source to a destination.

        Args:
            source (str): The path to the file or directory to download.
            dest (str): The path where the file or directory should be downloaded to.
            file_options (Optional[FileTransferOptions]): Options for filtering which files to
                download.

        Returns:
            None
        """

    @abstractmethod
    def delete_file(self, path: str) -> None:
        """
        Deletes a file at a given path.

        Args:
            path (str): The path to the file to delete.

        Returns:
            None
        """

    @abstractmethod
    def delete_dir(self, path: str) -> None:
        """
        Deletes a directory at a given path.

        Args:
            path (str): The path to the directory to delete.

        Returns:
            None
        """

    @abstractmethod
    def list_dir(self, folder: str, recursive: bool = False) -> list[str]:
        """
        Lists the files in a given folder.

        Args:
            folder (str): The path to the folder to list files from.
            recursive (bool): Whether to list files recursively. Defaults to False.

        Returns:
            A list of file paths.
        """
