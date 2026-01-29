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

    This is a synchronous function that checks if a path exists. It does not
    perform file I/O, so it doesn't need to be async. Compatible with
    `aiofiles.ospath.exists()`.

    Args:
        path: Path to check. Can be a string, bytes, or Path object.

    Returns:
        bool: True if the path exists (file or directory), False otherwise.

    Example:
        ```python
        import rapfiles.ospath as ospath

        if ospath.exists("file.txt"):
            print("File exists!")
        ```

    See Also:
        - `rapfiles.exists()`: Async version that checks path existence.
    """
    return os.path.exists(path)


def isfile(path: Union[str, bytes, Path]) -> bool:
    """
    Check if a path is a file (synchronous).

    This is a synchronous function that checks if a path is a file. It does
    not perform file I/O, so it doesn't need to be async. Compatible with
    `aiofiles.ospath.isfile()`.

    Args:
        path: Path to check. Can be a string, bytes, or Path object.

    Returns:
        bool: True if the path exists and is a file, False otherwise.

    Example:
        ```python
        import rapfiles.ospath as ospath

        if ospath.isfile("file.txt"):
            print("It's a file!")
        ```

    See Also:
        - `rapfiles.is_file()`: Async version that checks if path is a file.
    """
    return os.path.isfile(path)


def isdir(path: Union[str, bytes, Path]) -> bool:
    """
    Check if a path is a directory (synchronous).

    This is a synchronous function that checks if a path is a directory. It
    does not perform file I/O, so it doesn't need to be async. Compatible
    with `aiofiles.ospath.isdir()`.

    Args:
        path: Path to check. Can be a string, bytes, or Path object.

    Returns:
        bool: True if the path exists and is a directory, False otherwise.

    Example:
        ```python
        import rapfiles.ospath as ospath

        if ospath.isdir("directory"):
            print("It's a directory!")
        ```

    See Also:
        - `rapfiles.is_dir()`: Async version that checks if path is a directory.
    """
    return os.path.isdir(path)


def getsize(path: Union[str, bytes, Path]) -> int:
    """
    Get the size of a file in bytes (synchronous).

    This is a synchronous function that gets the size of a file. It performs
    minimal I/O (just metadata access), so it doesn't need to be async.
    Compatible with `aiofiles.ospath.getsize()`.

    Args:
        path: Path to the file. Can be a string, bytes, or Path object.

    Returns:
        int: File size in bytes.

    Raises:
        FileNotFoundError: If the file does not exist.
        OSError: If the path is not a file (e.g., it's a directory).

    Example:
        ```python
        import rapfiles.ospath as ospath

        size = ospath.getsize("file.txt")
        print(f"File size: {size} bytes")
        ```

    See Also:
        - `rapfiles.stat()`: Async version that returns full file metadata
          including size.
    """
    return os.path.getsize(path)


def join(*paths: Union[str, bytes, Path]) -> str:
    """
    Join path components (synchronous).

    Joins one or more path components intelligently. This is a pure string
    operation that does not perform file I/O, so it doesn't need to be async.
    Compatible with `aiofiles.ospath.join()`.

    On Unix-like systems, uses forward slashes. On Windows, uses backslashes.
    Empty components are ignored.

    Args:
        *paths: One or more path components. Can be strings, bytes, or Path
            objects. At least one path must be provided.

    Returns:
        str: Joined path as a string. Uses the appropriate path separator for
            the current platform.

    Example:
        ```python
        import rapfiles.ospath as ospath

        full_path = ospath.join("dir", "subdir", "file.txt")
        print(full_path)  # Output: "dir/subdir/file.txt" (Unix) or "dir\\subdir\\file.txt" (Windows)
        ```

    See Also:
        - `os.path.join()`: Standard library equivalent.
    """
    # Convert all paths to strings for os.path.join
    str_paths = [str(p) if isinstance(p, (bytes, Path)) else p for p in paths]
    return os.path.join(*str_paths)


def normpath(path: Union[str, bytes, Path]) -> str:
    """
    Normalize a path (synchronous).

    Normalizes redundant separators and up-level references (e.g., '..' and '.').
    This is a pure string operation that does not perform file I/O, so it
    doesn't need to be async. Compatible with `aiofiles.ospath.normpath()`.

    Args:
        path: Path to normalize. Can be a string, bytes, or Path object.

    Returns:
        str: Normalized path as a string. Redundant separators are collapsed
            and up-level references are resolved where possible.

    Example:
        ```python
        import rapfiles.ospath as ospath

        normalized = ospath.normpath("dir/../other/./file.txt")
        print(normalized)  # Output: "other/file.txt"
        ```

    See Also:
        - `os.path.normpath()`: Standard library equivalent.
    """
    return os.path.normpath(str(path))


def abspath(path: Union[str, bytes, Path]) -> str:
    """
    Get absolute path (synchronous).

    Converts a relative path to an absolute path. This is a pure string
    operation that does not perform file I/O, so it doesn't need to be async.
    Compatible with `aiofiles.ospath.abspath()`.

    Args:
        path: Path to convert. Can be a string, bytes, or Path object.

    Returns:
        str: Absolute path as a string. The path is normalized and made absolute
            relative to the current working directory.

    Example:
        ```python
        import rapfiles.ospath as ospath

        abs_path = ospath.abspath("./relative/path")
        print(abs_path)  # Output example: "/absolute/path/to/file"
        ```

    See Also:
        - `os.path.abspath()`: Standard library equivalent.
        - `rapfiles.canonicalize()`: Async version that resolves symlinks.
    """
    return os.path.abspath(str(path))


def dirname(path: Union[str, bytes, Path]) -> str:
    """
    Get directory name (synchronous).

    Returns the directory portion of a path. This is a pure string operation
    that does not perform file I/O, so it doesn't need to be async. Compatible
    with `aiofiles.ospath.dirname()`.

    Args:
        path: Path to process. Can be a string, bytes, or Path object.

    Returns:
        str: Directory name as a string. Returns the parent directory of the
            path. For a path without directory components, returns an empty string.

    Example:
        ```python
        import rapfiles.ospath as ospath

        dirname = ospath.dirname("/path/to/file.txt")
        print(dirname)  # Output: "/path/to"
        ```

    See Also:
        - `os.path.dirname()`: Standard library equivalent.
        - `basename()`: Get the filename portion of a path.
    """
    return os.path.dirname(str(path))


def basename(path: Union[str, bytes, Path]) -> str:
    """
    Get base name (synchronous).

    Returns the final component of a path (filename or directory name). This
    is a pure string operation that does not perform file I/O, so it doesn't
    need to be async. Compatible with `aiofiles.ospath.basename()`.

    Args:
        path: Path to process. Can be a string, bytes, or Path object.

    Returns:
        str: Base name as a string. Returns the final component of the path.
            For a path ending with a separator, returns an empty string.

    Example:
        ```python
        import rapfiles.ospath as ospath

        basename = ospath.basename("/path/to/file.txt")
        print(basename)  # Output: "file.txt"
        ```

    See Also:
        - `os.path.basename()`: Standard library equivalent.
        - `dirname()`: Get the directory portion of a path.
    """
    return os.path.basename(str(path))


def splitext(path: Union[str, bytes, Path]) -> Tuple[str, str]:
    """
    Split path into root and extension (synchronous).

    Splits the path into root and extension. This is a pure string operation
    that does not perform file I/O, so it doesn't need to be async. Compatible
    with `aiofiles.ospath.splitext()`.

    Args:
        path: Path to split. Can be a string, bytes, or Path object.

    Returns:
        Tuple[str, str]: Tuple of (root, extension) as strings. The extension
            includes the leading dot (e.g., '.txt'). If there's no extension,
            the extension is an empty string.

    Example:
        ```python
        import rapfiles.ospath as ospath

        name, ext = ospath.splitext("file.txt")
        print(name)  # Output: "file"
        print(ext)   # Output: ".txt"
        ```

    See Also:
        - `os.path.splitext()`: Standard library equivalent.
    """
    return os.path.splitext(str(path))


def split(path: Union[str, bytes, Path]) -> Tuple[str, str]:
    """
    Split path into head and tail (synchronous).

    Splits the path into head (directory) and tail (filename). This is a pure
    string operation that does not perform file I/O, so it doesn't need to be
    async. Compatible with `aiofiles.ospath.split()`.

    Args:
        path: Path to split. Can be a string, bytes, or Path object.

    Returns:
        Tuple[str, str]: Tuple of (head, tail) as strings. The head is the
            directory portion, and the tail is the filename portion. If the
            path ends with a separator, the tail is empty.

    Example:
        ```python
        import rapfiles.ospath as ospath

        head, tail = ospath.split("/path/to/file.txt")
        print(head)  # Output: "/path/to"
        print(tail)  # Output: "file.txt"
        ```

    See Also:
        - `os.path.split()`: Standard library equivalent.
        - `dirname()`: Get just the directory portion.
        - `basename()`: Get just the filename portion.
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
