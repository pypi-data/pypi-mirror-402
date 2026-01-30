"""A module for interacting with Azure Blob Storage."""

import os
from concurrent.futures import ThreadPoolExecutor, as_completed
from typing import Optional

from azure.storage.blob import BlobProperties, ContainerClient, ContentSettings
from retry import retry

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
    report_progress_ignored,
    report_progress_in_queue,
)
from .utils.md5_calculator import calculate_md5


class AzureBlobStorageFileService(FileService):
    """
    A concrete implementation of the FileService abstract class for Azure Blob Storage.
    """

    MAX_FILE_TRANSFER_WORKERS = 4
    """Maximum number of workers to use for file transfers."""

    MAX_CONCURRENCY = 2
    """Maximum number of parallel connections to use when the blob size exceeds 64MB."""

    def __init__(
        self,
        container_url: str,
        progress_callback: Optional[FileService.ProgressCallback] = None,
    ):
        """
        Initializes the AzureFileService with the URL of the Azure Blob Storage container.

        Args:
            container_url (str): The URL of the Azure Blob Storage container.
            progress_callback (Optional[ProgressCallback]): A callback to report progress
                on the operations.
        """
        super().__init__(progress_callback)
        self._container_url = container_url
        self._cloud_container_client: ContainerClient = (
            ContainerClient.from_container_url(container_url=container_url)
        )

    def upload(
        self,
        source: str,
        dest: str,
        file_options: Optional[FileTransferOptions] = None,
    ) -> None:
        """
        Uploads a file or directory from the local file system to Azure Blob Storage.

        Args:
            source (str): The path to the file or directory on the local file system.
            dest (str): The path to the file or directory in Azure Blob Storage.
            file_options (Optional[FileTransferOptions]): The file options for filtering files.
                Default is None.
        """
        if os.path.isdir(source):
            self._upload_dir(source, dest, file_options)
        else:
            self._upload_file(source, dest, file_options)

    def download(
        self,
        source: str,
        dest: str,
        file_options: Optional[FileTransferOptions] = None,
    ) -> None:
        """
        Downloads a file or directory from Azure Blob Storage to the local file system.

        Args:
            source (str): The path to the file or directory in Azure Blob Storage.
            dest (str): The path to the file or directory on the local file system.
            file_options (Optional[FileTransferOptions]): The file options for filtering files.
                Default is None.
            callback (Optional[FileService.ProgressCallback]): A callback to report progress on the
                download. Default is None.
        """
        if self._is_directory_blob(source):
            self._download_dir(source, dest, file_options)
        else:
            self._download_file(source, dest, file_options)

    def delete_file(self, path: str) -> None:
        """
        Deletes a file from Azure Blob Storage.

        Args:
            path (str): The path to the file in Azure Blob Storage.
        """
        try:
            self._cloud_container_client.delete_blob(path)
        except Exception as e:
            print(f"Error: Exception occurred while deleting directory: {e}")

    def delete_dir(self, path: str) -> None:
        """
        Deletes a directory and its contents from Azure Blob Storage.

        Args:
            path (str): The path to the directory in Azure Blob Storage.
        """
        try:
            # The files_generator is expected to yield tuples where the first element (index 0)
            # is the blob name.
            files_generator = list_files(self._container_url, path, None)
            blob_names = [file_info[0] for file_info in files_generator]

            # Split blob_names into chunks of 256. This is necessary because the Azure Blob
            # Storage SDK limits the number of blobs that can be deleted in a single request
            # to 256. By splitting the blobs into chunks of 256, we can delete all blobs by
            # making multiple requests.
            for i in range(0, len(blob_names), 256):
                blob_names_chunk = blob_names[i : i + 256]
                self._cloud_container_client.delete_blobs(*blob_names_chunk)
        except Exception as e:
            print(f"Error: Exception occurred while deleting directory: {e}")

    def list_dir(self, folder: str, _: bool = False) -> list[str]:
        """
        Lists the files in a given "folder" in Azure Blob Storage.

        Args:
            folder (str): The prefix to match blob names against. Blobs with names that start with
                this prefix will be returned.
            _ (bool): This parameter is ignored, as Azure Blob Storage does not support recursion.

        Returns:
            list[str]: A list of blob names that start with the given prefix.
        """
        return [
            blob.name
            for blob in self._cloud_container_client.list_blobs(name_starts_with=folder)
        ]

    def _upload_file(
        self,
        source: str,
        dest: str,
        file_options: Optional[FileTransferOptions] = None,
    ):
        """
        Uploads a file from the local system to Azure Blob Storage.

        Args:
            source (str): The path to the local file to upload.
            dest (str): The destination path in Azure Blob Storage where the file will be uploaded.
            file_options (Optional[FileTransferOptions]): Options for the file transfer, such as
                minimum and maximum file size. If None, default options will be used.
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
            self._upload_file_to_destination(source, dest)

    def _upload_dir(
        self,
        source: str,
        dest: str,
        file_options: Optional[FileTransferOptions] = None,
    ):
        """
        Uploads a directory from the local file system to the Blob Storage on the cloud.

        Args:
            source (str): The path to the directory on the local file system.
            dest (str): The path to the directory in Azure Blob Storage.
            file_options (Optional[FileTransferOptions]): Options for filtering which files to
                download.
        """
        prefix = "" if dest == "" else dest + "/"

        with ThreadPoolExecutor(self.MAX_FILE_TRANSFER_WORKERS) as executor:
            futures = []
            for file_info in list_files(self._container_url, source, file_options):
                file_path, file_size = file_info
                dir_path = os.path.dirname(file_path)
                rel_path = os.path.relpath(dir_path, source)
                rel_path = "" if rel_path == "." else rel_path + "/"
                file_name = os.path.basename(file_path)
                blob_path = prefix + rel_path + file_name

                report_progress_in_queue(
                    self.progress_callback, file_path, blob_path, file_size
                )
                future = executor.submit(
                    self._upload_file_to_destination, file_path, blob_path
                )
                futures.append(future)

            for future in as_completed(futures):
                try:
                    future.result()
                except Exception as e:
                    print(f"Exception occurred while uploading file: {e}")

    def _upload_file_to_destination(
        self,
        source: str,
        dest: str,
    ) -> None:
        """
        Uploads a single file from the local file system to Azure Blob Storage.

        Args:
            source (str): The path to the file on the local file system.
            dest (str): The path to the file in Azure Blob Storage.
        """
        total_file_size = os.path.getsize(source)

        if self._compare_local_and_blob_md5(source, dest):
            report_progress_ignored(
                self.progress_callback, source, dest, total_file_size
            )
            return

        report_progress_active(
            self.progress_callback, source, dest, 0, total_file_size, "Uploading"
        )

        file_md5 = calculate_md5(source)
        content_settings = ContentSettings(content_md5=file_md5) if file_md5 else None

        try:
            self._upload_blob_with_retry(source, dest, content_settings)
            report_progress_completed(
                self.progress_callback, source, dest, total_file_size
            )
        except Exception as ex:
            report_progress_failed(
                self.progress_callback, source, dest, total_file_size, str(ex)
            )

    @retry(delay=3, tries=3)
    def _upload_blob_with_retry(
        self, source: str, dest: str, content_settings: Optional[ContentSettings]
    ):
        """
        Uploads a file to Azure Blob Storage with retry.

        This function will attempt to upload a file to Azure Blob Storage up to 3 times,
        waiting 3 seconds between each attempt. If the upload fails, it will be retried
        automatically.

        Args:
            source (str): The path to the file on the local file system.
            dest (str): The path to the file in Azure Blob Storage.
            content_settings (Optional[ContentSettings]): The content settings for the blob.

        Raises:
            Exception: If the upload fails after 3 attempts.
        """
        with open(source, "rb") as data:
            self._cloud_container_client.upload_blob(
                name=dest,
                data=data,
                overwrite=True,
                max_concurrency=self.MAX_CONCURRENCY,
                progress_hook=lambda current, total: (
                    report_progress_active(
                        self.progress_callback,
                        source,
                        dest,
                        current,
                        total,
                        "Uploading",
                    )
                ),
                content_settings=content_settings,
            )

    def _download_file(
        self, source: str, dest: str, file_options: Optional[FileTransferOptions]
    ):
        """
        Downloads a file from Azure Blob Storage to the local system.

        Args:
            source (str): The path to the file in Azure Blob Storage to download.
            dest (str): The destination path on the local system where the file will be downloaded.
            file_options (Optional[FileTransferOptions]): Options for the file transfer, such as
                minimum and maximum file size. If None, default options will be used.
        """
        file_options = file_options if file_options else FileTransferOptions()
        min_file_size = file_options.min_size_in_bytes
        max_file_size = file_options.max_size_in_bytes
        try:
            blob_client = self._cloud_container_client.get_blob_client(blob=source)
            blob_size = blob_client.get_blob_properties().size

            if is_file_size_within_range(blob_size, min_file_size, max_file_size):
                report_progress_in_queue(
                    self.progress_callback, source, dest, blob_size
                )
                self._download_file_from_blob_storage(source, dest)
        except Exception as ex:
            report_progress_failed(self.progress_callback, source, dest, -1, str(ex))

    def _download_dir(
        self, source: str, dest: str, file_options: Optional[FileTransferOptions]
    ):
        """
        Downloads a directory from Azure Blob Storage to the local system.

        Args:
            source (str): Path to the directory in Azure Blob Storage.
            dest (str): Destination path on the local system.
            file_options (Optional[FileTransferOptions]): Transfer options, if any.
        """
        # If source is a directory, dest must also be a directory
        if not source == "" and not source.endswith("/"):
            source += "/"
        if not dest.endswith(os.path.sep):
            dest += os.path.sep

        with ThreadPoolExecutor(self.MAX_FILE_TRANSFER_WORKERS) as executor:
            futures = []
            for blob_info in list_files(self._container_url, source, file_options):
                blob_path, blob_size = blob_info
                file_path = dest + os.path.relpath(blob_path, source)
                report_progress_in_queue(
                    self.progress_callback, blob_path, file_path, blob_size
                )
                future = executor.submit(
                    self._download_file_from_blob_storage,
                    blob_path,
                    file_path,
                )
                futures.append(future)

            # Wait for all tasks to complete
            for future in as_completed(futures):
                try:
                    # If the task returned an exception, this will re-raise it
                    future.result()
                except Exception as e:
                    print(f"Exception occurred while downloading blob: {e}")

    def _download_file_from_blob_storage(self, source: str, destination: str):
        """
        Downloads a file from Azure Blob Storage and saves it to a specified path on the local
        filesystem.

        Args:
            source (str): The path to a file in Azure Blob Storage.
            destination (str): The path on the local file system where the file will be saved.
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

        blob_client = self._cloud_container_client.get_blob_client(blob=source)
        prop = blob_client.get_blob_properties()
        blob_total_size = prop.size

        if self._compare_local_and_blob_md5(dest_filename, source, prop):
            report_progress_ignored(
                self.progress_callback, source, dest_filename, blob_total_size
            )
            return

        report_progress_active(
            self.progress_callback,
            source,
            dest_filename,
            0,
            blob_total_size,
            "Downloading",
        )

        dirname = os.path.dirname(dest_filename)
        if not os.path.exists(dirname):
            os.makedirs(dirname, exist_ok=True)

        try:
            self._download_blob_with_retry(source, dest_filename)
            report_progress_completed(
                self.progress_callback, source, dest_filename, blob_total_size
            )
        except Exception as ex:
            report_progress_failed(
                self.progress_callback, source, dest_filename, blob_total_size, str(ex)
            )

    @retry(delay=3, tries=3)
    def _download_blob_with_retry(self, source: str, dest_filename: str):
        """
        Download a blob from Azure Blob Storage with retry.

        Args:
            source (str): The source blob to download.
            dest_filename (str): The destination file path to download the blob to.
        """
        with open(dest_filename, "wb") as blob_file:
            downloader = self._cloud_container_client.download_blob(
                blob=source,
                max_concurrency=self.MAX_CONCURRENCY,
                progress_hook=lambda current, total: (
                    report_progress_active(
                        self.progress_callback,
                        source,
                        dest_filename,
                        current,
                        total,
                        "Downloading",
                    )
                ),
            )
            blob_file.write(downloader.readall())

    def _compare_local_and_blob_md5(
        self,
        local_file_path: str,
        blob_file_path: str,
        blob_properties: Optional[BlobProperties] = None,
    ) -> bool:
        """
        Compare the MD5 hash of a local file and a file in Azure Blob Storage.

        Args:
            local_file_path (str): The path to the file on the local file system.
            blob_file_path (str): The path to the file in Azure Blob Storage.
            blob_properties (Optional[BlobProperties]): The properties of the blob file.

        Returns:
            bool: True if the MD5 hashes match, False otherwise.
        """
        if not os.path.isfile(local_file_path):
            return False

        # Get the blob client for the blob file
        if blob_properties is None:
            blob_client = self._cloud_container_client.get_blob_client(blob_file_path)
            blob_properties = (
                blob_client.get_blob_properties() if blob_client.exists() else None
            )

        if blob_properties:
            blob_md5 = blob_properties.content_settings.content_md5

            # If the blob has an MD5, compare it to the local file's MD5
            if blob_md5 is not None:
                local_file_md5 = calculate_md5(local_file_path)
                # If the MD5s match, return True
                if blob_md5 == local_file_md5:
                    return True
        return False

    def _is_directory_blob(self, blob_name: str) -> bool:
        """
        Checks if a blob name represents a directory in Azure Blob Storage.

        Args:
            blob_name (str): The name of the blob.

        Returns:
            bool: True if the blob name represents a directory, False otherwise.
        """

        # Check if the blob name ends with a forward slash ("/")
        if blob_name.endswith("/"):
            # Since Azure Blob Storage doesn't have true directories,
            # a blob name ending with a slash can be considered a directory marker.
            return True

        # If there's uncertainty, try to download the blob's metadata.
        # If the metadata exists, we assume it's a regular file, not a directory marker.
        # If an exception is raised during metadata fetching, it's either due to the blob
        # being a directory marker or an unexpected error.
        try:
            blob_client = self._cloud_container_client.get_blob_client(blob_name)
            blob_client.get_blob_properties()
            return False
        except Exception:
            return True
