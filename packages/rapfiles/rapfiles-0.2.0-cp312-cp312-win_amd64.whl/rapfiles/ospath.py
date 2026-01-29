"""Path operations module (aiofiles.ospath compatible).

This module provides synchronous path operations compatible with `aiofiles.ospath`.
These operations work with path strings and do not perform file I/O, so they
are synchronous and do not need to be async.

All functions accept str, bytes, or Path objects and return appropriate types.
"""

import os
from pathlib import Path
from typing import Union, Tuple

# Re-export common path operations for aiofiles compatibility
# These are synchronous operations that work with paths (not file I/O)


def exists(path: Union[str, bytes, Path]) -> bool:
    """
    Check if a path exists (synchronous).

    Args:
        path: Path to check (str, bytes, or Path object)

    Returns:
        True if the path exists, False otherwise
    """
    return os.path.exists(path)


def isfile(path: Union[str, bytes, Path]) -> bool:
    """
    Check if a path is a file (synchronous).

    Args:
        path: Path to check (str, bytes, or Path object)

    Returns:
        True if the path is a file, False otherwise
    """
    return os.path.isfile(path)


def isdir(path: Union[str, bytes, Path]) -> bool:
    """
    Check if a path is a directory (synchronous).

    Args:
        path: Path to check (str, bytes, or Path object)

    Returns:
        True if the path is a directory, False otherwise
    """
    return os.path.isdir(path)


def getsize(path: Union[str, bytes, Path]) -> int:
    """
    Get the size of a file (synchronous).

    Args:
        path: Path to the file (str, bytes, or Path object)

    Returns:
        File size in bytes

    Raises:
        FileNotFoundError: If the file does not exist
        OSError: If the path is not a file
    """
    return os.path.getsize(path)


def join(*paths: Union[str, bytes, Path]) -> str:
    """
    Join path components (synchronous).

    Args:
        *paths: One or more path components (str, bytes, or Path objects)

    Returns:
        Joined path as a string
    """
    # Convert all paths to strings for os.path.join
    str_paths = [str(p) if isinstance(p, (bytes, Path)) else p for p in paths]
    return os.path.join(*str_paths)


def normpath(path: Union[str, bytes, Path]) -> str:
    """
    Normalize a path (synchronous).

    Normalizes redundant separators and up-level references.

    Args:
        path: Path to normalize (str, bytes, or Path object)

    Returns:
        Normalized path as a string
    """
    return os.path.normpath(str(path))


def abspath(path: Union[str, bytes, Path]) -> str:
    """
    Get absolute path (synchronous).

    Args:
        path: Path to convert (str, bytes, or Path object)

    Returns:
        Absolute path as a string
    """
    return os.path.abspath(str(path))


def dirname(path: Union[str, bytes, Path]) -> str:
    """
    Get directory name (synchronous).

    Returns the directory portion of a path.

    Args:
        path: Path to process (str, bytes, or Path object)

    Returns:
        Directory name as a string
    """
    return os.path.dirname(str(path))


def basename(path: Union[str, bytes, Path]) -> str:
    """
    Get base name (synchronous).

    Returns the final component of a path.

    Args:
        path: Path to process (str, bytes, or Path object)

    Returns:
        Base name as a string
    """
    return os.path.basename(str(path))


def splitext(path: Union[str, bytes, Path]) -> Tuple[str, str]:
    """
    Split path into (root, ext) (synchronous).

    Splits the path into root and extension.

    Args:
        path: Path to split (str, bytes, or Path object)

    Returns:
        Tuple of (root, extension) as strings
    """
    return os.path.splitext(str(path))


def split(path: Union[str, bytes, Path]) -> Tuple[str, str]:
    """
    Split path into (head, tail) (synchronous).

    Splits the path into head (directory) and tail (filename).

    Args:
        path: Path to split (str, bytes, or Path object)

    Returns:
        Tuple of (head, tail) as strings
    """
    return os.path.split(str(path))


__all__ = [
    "exists",
    "isfile",
    "isdir",
    "getsize",
    "join",
    "normpath",
    "abspath",
    "dirname",
    "basename",
    "splitext",
    "split",
]
