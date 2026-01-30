"""A private module containing utility functions for file operations."""

import fnmatch
import glob
import os
from itertools import chain
from typing import Generator, Optional

from azure.storage.blob import ContainerClient

from ..file_service import FileTransferOptions
from ._file_size import is_file_size_within_range


def list_files(
    container_url: str, folder: str, file_options: Optional[FileTransferOptions] = None
) -> Generator[tuple[str, int], None, None]:
    """
    A generator function that lists all files matching the given patterns recursively in
    the specified folder, depending on the specified folder. If the folder is an absolute
    path, it is assumed that it points to the local storage space, otherwise it points to
    the BLOB Storage in the cloud.

    Args:
        folder (str): The root folder to start searching from.
        file_options (Optional[FileTransferOptions]): The file options for filtering files.
            Default is None.

    Yields:
        tuple[str, int]: A tuple containing the absolute path of a file matching one of the
        specified patterns and its size.
    """
    file_options = file_options if file_options else FileTransferOptions()
    patterns = file_options.patterns
    min_file_size = file_options.min_size_in_bytes
    max_file_size = file_options.max_size_in_bytes
    is_local_file = os.path.isabs(folder) and os.path.exists(folder)
    func = (
        list_files_from_local_file_storage
        if is_local_file
        else list_files_from_cloud_blob_storage
    )
    yield from func(container_url, folder, patterns, min_file_size, max_file_size)


def list_files_from_cloud_blob_storage(
    container_url: str,
    folder: str,
    patterns: list[str],
    min_file_size: int,
    max_file_size: int,
) -> Generator[tuple[str, int], None, None]:
    """
    Lists all files matching the given patterns in the specified folder from a cloud blob
    storage service.

    Args:
        folder (str): The root folder to start searching from.
        patterns (List[str]): A list of patterns to match files against.
        min_file_size (int): The minimum size in bytes of files to include in the results.
        max_file_size (int): The maximum size in bytes of files to exclude in the results.

    Returns:
        Generator[Tuple[str, int], None, None]: A generator yielding tuples, each containing
        the relative path of a file matching one of the specified patterns and its size.
    """
    cloud_container_client = ContainerClient.from_container_url(
        container_url=container_url
    )
    for blob in cloud_container_client.list_blobs(name_starts_with=folder):
        if any(fnmatch.fnmatch(blob.name, pattern) for pattern in patterns):
            if is_file_size_within_range(blob.size, min_file_size, max_file_size):
                yield (
                    blob.name,
                    blob.size,
                )  # blob.name contains relative path + name


def list_files_from_local_file_storage(
    _: str,
    folder: str,
    patterns: list[str],
    min_file_size: int,
    max_file_size: int,
) -> Generator[tuple[str, int], None, None]:
    """
    Lists all files matching the given patterns in the specified folder from a local storage
    system.

    Args:
        folder (str): The root folder to start searching from.
        patterns (List[str]): A list of patterns to match files against.
        min_file_size (int): The minimum size in bytes of files to include in the results.
        max_file_size (int): The maximum size in bytes of files to exclude in the results.
    Yields:
        tuple[str, int]: A tuple containing the absolute path of a file matching one of the
        specified patterns and its size.
    """
    folder = os.path.abspath(folder)
    file_paths = chain.from_iterable(
        glob.iglob(os.path.join(folder, pattern), recursive=True)
        for pattern in patterns
    )
    for file_path in file_paths:
        if os.path.isfile(file_path):
            file_size = os.path.getsize(file_path)
            if is_file_size_within_range(file_size, min_file_size, max_file_size):
                yield (file_path, file_size)
