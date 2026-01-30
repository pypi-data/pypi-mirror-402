"""A service for managing file operations on the host system."""

import os
import shutil
from concurrent.futures import ThreadPoolExecutor, as_completed
from typing import Optional
from urllib.parse import urlparse

from .file_service import FileService, FileTransferOptions
from .utils._file_service import list_files
from .utils._file_size import (
    is_file_size_within_range,
    is_file_size_within_range_for_path,
)
from .utils._progress_reporter import (
    report_progress_active,
    report_progress_completed,
    report_progress_failed,
    report_progress_in_queue,
)


class HostFileService(FileService):
    """
    A service for managing file operations on the host system.

    This service provides methods for uploading, downloading, deleting, and listing files or
    directories. It uses a multi-threaded approach for uploading and downloading files.
    """

    MAX_FILE_TRANSFER_WORKERS = 4
    """
    Defines the maximum number of worker threads that can be used for file transfer operations.

    The default value is 4.
    """

    def __init__(
        self,
        file_uri: str,
        progress_callback: Optional[FileService.ProgressCallback] = None,
    ):
        """
        Initializes a new instance of the HostFileService class.

        Args:
            file_uri (str): The URI of the file system to interact with.
            progress_callback (Optional[ProgressCallback]): A callback to report progress on the
                operations.
        """
        super().__init__(progress_callback)
        self._file_uri = file_uri

    def upload(
        self, source: str, dest: str, file_options: Optional[FileTransferOptions] = None
    ) -> None:
        """
        Uploads a file or directory from the local system to a specified destination.

        This method is equivalent to copying a file or directory in a local file system.

        Args:
            source (str): The local path to the file or directory to be uploaded.
            dest (str): The destination path where the file or directory should be uploaded.
            file_options (Optional[FileTransferOptions]): Options for the file transfer, such as
                minimum and maximum file size. If None, all files will be uploaded.
        """
        if os.path.isdir(source):
            self._upload_dir(source, dest, file_options)
        else:
            self._upload_file(source, dest, file_options)

    def download(
        self, source: str, dest: str, file_options: Optional[FileTransferOptions] = None
    ) -> None:
        """
        Downloads a file or directory from a source to a destination on the local file system.

        This method is equivalent to copying a file or directory in a local file system.

        Args:
            source (str): The local path to the file or directory to be downloaded.
            dest (str): The local path where the file or directory should be downloaded to.
            file_options (Optional[FileTransferOptions]): Options for the file transfer, such as
                minimum and maximum file size. If None, all files will be downloaded.

        Raises:
            FileNotFoundError: If the source file or directory does not exist.
        """
        container = self._extract_local_path_from_url(self._file_uri)
        source = os.path.normpath(os.path.join(container, source))
        if not os.path.exists(source):
            raise FileNotFoundError(f"File or directory not found: {source}")

        if os.path.isdir(source):
            self._download_dir(source, dest, file_options)
        else:
            self._download_file(source, dest, file_options)

    def delete_file(self, path: str) -> None:
        """
        Deletes a file at a given path.

        Args:
            path (str): The path to the file to delete.
        """
        os.remove(path)

    def delete_dir(self, path: str) -> None:
        """
        Deletes a directory at a given path.

        Args:
            path (str): The path to the directory to delete.
        """
        shutil.rmtree(path)

    def list_dir(self, folder: str, recursive: bool = False) -> list[str]:
        """
        Lists the files in a given folder.

        Args:
            folder (str): The path to the folder to list files from.
            recursive (bool): Whether to list files recursively. Defaults to False.

        Returns:
            A list of file paths.
        """
        if recursive:
            return [
                os.path.join(dp, f)
                for dp, dn, filenames in os.walk(folder)
                for f in filenames
            ]

        return [
            os.path.join(folder, f)
            for f in os.listdir(folder)
            if os.path.isfile(os.path.join(folder, f))
        ]

    def _upload_file(
        self,
        source: str,
        dest: str,
        file_options: Optional[FileTransferOptions] = None,
    ):
        """
        Uploads a file from local system to storage.

        Args:
            source (str): Local file path.
            dest (str): Destination path in storage.
            file_options (Optional[FileTransferOptions]): File transfer options.
        """
        file_options = file_options if file_options else FileTransferOptions()
        min_file_size = file_options.min_size_in_bytes
        max_file_size = file_options.max_size_in_bytes

        if os.path.isfile(source) and is_file_size_within_range_for_path(
            source, min_file_size, max_file_size
        ):
            report_progress_in_queue(
                self.progress_callback, source, dest, os.path.getsize(source)
            )
            self._upload_file_to_storage(source, dest)

    def _upload_dir(
        self,
        source: str,
        dest: str,
        file_options: Optional[FileTransferOptions] = None,
    ):
        """
        Uploads a directory from the source to the destination.

        This method uses a ThreadPoolExecutor to upload files in the directory concurrently.

        Args:
            source (str): The path to the directory to upload.
            dest (str): The path where the directory should be uploaded.
            file_options (Optional[FileTransferOptions]): Options for filtering which files to
            upload.
        """

        prefix = "" if dest == "" else dest + "/"
        local_path = self._extract_local_path_from_url(self._file_uri)

        with ThreadPoolExecutor(self.MAX_FILE_TRANSFER_WORKERS) as executor:
            futures = []
            for file_info in list_files(self._file_uri, source, file_options):
                src_file, src_file_size = file_info

                dir_path = os.path.dirname(src_file)
                rel_path = os.path.relpath(dir_path, source)
                rel_path = "" if rel_path == "." else rel_path + "/"
                file_name = os.path.basename(src_file)

                dest_file_dir = os.path.normpath(
                    os.path.join(*[local_path, prefix, rel_path])
                )
                dest_file = os.path.join(dest_file_dir, file_name)

                os.makedirs(dest_file_dir, exist_ok=True)

                report_progress_in_queue(
                    self.progress_callback, src_file, dest_file, src_file_size
                )

                future = executor.submit(
                    self._upload_file_to_storage, src_file, dest_file
                )
                futures.append(future)

            for future in as_completed(futures):
                try:
                    future.result()
                except Exception as e:
                    print(f"Exception occurred while uploading file: {e}")

    def _upload_file_to_storage(self, source: str, dest: str) -> None:
        """
        Uploads a file from the local system to a specified destination in the storage.

        This method copies the file from the source path to the destination path, reporting progress
        to a callback function if one is provided.

        Args:
            source (str): The local path to the file to be uploaded.
            dest (str): The destination path in the storage where the file will be uploaded.
        """
        total_file_size = os.path.getsize(source)
        try:
            report_progress_active(
                self.progress_callback, source, dest, 0, total_file_size, "Uploading"
            )

            shutil.copy2(source, dest)

            report_progress_completed(
                self.progress_callback, source, dest, total_file_size
            )
        except Exception as ex:
            report_progress_failed(
                self.progress_callback, source, dest, total_file_size, str(ex)
            )

    def _download_file(
        self, source: str, dest: str, file_options: Optional[FileTransferOptions]
    ) -> None:
        """
        Downloads a file from storage to local system.

        Args:
            source (str): Source file path in storage.
            dest (str): Destination path on local system.
            file_options (Optional[FileTransferOptions]): File transfer options.
        """
        file_options = file_options if file_options else FileTransferOptions()
        min_file_size = file_options.min_size_in_bytes
        max_file_size = file_options.max_size_in_bytes

        try:
            file_size = os.path.getsize(source)
            if is_file_size_within_range(file_size, min_file_size, max_file_size):
                report_progress_in_queue(
                    self.progress_callback, source, dest, file_size
                )
                self._download_file_from_storage(source, dest)
        except Exception as ex:
            report_progress_failed(self.progress_callback, source, dest, -1, str(ex))

    def _download_dir(
        self, source: str, dest: str, file_options: Optional[FileTransferOptions]
    ) -> None:
        """
        Downloads a directory from the storage to the local system.

        This method uses a ThreadPoolExecutor to download multiple files concurrently. It first
        lists all the files in the source directory, then submits a task to the executor for each
        file to download it to the destination directory.

        Args:
            source (str): The path to the directory in the storage to be downloaded.
            dest (str): The path on the local system where the directory will be downloaded.
            file_options (Optional[FileTransferOptions]): Options for the file transfer, such as
                minimum and maximum file size. If None, all files will be downloaded.
        """

        # If source is a directory, dest must also be a directory
        if not source == "" and not source.endswith(os.path.sep):
            source += os.path.sep

        if not dest.endswith(os.path.sep):
            dest += os.path.sep

        # Dest is a directory if ending with 'os.path.sep' or '.', otherwise it's a file
        if dest.endswith("."):
            dest += os.path.sep

        with ThreadPoolExecutor(self.MAX_FILE_TRANSFER_WORKERS) as executor:
            futures = []
            for file_info in list_files(self._file_uri, source, file_options):
                src_file_path, src_file_size = file_info
                file_path = dest + os.path.relpath(src_file_path, source)
                report_progress_in_queue(
                    self.progress_callback, src_file_path, file_path, src_file_size
                )
                future = executor.submit(
                    self._download_file_from_storage,
                    src_file_path,
                    file_path,
                )
                futures.append(future)

            # Wait for all tasks to complete
            for future in as_completed(futures):
                try:
                    # If the task returned an exception, this will re-raise it
                    future.result()
                except Exception as e:
                    print(f"Exception occurred while downloading file: {e}")

    def _download_file_from_storage(self, source: str, destination: str) -> None:
        """
        Downloads a file from the storage to a specified location on the local system.

        It creates the destination directory if it doesn't exist, and reports progress to
        a callback function if one is provided.

        Args:
            source (str): The path to the file in the storage to be downloaded.
            destination (str): The path on the local system where the file will be downloaded.
                This can be a directory or a file path.
        """
        # If the destination ends with a period, it's likely intended to be a directory.
        # Append the appropriate directory separator for the current operating system.
        if destination.endswith("."):
            destination += os.path.sep

        # If the destination ends with a directory separator, it's likely intended to be a
        # directory. In that case, join the destination with the base name of the source file.
        # Otherwise, use the destination as is.
        dest_filename = (
            os.path.join(destination, os.path.basename(source))
            if destination.endswith(os.path.sep)
            else destination
        )

        dirname = os.path.dirname(dest_filename)
        if not os.path.exists(dirname):
            os.makedirs(dirname, exist_ok=True)

        total_size = os.path.getsize(source)

        report_progress_active(
            self.progress_callback, source, dest_filename, 0, total_size, "Downloading"
        )

        try:
            shutil.copy2(source, dest_filename)
            report_progress_completed(
                self.progress_callback, source, dest_filename, total_size
            )
        except Exception as ex:
            report_progress_failed(
                self.progress_callback, source, dest_filename, total_size, str(ex)
            )

    @staticmethod
    def _is_directory(path: str) -> bool:
        """
        Check if a given path refers to a directory.

        Args:
            path (str): The path to check.

        Returns:
            bool: True if the path refers to a directory, False otherwise.
        """
        return os.path.isdir(path)

    @staticmethod
    def _is_local_url(url: str) -> bool:
        """
        Check if a URL refers to a local file system path.

        Args: url (str): The URL to check.

        Returns:
            bool: True if the URL refers to a local file system path, False otherwise.
        """
        url_parsed = urlparse(url)
        if url_parsed.scheme in ("file", "") or url_parsed.netloc == "localhost":
            return True
        return False

    @staticmethod
    def _extract_local_path_from_url(url: str) -> str:
        """
        Extract the local file system path from a file URL.

        Args: url (str): The file URL to extract the path from.

        Returns:
            str: The normalized local file system path.
        """
        url_parsed = urlparse(url)
        if url_parsed.scheme in ("file", "") or url_parsed.netloc == "localhost":
            if url_parsed.path.startswith("/"):
                file_path = url_parsed.path[1:]
                return os.path.normpath(file_path)
        return ""
