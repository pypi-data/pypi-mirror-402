"""Custom exception classes for rapfiles (aiofiles compatible).

This module provides custom exception classes for better error handling
and compatibility with aiofiles. All exceptions inherit from standard
Python exceptions for compatibility.
"""


class RAPFilesError(Exception):
    """Base exception for all rapfiles errors.

    This is the base class for all custom exceptions in rapfiles.
    All other rapfiles exceptions inherit from this class.
    """

    pass


class RAPFilesIOError(RAPFilesError, IOError):
    """I/O error in rapfiles operations."""

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
    """File not found error."""

    pass


class RAPFilesPermissionError(RAPFilesOSError, PermissionError):
    """Permission denied error."""

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
