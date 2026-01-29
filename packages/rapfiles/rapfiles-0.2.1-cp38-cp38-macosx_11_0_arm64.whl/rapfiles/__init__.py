"""True async filesystem I/O — no fake async, no GIL stalls."""

from typing import (
    List,
    Optional,
    Union,
    Any,
    Coroutine,
    TypeVar,
    TYPE_CHECKING,
    Tuple,
    Type,
    Dict,
)
from types import TracebackType

if TYPE_CHECKING:
    from typing import Protocol

# Import ospath module for aiofiles compatibility
from rapfiles import ospath  # noqa: F401

try:
    from _rapfiles import (  # type: ignore[import-not-found]
        read_file_async,
        write_file_async,
        read_file_bytes_async,
        write_file_bytes_async,
        append_file_async,
        open_file,
        AsyncFile,
        create_dir_async,
        create_dir_all_async,
        remove_dir_async,
        remove_dir_all_async,
        list_dir_async,
        exists_async,
        is_file_async,
        is_dir_async,
        stat_async,
        metadata_async,
        FileMetadata,
        walk_dir_async,
        copy_file_async,
        move_file_async,
        remove_file_async,
        hard_link_async,
        symlink_async,
        canonicalize_async,
        atomic_write_file_async,
        atomic_write_file_bytes_async,
        atomic_move_file_async,
        lock_file_async,
        FileLock,
        read_files_async,
        write_files_async,
        copy_files_async,
    )
except ImportError:
    # Try alternative import path
    try:
        from rapfiles._rapfiles import (
            read_file_async,
            write_file_async,
            read_file_bytes_async,
            write_file_bytes_async,
            append_file_async,
            open_file,
            AsyncFile,
            create_dir_async,
            create_dir_all_async,
            remove_dir_async,
            remove_dir_all_async,
            list_dir_async,
            exists_async,
            is_file_async,
            is_dir_async,
            stat_async,
            metadata_async,
            FileMetadata,
            walk_dir_async,
            copy_file_async,
            move_file_async,
            remove_file_async,
            hard_link_async,
            symlink_async,
            canonicalize_async,
            atomic_write_file_async,
            atomic_write_file_bytes_async,
            atomic_move_file_async,
            lock_file_async,
            FileLock,
            read_files_async,
            write_files_async,
            copy_files_async,
        )
    except ImportError:
        raise ImportError(
            "Could not import _rapfiles. Make sure rapfiles is built with maturin."
        )

__version__: str = "0.2.1"
__all__: List[str] = [
    # File operations
    "read_file_async",
    "write_file_async",
    "read_file_bytes_async",
    "write_file_bytes_async",
    "append_file_async",
    "read_file",
    "write_file",
    "read_file_bytes",
    "write_file_bytes",
    "append_file",
    # File handles
    "open",
    "open_file",
    "AsyncFile",
    # Directory operations
    "create_dir",
    "create_dir_all",
    "remove_dir",
    "remove_dir_all",
    "list_dir",
    "exists",
    "is_file",
    "is_dir",
    # Metadata operations
    "stat",
    "metadata",
    "FileMetadata",
    # Directory traversal
    "walk_dir",
    # File manipulation
    "copy_file",
    "move_file",
    "rename",
    "remove_file",
    "hard_link",
    "symlink",
    "canonicalize",
    # Atomic operations
    "atomic_write_file",
    "atomic_write_file_bytes",
    "atomic_move_file",
    # File locking
    "lock_file",
    "lock_file_shared",
    "FileLock",
    "_LockContextManager",
    # Batch operations
    "read_files",
    "read_files_dict",
    "write_files",
    "copy_files",
]


# Convenience async functions
async def read_file(path: str) -> str:
    """
    Read a file asynchronously using true async I/O.

    This function reads the entire file and returns its contents as a UTF-8
    decoded string. All I/O operations execute outside the Python GIL using
    native Rust/Tokio, ensuring true async behavior and preventing event loop
    stalls.

    The file is read completely into memory. For large files, consider using
    `open()` with a file handle for streaming reads.

    Args:
        path: Path to the file to read. Can be a relative or absolute path.

    Returns:
        str: File contents as a UTF-8 decoded string.

    Raises:
        FileNotFoundError: If the file does not exist.
        IOError: If the file cannot be read (e.g., permission denied).
        ValueError: If the path is invalid (empty string or contains null bytes).

    Example:
        ```python
        content = await read_file("example.txt")
        print(content)
        # Output: Hello from rapfiles!
        ```

    See Also:
        - `read_file_bytes()`: Read file as raw bytes.
        - `open()`: Open file handle for streaming reads.
        - `read_files()`: Read multiple files concurrently.
    """
    return await read_file_async(path)


async def write_file(path: str, contents: str) -> None:
    """
    Write a file asynchronously using true async I/O.

    This function writes the entire contents to a file. If the file exists,
    it will be overwritten. If the file does not exist, it will be created.
    All I/O operations execute outside the Python GIL using native Rust/Tokio,
    ensuring true async behavior and preventing event loop stalls.

    The contents are encoded as UTF-8 before writing. For binary data, use
    `write_file_bytes()` instead.

    Args:
        path: Path to the file to write. Can be a relative or absolute path.
        contents: Content to write to the file. Will be encoded as UTF-8.

    Raises:
        IOError: If the file cannot be written (e.g., disk full, I/O error).
        PermissionError: If write permission is denied.
        ValueError: If the path is invalid (empty string or contains null bytes).

    Example:
        ```python
        await write_file("example.txt", "Hello, world!")
        # File is now written with UTF-8 encoded content
        ```

    See Also:
        - `write_file_bytes()`: Write raw bytes to a file.
        - `atomic_write_file()`: Write file atomically (prevents partial writes).
        - `append_file()`: Append content to an existing file.
        - `write_files()`: Write multiple files concurrently.
    """
    await write_file_async(path, contents)


async def read_file_bytes(path: str) -> bytes:
    """
    Read a file asynchronously as raw bytes.

    This function reads the entire file and returns its contents as raw bytes
    without any encoding/decoding. All I/O operations execute outside the
    Python GIL using native Rust/Tokio, ensuring true async behavior and
    preventing event loop stalls.

    Use this function for binary files (images, executables, etc.) or when you
    need to handle encoding manually. For text files, use `read_file()` instead.

    Args:
        path: Path to the file to read. Can be a relative or absolute path.

    Returns:
        bytes: File contents as raw bytes.

    Raises:
        FileNotFoundError: If the file does not exist.
        IOError: If the file cannot be read (e.g., permission denied).
        ValueError: If the path is invalid (empty string or contains null bytes).

    Example:
        ```python
        data = await read_file_bytes("image.png")
        # data is now bytes: b'\\x89PNG\\r\\n\\x1a\\n...'
        ```

    See Also:
        - `read_file()`: Read file as UTF-8 decoded string.
        - `open()`: Open file handle for streaming reads.
        - `read_files()`: Read multiple files concurrently.
    """
    return await read_file_bytes_async(path)


async def write_file_bytes(path: str, contents: bytes) -> None:
    """
    Write raw bytes to a file asynchronously.

    This function writes raw bytes to a file without any encoding/decoding.
    If the file exists, it will be overwritten. If the file does not exist,
    it will be created. All I/O operations execute outside the Python GIL
    using native Rust/Tokio, ensuring true async behavior and preventing
    event loop stalls.

    Use this function for binary files (images, executables, etc.) or when
    you need to write bytes directly. For text files, use `write_file()`
    instead.

    Args:
        path: Path to the file to write. Can be a relative or absolute path.
        contents: Raw bytes to write to the file.

    Raises:
        IOError: If the file cannot be written (e.g., disk full, I/O error).
        PermissionError: If write permission is denied.
        ValueError: If the path is invalid (empty string or contains null bytes).

    Example:
        ```python
        await write_file_bytes("data.bin", b"\\x00\\x01\\x02")
        # File now contains the raw bytes
        ```

    See Also:
        - `write_file()`: Write UTF-8 encoded string to a file.
        - `atomic_write_file_bytes()`: Write bytes atomically (prevents partial writes).
        - `write_files()`: Write multiple files concurrently.
    """
    await write_file_bytes_async(path, contents)


async def append_file(path: str, contents: str) -> None:
    """
    Append content to a file asynchronously.

    This function appends content to the end of a file. If the file does not
    exist, it will be created. The content is encoded as UTF-8 before writing.
    All I/O operations execute outside the Python GIL using native Rust/Tokio,
    ensuring true async behavior and preventing event loop stalls.

    This is useful for log files, data collection, or any scenario where you
    need to add content to an existing file without overwriting it.

    Args:
        path: Path to the file to append to. Can be a relative or absolute path.
        contents: Content to append to the file. Will be encoded as UTF-8.

    Raises:
        IOError: If the file cannot be written (e.g., disk full, I/O error).
        PermissionError: If write permission is denied.
        ValueError: If the path is invalid (empty string or contains null bytes).

    Example:
        ```python
        await append_file("log.txt", "New log entry\\n")
        # Content is appended to the end of log.txt
        ```

    See Also:
        - `write_file()`: Overwrite file with new content.
        - `write_file_bytes()`: Append raw bytes to a file (use with 'a' mode via `open()`).
    """
    await append_file_async(path, contents)


# Directory operations
async def create_dir(path: str) -> None:
    """
    Create a single directory asynchronously.

    Creates a single directory. Parent directories must already exist. If you
    need to create parent directories as well, use `create_dir_all()` instead.
    All I/O operations execute outside the Python GIL using native Rust/Tokio,
    ensuring true async behavior and preventing event loop stalls.

    Args:
        path: Path to the directory to create. Can be a relative or absolute path.

    Raises:
        FileExistsError: If the directory already exists.
        IOError: If the directory cannot be created (e.g., parent doesn't exist).
        PermissionError: If permission is denied.
        ValueError: If the path is invalid (empty string or contains null bytes).

    Example:
        ```python
        await create_dir("new_directory")
        # Directory is created if parent exists
        ```

    See Also:
        - `create_dir_all()`: Create directory and all parent directories.
        - `remove_dir()`: Remove an empty directory.
    """
    await create_dir_async(path)


async def create_dir_all(path: str) -> None:
    """
    Create a directory and all parent directories asynchronously.

    Creates a directory and any necessary parent directories. Equivalent to
    `mkdir -p` in Unix. This function will create all missing parent
    directories in the path. All I/O operations execute outside the Python GIL
    using native Rust/Tokio, ensuring true async behavior and preventing
    event loop stalls.

    Args:
        path: Path to the directory to create. All parent directories will be
            created if they don't exist. Can be a relative or absolute path.

    Raises:
        IOError: If the directory cannot be created (e.g., permission denied).
        PermissionError: If permission is denied.
        ValueError: If the path is invalid (empty string or contains null bytes).

    Example:
        ```python
        await create_dir_all("path/to/nested/directory")
        # Creates path/, path/to/, path/to/nested/, and path/to/nested/directory/
        ```

    See Also:
        - `create_dir()`: Create a single directory (parent must exist).
        - `remove_dir_all()`: Remove a directory and all its contents.
    """
    await create_dir_all_async(path)


async def remove_dir(path: str) -> None:
    """
    Remove an empty directory asynchronously.

    Removes a single empty directory. The directory must be empty - use
    `remove_dir_all()` to remove a directory and all its contents. All I/O
    operations execute outside the Python GIL using native Rust/Tokio,
    ensuring true async behavior and preventing event loop stalls.

    Args:
        path: Path to the directory to remove. Can be a relative or absolute path.

    Raises:
        FileNotFoundError: If the directory does not exist.
        IOError: If the directory is not empty or cannot be removed
            (e.g., permission denied).
        ValueError: If the path is invalid (empty string or contains null bytes).

    Example:
        ```python
        await remove_dir("empty_directory")
        # Directory is removed if it exists and is empty
        ```

    See Also:
        - `remove_dir_all()`: Remove a directory and all its contents.
        - `remove_file()`: Remove a file.
        - `create_dir()`: Create a directory.
    """
    await remove_dir_async(path)


async def remove_dir_all(path: str) -> None:
    """
    Remove a directory and all its contents asynchronously.

    Recursively removes a directory and all files and subdirectories within it.
    Equivalent to `rm -rf` in Unix. This operation is permanent and cannot be
    undone. All I/O operations execute outside the Python GIL using native
    Rust/Tokio, ensuring true async behavior and preventing event loop stalls.

    Warning: This function will delete all files and subdirectories within the
    specified directory. Use with caution.

    Args:
        path: Path to the directory to remove. Can be a relative or absolute path.

    Raises:
        FileNotFoundError: If the directory does not exist.
        IOError: If the directory cannot be removed (e.g., permission denied,
            files in use).
        ValueError: If the path is invalid (empty string or contains null bytes).

    Example:
        ```python
        await remove_dir_all("directory_to_remove")
        # Directory and all its contents are permanently deleted
        ```

    See Also:
        - `remove_dir()`: Remove an empty directory.
        - `remove_file()`: Remove a file.
    """
    await remove_dir_all_async(path)


async def list_dir(path: str) -> List[str]:
    """
    List directory contents asynchronously.

    Returns a list of file and directory names in the specified directory.
    The list contains only the names (not full paths) of items in the directory.
    All I/O operations execute outside the Python GIL using native Rust/Tokio,
    ensuring true async behavior and preventing event loop stalls.

    For recursive directory traversal, use `walk_dir()` instead.

    Args:
        path: Path to the directory to list. Can be a relative or absolute path.

    Returns:
        List[str]: List of file and directory names (strings). The order is
            not guaranteed and may vary between calls.

    Raises:
        FileNotFoundError: If the directory does not exist.
        IOError: If the directory cannot be read (e.g., permission denied).
        ValueError: If the path is invalid (empty string or contains null bytes).

    Example:
        ```python
        files = await list_dir(".")
        for name in files:
            print(name)
        # Output example: ['file1.txt', 'file2.txt', 'subdir']
        ```

    See Also:
        - `walk_dir()`: Recursively walk a directory tree.
        - `exists()`: Check if a path exists.
        - `is_file()`: Check if a path is a file.
        - `is_dir()`: Check if a path is a directory.
    """
    return await list_dir_async(path)


async def exists(path: str) -> bool:
    """
    Check if a path exists asynchronously.

    Returns True if the path exists (file or directory), False otherwise.
    This function does not distinguish between files and directories - use
    `is_file()` or `is_dir()` for that. All I/O operations execute outside
    the Python GIL using native Rust/Tokio, ensuring true async behavior
    and preventing event loop stalls.

    Args:
        path: Path to check. Can be a relative or absolute path.

    Returns:
        bool: True if the path exists, False otherwise.

    Raises:
        ValueError: If the path is invalid (empty string or contains null bytes).

    Example:
        ```python
        if await exists("file.txt"):
            print("File exists!")
        # Output: File exists! (if file exists)
        ```

    See Also:
        - `is_file()`: Check if a path is a file.
        - `is_dir()`: Check if a path is a directory.
        - `rapfiles.ospath.exists()`: Synchronous version (for path operations).
    """
    return await exists_async(path)


async def is_file(path: str) -> bool:
    """
    Check if a path is a file asynchronously.

    Returns True if the path exists and is a file, False otherwise. This
    function performs a filesystem check, so it requires the path to exist.
    All I/O operations execute outside the Python GIL using native Rust/Tokio,
    ensuring true async behavior and preventing event loop stalls.

    Args:
        path: Path to check. Can be a relative or absolute path.

    Returns:
        bool: True if the path exists and is a file, False otherwise (including
            if the path doesn't exist or is a directory).

    Raises:
        IOError: If the path cannot be checked (e.g., permission denied).
        ValueError: If the path is invalid (empty string or contains null bytes).

    Example:
        ```python
        if await is_file("file.txt"):
            print("It's a file!")
        # Output: It's a file! (if path exists and is a file)
        ```

    See Also:
        - `is_dir()`: Check if a path is a directory.
        - `exists()`: Check if a path exists (file or directory).
        - `rapfiles.ospath.isfile()`: Synchronous version (for path operations).
    """
    return await is_file_async(path)


async def is_dir(path: str) -> bool:
    """
    Check if a path is a directory asynchronously.

    Returns True if the path exists and is a directory, False otherwise. This
    function performs a filesystem check, so it requires the path to exist.
    All I/O operations execute outside the Python GIL using native Rust/Tokio,
    ensuring true async behavior and preventing event loop stalls.

    Args:
        path: Path to check. Can be a relative or absolute path.

    Returns:
        bool: True if the path exists and is a directory, False otherwise
            (including if the path doesn't exist or is a file).

    Raises:
        IOError: If the path cannot be checked (e.g., permission denied).
        ValueError: If the path is invalid (empty string or contains null bytes).

    Example:
        ```python
        if await is_dir("directory"):
            print("It's a directory!")
        # Output: It's a directory! (if path exists and is a directory)
        ```

    See Also:
        - `is_file()`: Check if a path is a file.
        - `exists()`: Check if a path exists (file or directory).
        - `rapfiles.ospath.isdir()`: Synchronous version (for path operations).
    """
    return await is_dir_async(path)


# Metadata operations
async def stat(path: str) -> "FileMetadata":
    """
    Get file or directory statistics asynchronously.

    Returns file metadata including size, timestamps, and type information.
    All I/O operations execute outside the Python GIL using native Rust/Tokio,
    ensuring true async behavior and preventing event loop stalls.

    The returned `FileMetadata` object is compatible with `aiofiles.stat_result`
    for drop-in replacement scenarios.

    Args:
        path: Path to the file or directory. Can be a relative or absolute path.

    Returns:
        FileMetadata: File metadata object with the following properties:
            - size (int): File size in bytes (0 for directories)
            - is_file (bool): True if path is a file
            - is_dir (bool): True if path is a directory
            - modified (float): Modification time as Unix timestamp (seconds since epoch)
            - accessed (float): Access time as Unix timestamp
            - created (float): Creation time as Unix timestamp (birth time on Unix,
              creation time on Windows)

    Raises:
        FileNotFoundError: If the path does not exist.
        IOError: If metadata cannot be retrieved (e.g., permission denied).
        ValueError: If the path is invalid (empty string or contains null bytes).

    Example:
        ```python
        meta = await stat("file.txt")
        print(f"Size: {meta.size} bytes")
        print(f"Is file: {meta.is_file}")
        print(f"Modified: {meta.modified}")
        # Output example:
        # Size: 12 bytes
        # Is file: True
        # Modified: 1768696716.4495575
        ```

    See Also:
        - `metadata()`: Alias for `stat()`.
        - `is_file()`: Check if a path is a file.
        - `is_dir()`: Check if a path is a directory.
    """
    return await stat_async(path)


async def metadata(path: str) -> "FileMetadata":
    """
    Get file metadata asynchronously (alias for stat).

    This is an alias for `stat()` function. Returns file metadata including
    size, timestamps, and type information. All I/O operations execute outside
    the Python GIL using native Rust/Tokio, ensuring true async behavior and
    preventing event loop stalls.

    Args:
        path: Path to the file or directory. Can be a relative or absolute path.

    Returns:
        FileMetadata: File metadata object with size, timestamps, and type
            information. See `stat()` for detailed property descriptions.

    Raises:
        FileNotFoundError: If the path does not exist.
        IOError: If metadata cannot be retrieved (e.g., permission denied).
        ValueError: If the path is invalid (empty string or contains null bytes).

    Example:
        ```python
        meta = await metadata("file.txt")
        print(f"Size: {meta.size} bytes")
        print(f"Is file: {meta.is_file}")
        # Output example:
        # Size: 12 bytes
        # Is file: True
        ```

    See Also:
        - `stat()`: Primary function for getting file metadata.
        - `is_file()`: Check if a path is a file.
        - `is_dir()`: Check if a path is a directory.
    """
    return await metadata_async(path)


# Directory traversal
async def walk_dir(path: str) -> List[Tuple[str, bool]]:
    """
    Recursively walk a directory tree asynchronously.

    Traverses a directory tree recursively and returns a list of all files
    and directories found. The traversal is depth-first. All I/O operations
    execute outside the Python GIL using native Rust/Tokio, ensuring true
    async behavior and preventing event loop stalls.

    Args:
        path: Directory path to walk. Can be a relative or absolute path.

    Returns:
        List[Tuple[str, bool]]: List of (path, is_file) tuples where:
            - path (str): Full path to the file or directory
            - is_file (bool): True if the path is a file, False if it's a directory

        The order of items is not guaranteed and may vary between calls.

    Raises:
        FileNotFoundError: If the directory does not exist.
        IOError: If the directory cannot be read (e.g., permission denied).
        ValueError: If the path is invalid (empty string or contains null bytes).

    Example:
        ```python
        for path, is_file in await walk_dir("."):
            if is_file:
                print(f"File: {path}")
            else:
                print(f"Directory: {path}")
        # Output example:
        # File: ./file1.txt
        # Directory: ./subdir
        # File: ./subdir/file2.txt
        ```

    See Also:
        - `list_dir()`: List contents of a single directory (non-recursive).
    """
    return await walk_dir_async(path)


# File manipulation operations
async def copy_file(src: str, dst: str) -> None:
    """
    Copy a file asynchronously.

    Copies a file from source to destination. If the destination file exists,
    it will be overwritten. The source file remains unchanged. All I/O
    operations execute outside the Python GIL using native Rust/Tokio,
    ensuring true async behavior and preventing event loop stalls.

    This operation preserves file permissions and metadata where possible.
    For atomic file operations, see `atomic_write_file()`.

    Args:
        src: Path to the source file. Can be a relative or absolute path.
        dst: Path to the destination file. Can be a relative or absolute path.
            Parent directories will not be created automatically.

    Raises:
        FileNotFoundError: If the source file does not exist.
        IOError: If the file cannot be copied (e.g., disk full, permission denied).
        ValueError: If any path is invalid (empty string or contains null bytes).

    Example:
        ```python
        await copy_file("source.txt", "destination.txt")
        # destination.txt now contains a copy of source.txt
        ```

    See Also:
        - `move_file()`: Move a file (removes source after copying).
        - `copy_files()`: Copy multiple files concurrently.
        - `atomic_write_file()`: Write file atomically.
    """
    await copy_file_async(src, dst)


async def move_file(src: str, dst: str) -> None:
    """
    Move or rename a file asynchronously.

    Moves a file from source to destination. This is an atomic operation when
    moving within the same filesystem (uses rename operation). For cross-device
    moves, it will copy the file and then remove the source file. The source
    file is removed after a successful move. All I/O operations execute outside
    the Python GIL using native Rust/Tokio, ensuring true async behavior and
    preventing event loop stalls.

    If the destination file exists, it will be overwritten. This operation
    preserves file permissions and metadata where possible.

    Args:
        src: Path to the source file. Can be a relative or absolute path.
        dst: Path to the destination file. Can be a relative or absolute path.
            Parent directories will not be created automatically.

    Raises:
        FileNotFoundError: If the source file does not exist.
        IOError: If the file cannot be moved (e.g., disk full, permission denied).
        ValueError: If any path is invalid (empty string or contains null bytes).

    Example:
        ```python
        await move_file("old_name.txt", "new_name.txt")
        # old_name.txt is now renamed to new_name.txt
        ```

    See Also:
        - `rename()`: Alias for `move_file()`.
        - `atomic_move_file()`: Move file atomically with additional safety.
        - `copy_file()`: Copy a file without removing the source.
    """
    await move_file_async(src, dst)


async def rename(src: str, dst: str) -> None:
    """
    Rename a file asynchronously (alias for move_file).

    This is an alias for `move_file()`. Renames a file from source to destination.
    The source file is removed after a successful rename. All I/O operations
    execute outside the Python GIL using native Rust/Tokio, ensuring true async
    behavior and preventing event loop stalls.

    Args:
        src: Path to the source file. Can be a relative or absolute path.
        dst: Path to the destination file. Can be a relative or absolute path.
            Parent directories will not be created automatically.

    Raises:
        FileNotFoundError: If the source file does not exist.
        IOError: If the file cannot be renamed (e.g., disk full, permission denied).
        ValueError: If any path is invalid (empty string or contains null bytes).

    Example:
        ```python
        await rename("old_name.txt", "new_name.txt")
        # old_name.txt is now renamed to new_name.txt
        ```

    See Also:
        - `move_file()`: Primary function for moving/renaming files.
        - `atomic_move_file()`: Atomic file move operation.
        - `copy_file()`: Copy a file without removing the source.
    """
    await move_file_async(src, dst)


async def remove_file(path: str) -> None:
    """
    Remove a file asynchronously.

    Deletes a file from the filesystem. This function only removes files, not
    directories. Use `remove_dir()` or `remove_dir_all()` for directories.
    All I/O operations execute outside the Python GIL using native Rust/Tokio,
    ensuring true async behavior and preventing event loop stalls.

    The file is permanently deleted and cannot be recovered (unless using
    filesystem-level recovery tools).

    Args:
        path: Path to the file to remove. Can be a relative or absolute path.

    Raises:
        FileNotFoundError: If the file does not exist.
        IOError: If the file cannot be removed (e.g., it's a directory,
            permission denied, or file is in use).
        ValueError: If the path is invalid (empty string or contains null bytes).

    Example:
        ```python
        await remove_file("file_to_delete.txt")
        # File is permanently deleted
        ```

    See Also:
        - `remove_dir()`: Remove an empty directory.
        - `remove_dir_all()`: Remove a directory and all its contents.
    """
    await remove_file_async(path)


async def hard_link(src: str, dst: str) -> None:
    """
    Create a hard link asynchronously.

    Creates a hard link from source to destination. Both files will refer
    to the same underlying file data. Changes to one file will be reflected
    in the other. Hard links only work within the same filesystem. All I/O
    operations execute outside the Python GIL using native Rust/Tokio,
    ensuring true async behavior and preventing event loop stalls.

    Note: Hard links cannot be created for directories on most filesystems.

    Args:
        src: Path to the source file. Can be a relative or absolute path.
        dst: Path to the destination link. Can be a relative or absolute path.

    Raises:
        FileNotFoundError: If the source file does not exist.
        IOError: If the link cannot be created (e.g., cross-filesystem link,
            permission denied, or destination already exists).
        ValueError: If any path is invalid (empty string or contains null bytes).

    Example:
        ```python
        await hard_link("original.txt", "link.txt")
        # Both files now refer to the same data
        ```

    See Also:
        - `symlink()`: Create a symbolic link (works across filesystems).
        - `copy_file()`: Create a copy of a file (independent data).
    """
    await hard_link_async(src, dst)


async def symlink(src: str, dst: str) -> None:
    """
    Create a symbolic link asynchronously.

    Creates a symbolic link from source to destination. The destination will
    point to the source path. Unlike hard links, symbolic links can point
    to files on different filesystems and can point to directories. All I/O
    operations execute outside the Python GIL using native Rust/Tokio,
    ensuring true async behavior and preventing event loop stalls.

    The source path can be relative or absolute. If relative, it's resolved
    relative to the symlink's directory.

    Args:
        src: Path that the symlink will point to. Can be a relative or absolute
            path. The path doesn't need to exist at creation time.
        dst: Path to the symbolic link to create. Can be a relative or absolute
            path. Parent directories will not be created automatically.

    Raises:
        IOError: If the symlink cannot be created (e.g., destination already
            exists, permission denied).
        ValueError: If any path is invalid (empty string or contains null bytes).

    Example:
        ```python
        await symlink("/path/to/original", "/path/to/link")
        # link now points to original
        ```

    See Also:
        - `hard_link()`: Create a hard link (same filesystem only).
        - `canonicalize()`: Resolve a symlink to its canonical path.
    """
    await symlink_async(src, dst)


async def canonicalize(path: str) -> str:
    """
    Canonicalize a path asynchronously.

    Resolves all symbolic links and returns the absolute path. This function
    resolves all intermediate symlinks in the path and normalizes relative
    components (e.g., '..' and '.'). All I/O operations execute outside the
    Python GIL using native Rust/Tokio, ensuring true async behavior and
    preventing event loop stalls.

    The path must exist for canonicalization to succeed. This is useful for
    getting the "real" path of a file, especially when dealing with symlinks.

    Args:
        path: Path to canonicalize. Can be a relative or absolute path.

    Returns:
        str: Canonical absolute path as a string. All symlinks are resolved
            and the path is normalized.

    Raises:
        FileNotFoundError: If the path does not exist.
        IOError: If the path cannot be canonicalized (e.g., broken symlink,
            permission denied).
        ValueError: If the path is invalid (empty string or contains null bytes).

    Example:
        ```python
        canonical_path = await canonicalize("./relative/path/../file.txt")
        print(canonical_path)  # /absolute/path/to/file.txt
        ```

    See Also:
        - `symlink()`: Create a symbolic link.
        - `rapfiles.ospath.abspath()`: Get absolute path without resolving symlinks.
    """
    return await canonicalize_async(path)


# Atomic file operations
async def atomic_write_file(path: str, contents: str) -> None:
    """
    Write a file atomically using a temporary file.

    Writes content to a temporary file first, then atomically replaces
    the target file by renaming. This ensures the target file is never
    in a partially-written state, making it safe for critical data writes
    (configuration files, databases, etc.). All I/O operations execute
    outside the Python GIL using native Rust/Tokio, ensuring true async
    behavior and preventing event loop stalls.

    If the process crashes during writing, the original file remains intact.
    The temporary file is created in the same directory as the target file.

    Args:
        path: Path to the file to write. Can be a relative or absolute path.
        contents: Content to write to the file. Will be encoded as UTF-8.

    Raises:
        IOError: If the file cannot be written (e.g., disk full, I/O error).
        PermissionError: If write permission is denied.
        ValueError: If the path is invalid (empty string or contains null bytes).

    Example:
        ```python
        await atomic_write_file("important.txt", "Critical data")
        # File is written atomically - never in a partial state
        ```

    See Also:
        - `write_file()`: Regular file write (may leave partial file on crash).
        - `atomic_write_file_bytes()`: Atomic write for binary data.
        - `atomic_move_file()`: Atomic file move operation.
    """
    await atomic_write_file_async(path, contents)


async def atomic_write_file_bytes(path: str, contents: bytes) -> None:
    """
    Write bytes to a file atomically using a temporary file.

    Writes bytes to a temporary file first, then atomically replaces
    the target file by renaming. This ensures the target file is never
    in a partially-written state, making it safe for critical binary data
    writes. All I/O operations execute outside the Python GIL using native
    Rust/Tokio, ensuring true async behavior and preventing event loop stalls.

    If the process crashes during writing, the original file remains intact.
    The temporary file is created in the same directory as the target file.

    Args:
        path: Path to the file to write. Can be a relative or absolute path.
        contents: Raw bytes to write to the file.

    Raises:
        IOError: If the file cannot be written (e.g., disk full, I/O error).
        PermissionError: If write permission is denied.
        ValueError: If the path is invalid (empty string or contains null bytes).

    Example:
        ```python
        await atomic_write_file_bytes("data.bin", b"\\x00\\x01\\x02")
        # File is written atomically - never in a partial state
        ```

    See Also:
        - `write_file_bytes()`: Regular file write (may leave partial file on crash).
        - `atomic_write_file()`: Atomic write for text data.
        - `atomic_move_file()`: Atomic file move operation.
    """
    await atomic_write_file_bytes_async(path, contents)


async def atomic_move_file(src: str, dst: str) -> None:
    """
    Move a file atomically.

    Moves a file from source to destination atomically. For same-filesystem
    moves, this uses an atomic rename operation. For cross-device moves,
    it will copy atomically (using a temporary file) and then remove the
    source. All I/O operations execute outside the Python GIL using native
    Rust/Tokio, ensuring true async behavior and preventing event loop stalls.

    This ensures the destination file is never in a partially-written state,
    making it safer than regular `move_file()` for critical operations.

    Args:
        src: Path to the source file. Can be a relative or absolute path.
        dst: Path to the destination file. Can be a relative or absolute path.
            Parent directories will not be created automatically.

    Raises:
        FileNotFoundError: If the source file does not exist.
        IOError: If the file cannot be moved (e.g., disk full, permission denied).
        ValueError: If any path is invalid (empty string or contains null bytes).

    Example:
        ```python
        await atomic_move_file("old_name.txt", "new_name.txt")
        # File is moved atomically - never in a partial state
        ```

    See Also:
        - `move_file()`: Regular file move (may leave partial file on crash).
        - `atomic_write_file()`: Atomic file write operation.
    """
    await atomic_move_file_async(src, dst)


# File locking operations
class _LockContextManager:
    """Internal async context manager wrapper for lock_file."""

    def __init__(self, coro: Coroutine[Any, Any, "FileLock"]) -> None:
        self._coro: Coroutine[Any, Any, "FileLock"] = coro
        self._lock: Optional["FileLock"] = None

    async def __aenter__(self) -> "FileLock":
        self._lock = await self._coro
        return self._lock.__aenter__()

    async def __aexit__(
        self,
        exc_type: Optional[Type[BaseException]],
        exc_val: Optional[BaseException],
        exc_tb: Optional[TracebackType],
    ) -> Optional[bool]:
        if self._lock:
            return await self._lock.__aexit__(exc_type, exc_val, exc_tb)
        return None


def lock_file(path: str, exclusive: bool = True) -> _LockContextManager:
    """
    Lock a file asynchronously with advisory file locking.

    Acquires an advisory file lock on the specified file. The lock can be
    shared (read) or exclusive (write). The file is created if it doesn't
    exist. All I/O operations execute outside the Python GIL using native
    Rust/Tokio, ensuring true async behavior and preventing event loop stalls.

    Advisory locks only work if all processes respect them - they don't
    prevent file access, only coordinate it. Use exclusive locks for writing
    and shared locks for reading.

    Args:
        path: Path to the file to lock. Can be a relative or absolute path.
        exclusive: If True, acquire exclusive (write) lock; if False, acquire
            shared (read) lock. Defaults to True.

    Returns:
        _LockContextManager: An async context manager that yields a `FileLock`
            object. Use with `async with` syntax.

    Raises:
        IOError: If the file cannot be locked (e.g., lock already held).
        ValueError: If the path is invalid (empty string or contains null bytes).

    Example:
        ```python
        # Cross-platform pattern: Release lock before writing
        async with lock_file("file.txt", exclusive=True) as lock:
            # File is locked here - only this process can acquire exclusive lock
            # Read operations work on all platforms
            pass
        # Lock released - now write safely (required on Windows)
        await write_file("file.txt", "content")
        
        # Alternative: Use atomic_write_file which handles locking internally
        async with lock_file("file.txt", exclusive=True):
            # Read and prepare data while holding lock
            pass
        await atomic_write_file("file.txt", "content")
        ```
        
    Note:
        On Windows, you cannot write to a file through a different handle
        (like `write_file()`) while holding an exclusive lock. Release the
        lock first, or use `atomic_write_file()` for atomic operations.

    See Also:
        - `lock_file_shared()`: Convenience function for shared locks.
        - `atomic_write_file()`: Atomic writes for data integrity.
    """
    coro = lock_file_async(path, exclusive)
    return _LockContextManager(coro)


def lock_file_shared(path: str) -> _LockContextManager:
    """
    Lock a file with shared (read) lock asynchronously.

    Convenience function for acquiring a shared lock. Equivalent to
    `lock_file(path, exclusive=False)`. Multiple processes can hold shared
    locks simultaneously, but an exclusive lock will block all shared locks.
    All I/O operations execute outside the Python GIL using native Rust/Tokio,
    ensuring true async behavior and preventing event loop stalls.

    Use shared locks when multiple readers need concurrent access to a file.
    For writing, use `lock_file()` with `exclusive=True`.

    Args:
        path: Path to the file to lock. Can be a relative or absolute path.

    Returns:
        _LockContextManager: An async context manager that yields a `FileLock`
            object. Use with `async with` syntax.

    Raises:
        IOError: If the file cannot be locked (e.g., exclusive lock already held).
        ValueError: If the path is invalid (empty string or contains null bytes).

    Example:
        ```python
        async with lock_file_shared("file.txt") as lock:
            # File has shared lock - multiple readers can access simultaneously
            content = await read_file("file.txt")
        # Lock is automatically released when exiting the context
        ```

    See Also:
        - `lock_file()`: Lock a file with exclusive or shared lock.
        - `atomic_write_file()`: Atomic writes for data integrity.
    """
    coro = lock_file_async(path, exclusive=False)
    return _LockContextManager(coro)


# Batch operations
async def read_files(paths: List[str]) -> List[Tuple[str, bytes]]:
    """
    Read multiple files concurrently.

    Reads all specified files concurrently and returns their contents as a
    list of tuples. All files are read in parallel, significantly improving
    performance when processing many files. All I/O operations execute outside
    the Python GIL using native Rust/Tokio, ensuring true async behavior and
    preventing event loop stalls.

    Args:
        paths: List of file paths to read. Can contain relative or absolute paths.

    Returns:
        List[Tuple[str, bytes]]: List of (path, bytes) tuples where:
            - path (str): The file path (same as input)
            - bytes (bytes): The file contents as raw bytes

        The order of results matches the order of input paths.

    Raises:
        FileNotFoundError: If any file does not exist.
        IOError: If any file cannot be read (e.g., permission denied).
        ValueError: If any path is invalid (empty string or contains null bytes).

    Example:
        ```python
        files = await read_files(["file1.txt", "file2.txt", "file3.txt"])
        for path, content in files:
            print(f"{path}: {len(content)} bytes")
        # Output example:
        # file1.txt: 12 bytes
        # file2.txt: 15 bytes
        # file3.txt: 8 bytes
        ```

    See Also:
        - `read_files_dict()`: Read files and return as dictionary.
        - `read_file()`: Read a single file.
        - `read_file_bytes()`: Read a single file as bytes.
    """
    results = await read_files_async(paths)
    # Convert results to list of (path, bytes) tuples, raising on error
    output = []
    for path, result in results:
        if isinstance(result, bytes):
            output.append((path, result))
        elif isinstance(result, str):
            raise IOError(result)
        elif isinstance(result, Exception):
            raise result
        else:
            output.append((path, result))
    return output


async def read_files_dict(paths: List[str]) -> Dict[str, bytes]:
    """
    Read multiple files concurrently and return as dictionary.

    Reads all specified files concurrently and returns their contents as a
    dictionary mapping paths to contents. This is a convenience wrapper around
    `read_files()` that returns a dictionary instead of a list of tuples.
    All I/O operations execute outside the Python GIL using native Rust/Tokio,
    ensuring true async behavior and preventing event loop stalls.

    Args:
        paths: List of file paths to read. Can contain relative or absolute paths.

    Returns:
        Dict[str, bytes]: Dictionary mapping file paths (str) to their contents
            (bytes). Keys are the same as the input paths.

    Raises:
        FileNotFoundError: If any file does not exist.
        IOError: If any file cannot be read (e.g., permission denied).
        ValueError: If any path is invalid (empty string or contains null bytes).

    Example:
        ```python
        files = await read_files_dict(["file1.txt", "file2.txt"])
        print(files["file1.txt"])  # b"content"
        # Access files by path: files["file1.txt"]
        ```

    See Also:
        - `read_files()`: Read files and return as list of tuples.
        - `read_file()`: Read a single file.
    """
    results = await read_files(paths)
    return dict(results)


async def write_files(files: Dict[str, bytes]) -> None:
    """
    Write multiple files concurrently.

    Writes contents to all specified files concurrently. All files are written
    in parallel, significantly improving performance when processing many files.
    If a destination file exists, it will be overwritten. All I/O operations
    execute outside the Python GIL using native Rust/Tokio, ensuring true async
    behavior and preventing event loop stalls.

    Args:
        files: Dictionary mapping file paths (str) to their contents (bytes).
            Keys are file paths, values are the bytes to write.

    Raises:
        IOError: If any file cannot be written (e.g., disk full, I/O error).
        PermissionError: If write permission is denied for any file.
        ValueError: If any path is invalid (empty string or contains null bytes).

    Example:
        ```python
        files = {
            "file1.txt": b"content1",
            "file2.txt": b"content2",
        }
        await write_files(files)
        # All files are written concurrently
        ```

    See Also:
        - `write_file()`: Write a single file.
        - `write_file_bytes()`: Write a single file as bytes.
        - `read_files_dict()`: Read multiple files as dictionary.
    """
    # Convert dict to list of (path, bytes) tuples for Rust function
    # PyO3 will automatically convert Python bytes to Vec<u8>
    files_list = [(path, contents) for path, contents in files.items()]
    results = await write_files_async(files_list)

    # Check for errors
    for path, result in results:
        if isinstance(result, str):
            raise IOError(result)


async def copy_files(files: List[Tuple[str, str]]) -> None:
    """
    Copy multiple files concurrently.

    Copies all specified files concurrently. All files are copied in parallel,
    significantly improving performance when processing many files. If a
    destination file exists, it will be overwritten. All I/O operations execute
    outside the Python GIL using native Rust/Tokio, ensuring true async behavior
    and preventing event loop stalls.

    Args:
        files: List of (src, dst) tuples where:
            - src (str): Path to the source file
            - dst (str): Path to the destination file

    Raises:
        FileNotFoundError: If any source file does not exist.
        IOError: If any file cannot be copied (e.g., disk full, permission denied).
        ValueError: If any path is invalid (empty string or contains null bytes).

    Example:
        ```python
        files = [
            ("source1.txt", "dest1.txt"),
            ("source2.txt", "dest2.txt"),
        ]
        await copy_files(files)
        # All files are copied concurrently
        ```

    See Also:
        - `copy_file()`: Copy a single file.
        - `move_file()`: Move a file (removes source).
    """
    results = await copy_files_async(files)

    # Check for errors
    for src, dst, result in results:
        if isinstance(result, str):
            raise IOError(result)


# Type variable for the return type of open()
_T = TypeVar("_T", bound="AsyncFile")

# Forward declarations for type checking
if TYPE_CHECKING:

    class _OpenContextManagerProtocol(Protocol):
        async def __aenter__(self) -> Union["_TextModeWrapperProtocol", AsyncFile]: ...
        async def __aexit__(
            self,
            exc_type: Optional[Type[BaseException]],
            exc_val: Optional[BaseException],
            exc_tb: Optional[TracebackType],
        ) -> Optional[bool]: ...
        def __await__(self) -> Any: ...

    class _TextModeWrapperProtocol(Protocol):
        async def read(self, size: int = -1) -> str: ...
        async def readline(self, size: int = -1) -> str: ...
        async def readlines(self, hint: int = -1) -> List[str]: ...


# aiofiles.open() compatible function
def open(
    file: Union[str, bytes],
    mode: str = "r",
    buffering: int = -1,
    encoding: Optional[str] = None,
    errors: Optional[str] = None,
    newline: Optional[str] = None,
    closefd: bool = True,
    opener: Optional[Any] = None,
) -> Any:  # Returns _OpenContextManager (internal type)
    """
    Open a file asynchronously (aiofiles.open() compatible).

    Opens a file and returns an async file handle that can be used with async
    context managers. This function is compatible with `aiofiles.open()` API,
    making it a drop-in replacement. All I/O operations execute outside the
    Python GIL using native Rust/Tokio, ensuring true async behavior and
    preventing event loop stalls.

    Args:
        file: Path to the file. Can be a string or bytes (bytes are decoded to UTF-8).
        mode: File mode string. Supported modes:
            - 'r', 'r+': Read mode (text)
            - 'w', 'w+': Write mode (text, truncates existing file)
            - 'a', 'a+': Append mode (text)
            - 'rb', 'rb+': Read mode (binary)
            - 'wb', 'wb+': Write mode (binary, truncates existing file)
            - 'ab', 'ab+': Append mode (binary)
        buffering: Buffer size. Currently not implemented, accepted for API
            compatibility. Defaults to -1.
        encoding: Text encoding. Currently not implemented (always UTF-8),
            accepted for API compatibility.
        errors: Error handling. Currently not implemented, accepted for API
            compatibility.
        newline: Newline handling. Currently not implemented, accepted for
            API compatibility.
        closefd: Close file descriptor. Currently not implemented, accepted
            for API compatibility. Defaults to True.
        opener: Custom opener. Currently not implemented, accepted for API
            compatibility.

    Returns:
        _OpenContextManager: An async context manager that yields an `AsyncFile`
            instance (or `_TextModeWrapper` for text mode). Use with `async with`
            syntax.

    Raises:
        FileNotFoundError: If the file does not exist (read modes).
        IOError: If the file cannot be opened (e.g., permission denied).
        ValueError: If the path is invalid (empty string or contains null bytes)
            or if the mode is invalid.

    Example:
        ```python
        # Text mode
        async with open("file.txt", "r") as f:
            content = await f.read()
            print(content)

        # Binary mode
        async with open("image.png", "rb") as f:
            data = await f.read()

        # Write mode
        async with open("output.txt", "w") as f:
            await f.write("Hello, world!")
        ```

    See Also:
        - `read_file()`: Read entire file as string.
        - `read_file_bytes()`: Read entire file as bytes.
        - `write_file()`: Write entire file as string.
    """
    if isinstance(file, bytes):
        file = file.decode("utf-8")

    # Create an awaitable wrapper that implements async context manager protocol
    # and handles text/binary mode conversion
    class _OpenContextManager:
        """Internal context manager wrapper for async file opening."""

        def __init__(
            self,
            coro: Coroutine[Any, Any, AsyncFile],
            file_mode: str,
        ) -> None:
            self._coro: Coroutine[Any, Any, AsyncFile] = coro
            self._file: Optional[AsyncFile] = None
            self._is_binary: bool = "b" in file_mode

        def __await__(self) -> Any:
            return self._coro.__await__()

        async def __aenter__(self) -> Union["_TextModeWrapper", AsyncFile]:
            self._file = await self._coro
            # __aenter__ returns self directly, no need to await
            file_obj = self._file.__aenter__()

            # Wrap the file object to handle text/binary mode
            # Note: file_obj is already the AsyncFile instance (__aenter__ returns self)
            if not self._is_binary:
                return _TextModeWrapper(file_obj)
            return file_obj

        async def __aexit__(
            self,
            exc_type: Optional[Type[BaseException]],
            exc_val: Optional[BaseException],
            exc_tb: Optional[TracebackType],
        ) -> Optional[bool]:
            if self._file is None:
                self._file = await self._coro
            # __aexit__ returns a coroutine/future, need to await it
            result = self._file.__aexit__(exc_type, exc_val, exc_tb)
            if hasattr(result, "__await__"):
                return await result  # type: ignore[misc]
            return result  # type: ignore[return-value]

    # Wrapper class to handle text mode decoding
    class _TextModeWrapper:
        """Internal wrapper to decode bytes to strings for text mode files."""

        def __init__(self, file_obj: AsyncFile) -> None:
            self._file: AsyncFile = file_obj

        async def read(self, size: int = -1) -> str:
            """Read and decode bytes to string for text mode."""
            result: Union[str, bytes] = await self._file.read(size)
            if isinstance(result, bytes):
                return result.decode("utf-8")
            return result  # type: ignore[return-value]

        async def readline(self, size: int = -1) -> str:
            """Read a line and decode bytes to string for text mode."""
            result: Union[str, bytes] = await self._file.readline(size)
            if isinstance(result, bytes):
                return result.decode("utf-8")
            return result  # type: ignore[return-value]

        async def readlines(self, hint: int = -1) -> List[str]:
            """Read all lines and decode bytes to strings for text mode."""
            result: Union[List[str], List[bytes]] = await self._file.readlines(hint)
            if isinstance(result, list) and result and isinstance(result[0], bytes):
                return [
                    line.decode("utf-8") if isinstance(line, bytes) else line
                    for line in result
                ]  # type: ignore[misc,return-value]
            return result  # type: ignore[return-value]

        def __getattr__(self, name: str) -> Any:
            # Delegate all other attributes to the underlying file
            return getattr(self._file, name)

    coro = open_file(file, mode, buffering, encoding, errors, newline, closefd, opener)
    return _OpenContextManager(coro, mode)
