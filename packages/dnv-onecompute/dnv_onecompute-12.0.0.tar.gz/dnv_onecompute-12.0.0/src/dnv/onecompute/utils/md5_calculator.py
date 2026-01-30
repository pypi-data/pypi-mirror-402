"""A module for file-related utility functions."""

import hashlib
import mmap
from typing import Optional


def calculate_md5(file_path: str, chunk_size=4096) -> Optional[bytes]:
    """
    Calculate the MD5 hash of a file.

    This method reads the file in blocks of size defined by `chunk_size` bytes, which works for
    large files without using too much memory. The MD5 hash is calculated by updating the hash
    with each block of bytes.

    If the file cannot be opened, or if an error occurs while reading the file and calculating
    the hash,the method will print an error message and return None.

    Args:
        file_path (str): The path to the file for which the MD5 hash is to be calculated.
        chunk_size (int, optional): The size of the chunks in which the file is read.
            Defaults to 4096.

    Returns:
        The MD5 hash of the file, in bytes, or None if an error occurred.
    """
    md5_hash = hashlib.md5()
    try:
        with open(file_path, "rb") as file:
            for byte_block in iter(lambda: file.read(chunk_size), b""):
                md5_hash.update(byte_block)
    except IOError as e:
        print(f"Error: File {file_path} cannot be opened: {e}")
        return None
    except Exception as e:
        print(f"Error: An error occurred while calculating the MD5 hash: {e}")
        return None
    return md5_hash.digest()


def calculate_md5_mmap(file_path: str, chunk_size=4096) -> Optional[bytes]:
    """
    Calculate the MD5 hash of a file using memory-mapped file support.

    This method reads the file in blocks of size defined by `chunk_size` bytes using a
    memory-mapped file object, which allows efficient reading and manipulation of files too
    large to fit into memory. The MD5 hash is calculated by updating the hash with each block
    of bytes.

    If the file cannot be opened, or if an error occurs while reading the file and calculating
    the hash,the method will print an error message and return None.

    Args:
        file_path (str): The path to the file for which the MD5 hash is to be calculated.
        chunk_size (int, optional): The size of the chunks in which the file is read.
            Defaults to 4096.

    Returns:
        The MD5 hash of the file, in bytes, or None if an error occurred.
    """
    md5_hash = hashlib.md5()
    try:
        with open(file_path, "rb") as file:
            with mmap.mmap(
                file.fileno(), 0, access=mmap.ACCESS_READ
            ) as mem_mapped_file:
                for i in range(0, len(mem_mapped_file), chunk_size):
                    md5_hash.update(mem_mapped_file[i : i + chunk_size])
    except IOError as e:
        print(f"Error: File {file_path} cannot be opened: {e}")
        return None
    except Exception as e:
        print(f"Error: An error occurred while calculating the MD5 hash: {e}")
        return None
    return md5_hash.digest()
