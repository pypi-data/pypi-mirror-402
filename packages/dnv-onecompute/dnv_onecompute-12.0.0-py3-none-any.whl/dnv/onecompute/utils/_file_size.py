"""Utility functions for handling and manipulating file sizes."""

import os
import re


def convert_to_bytes(input_str: str) -> int:
    """
    Converts a human-readable size string to bytes.
    Args:
        input_str (str): The size string to convert (e.g., '1TB', '20.55 GB', '2GB', '10MB',
        '500KB'). Spaces are allowed between the numeric value and the unit.
    Returns:
        int: The size in bytes.
    Raises:
        ValueError: If the input string format or unit is invalid.
    """
    try:
        # Regular expression pattern to match a numeric value with an optional decimal point,
        # followed by optional whitespace, and then a word (unit) character.
        match = re.match(r"(\d+(\.\d+)?)?\s*(\w+)?", input_str, re.IGNORECASE)
        if match:
            value, _, unit = match.groups()
            value = float(value)
            unit = unit.lower()
            conversion_factors = {
                "b": 1,
                "kb": 1000,
                "mb": 1000 * 1000,
                "gb": 1000 * 1000 * 1000,
                "tb": 1000 * 1000 * 1000 * 1000,
            }
            if unit in conversion_factors:
                return int(value * conversion_factors[unit])
            raise ValueError("Invalid unit. Please use MB, KB, GB, TB, or B.")
        raise ValueError(
            "Invalid input format. Please provide a valid size with"
            "units (MB, KB, GB, TB, or B)."
        )
    except ValueError as ex:
        raise ValueError(str(ex)) from ex


def is_file_size_within_range_for_path(
    file_path: str, min_file_size: int, max_file_size: int
) -> bool:
    """
    Check if the file size is within the given range.
    Args:
        file_path (str): The path to the file.
        min_file_size (int): The minimum file size.
        max_file_size (int): The maximum file size. If it's less than 0, it means there's no
            upper limit.
    Returns:
        bool: True if the file size is within the range, False otherwise.
    """
    file_size = os.path.getsize(file_path)
    return is_file_size_within_range(file_size, min_file_size, max_file_size)


def is_file_size_within_range(
    file_size: int, min_file_size: int, max_file_size: int
) -> bool:
    """
    Checks if a file size is within the specified range.
    """
    return file_size >= min_file_size and (
        max_file_size < 0 or file_size <= max_file_size
    )
