""" Progress reporting utilities for file transfer operations."""

from typing import Optional

from ..file_service import FileService, ProgressInfo


def report_progress_active(
    progress_callback: Optional[FileService.ProgressCallback],
    source: str,
    destination: str,
    current: int,
    total_size: int,
    operation: str,
):
    """
    Reports active progress of a file transfer operation.
    """
    report_progress(
        progress_callback,
        ProgressInfo(
            source=source,
            destination=destination,
            current=current,
            total=total_size,
            status=ProgressInfo.Status.IN_PROGRESS,
            message=f"{operation}...",
        ),
    )


def report_progress_in_queue(
    progress_callback: Optional[FileService.ProgressCallback],
    source: str,
    destination: str,
    total_size: int,
):
    """
    Reports queued status of a file transfer operation.
    """
    report_progress(
        progress_callback,
        ProgressInfo(
            source=source,
            destination=destination,
            current=0,
            total=total_size,
            status=ProgressInfo.Status.QUEUE,
            message="Queued",
        ),
    )


def report_progress_ignored(
    progress_callback: Optional[FileService.ProgressCallback],
    source: str,
    destination: str,
    total_size: int,
):
    """
    Reports that a file transfer was ignored due to identical files.
    """
    report_progress(
        progress_callback,
        ProgressInfo(
            source=source,
            destination=destination,
            current=0,
            total=total_size,
            status=ProgressInfo.Status.IGNORED,
            message="Identical file",
        ),
    )


def report_progress_completed(
    progress_callback: Optional[FileService.ProgressCallback],
    source: str,
    destination: str,
    total_size: int,
):
    """
    Reports that a file transfer was completed.
    """
    report_progress(
        progress_callback,
        ProgressInfo(
            source=source,
            destination=destination,
            current=total_size,
            total=total_size,
            status=ProgressInfo.Status.COMPLETED,
            message="",
        ),
    )


def report_progress_failed(
    progress_callback: Optional[FileService.ProgressCallback],
    source: str,
    destination: str,
    total_size: int,
    err_msg: str,
):
    """
    Reports that a file transfer has failed.
    """
    report_progress(
        progress_callback,
        ProgressInfo(
            source=source,
            destination=destination,
            current=-1,
            total=total_size,
            status=ProgressInfo.Status.FAILED,
            message=err_msg,
        ),
    )


def report_progress(
    progress_callback: Optional[FileService.ProgressCallback],
    progress_info: ProgressInfo,
):
    """
    Reports progress information if a callback is set.
    """
    if progress_callback:
        progress_callback(progress_info)
