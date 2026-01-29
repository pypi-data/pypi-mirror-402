"""Custom exception classes for rapfiles (aiofiles compatible).

This module provides custom exception classes for better error handling
and compatibility with aiofiles. All exceptions inherit from standard
Python exceptions for compatibility.
"""


class RAPFilesError(Exception):
    """
    Base exception for all rapfiles errors.

    This is the base class for all custom exceptions in rapfiles.
    All other rapfiles exceptions inherit from this class, allowing
    you to catch all rapfiles-specific errors with a single exception handler.

    Example:
        ```python
        try:
            await rapfiles.read_file("nonexistent.txt")
        except rapfiles.RAPFilesError as e:
            print(f"Rapfiles error: {e}")
        ```
    """

    pass


class RAPFilesIOError(RAPFilesError, IOError):
    """
    I/O error in rapfiles operations.

    Raised when an I/O operation fails (e.g., disk full, read/write error).
    Inherits from both `RAPFilesError` and `IOError` for compatibility.
    """

    pass


class RAPFilesOSError(RAPFilesError, OSError):
    """OS error in rapfiles operations."""

    pass


class RAPFilesValueError(RAPFilesError, ValueError):
    """Value error in rapfiles operations."""

    pass


class RAPFilesTypeError(RAPFilesError, TypeError):
    """Type error in rapfiles operations."""

    pass


class RAPFilesFileNotFoundError(RAPFilesIOError, FileNotFoundError):
    """
    File not found error.

    Raised when a file or directory does not exist. Inherits from both
    `RAPFilesIOError` and `FileNotFoundError` for compatibility.

    Example:
        ```python
        try:
            await rapfiles.read_file("nonexistent.txt")
        except rapfiles.RAPFilesFileNotFoundError:
            print("File not found!")
        ```
    """

    pass


class RAPFilesPermissionError(RAPFilesOSError, PermissionError):
    """
    Permission denied error.

    Raised when a file operation is denied due to insufficient permissions.
    Inherits from both `RAPFilesOSError` and `PermissionError` for compatibility.

    Example:
        ```python
        try:
            await rapfiles.write_file("/root/protected.txt", "data")
        except rapfiles.RAPFilesPermissionError:
            print("Permission denied!")
        ```
    """

    pass


class RAPFilesIsADirectoryError(RAPFilesOSError, IsADirectoryError):
    """Operation on directory when file expected."""

    pass


class RAPFilesNotADirectoryError(RAPFilesOSError, NotADirectoryError):
    """Operation on file when directory expected."""

    pass


__all__ = [
    "RAPFilesError",
    "RAPFilesIOError",
    "RAPFilesOSError",
    "RAPFilesValueError",
    "RAPFilesTypeError",
    "RAPFilesFileNotFoundError",
    "RAPFilesPermissionError",
    "RAPFilesIsADirectoryError",
    "RAPFilesNotADirectoryError",
]
