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

__version__: str = "0.2.0"
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
    native Rust/Tokio, ensuring true async behavior.

    Args:
        path: Path to the file to read

    Returns:
        File contents as a UTF-8 decoded string

    Raises:
        FileNotFoundError: If the file does not exist
        IOError: If the file cannot be read
        ValueError: If the path is invalid (empty or contains null bytes)

    Example:
        ```python
        content = await read_file("example.txt")
        print(content)
        ```
    """
    return await read_file_async(path)


async def write_file(path: str, contents: str) -> None:
    """
    Write a file asynchronously using true async I/O.

    This function writes the entire contents to a file. If the file exists,
    it will be overwritten. All I/O operations execute outside the Python GIL
    using native Rust/Tokio, ensuring true async behavior.

    Args:
        path: Path to the file to write
        contents: Content to write to the file (will be encoded as UTF-8)

    Raises:
        IOError: If the file cannot be written
        PermissionError: If write permission is denied
        ValueError: If the path is invalid (empty or contains null bytes)

    Example:
        ```python
        await write_file("example.txt", "Hello, world!")
        ```
    """
    await write_file_async(path, contents)


async def read_file_bytes(path: str) -> bytes:
    """
    Read a file asynchronously as bytes.

    This function reads the entire file and returns its contents as raw bytes.
    All I/O operations execute outside the Python GIL using native Rust/Tokio,
    ensuring true async behavior.

    Args:
        path: Path to the file to read

    Returns:
        File contents as raw bytes

    Raises:
        FileNotFoundError: If the file does not exist
        IOError: If the file cannot be read
        ValueError: If the path is invalid (empty or contains null bytes)

    Example:
        ```python
        data = await read_file_bytes("image.png")
        ```
    """
    return await read_file_bytes_async(path)


async def write_file_bytes(path: str, contents: bytes) -> None:
    """
    Write bytes to a file asynchronously.

    This function writes raw bytes to a file. If the file exists, it will be
    overwritten. All I/O operations execute outside the Python GIL using
    native Rust/Tokio, ensuring true async behavior.

    Args:
        path: Path to the file to write
        contents: Bytes to write to the file

    Raises:
        IOError: If the file cannot be written
        PermissionError: If write permission is denied
        ValueError: If the path is invalid (empty or contains null bytes)

    Example:
        ```python
        await write_file_bytes("data.bin", b"\\x00\\x01\\x02")
        ```
    """
    await write_file_bytes_async(path, contents)


async def append_file(path: str, contents: str) -> None:
    """
    Append to a file asynchronously.

    This function appends content to the end of a file. If the file does not
    exist, it will be created. All I/O operations execute outside the Python
    GIL using native Rust/Tokio, ensuring true async behavior.

    Args:
        path: Path to the file to append to
        contents: Content to append to the file (will be encoded as UTF-8)

    Raises:
        IOError: If the file cannot be written
        PermissionError: If write permission is denied
        ValueError: If the path is invalid (empty or contains null bytes)

    Example:
        ```python
        await append_file("log.txt", "New log entry\\n")
        ```
    """
    await append_file_async(path, contents)


# Directory operations
async def create_dir(path: str) -> None:
    """
    Create a directory asynchronously.

    Creates a single directory. Parent directories must already exist.
    All I/O operations execute outside the Python GIL using native Rust/Tokio.

    Args:
        path: Path to the directory to create

    Raises:
        FileExistsError: If the directory already exists
        IOError: If the directory cannot be created
        ValueError: If the path is invalid (empty or contains null bytes)

    Example:
        ```python
        await create_dir("new_directory")
        ```
    """
    await create_dir_async(path)


async def create_dir_all(path: str) -> None:
    """
    Create a directory and all parent directories asynchronously.

    Creates a directory and any necessary parent directories. Equivalent to
    `mkdir -p` in Unix. All I/O operations execute outside the Python GIL
    using native Rust/Tokio.

    Args:
        path: Path to the directory to create (with parents)

    Raises:
        IOError: If the directory cannot be created
        ValueError: If the path is invalid (empty or contains null bytes)

    Example:
        ```python
        await create_dir_all("path/to/nested/directory")
        ```
    """
    await create_dir_all_async(path)


async def remove_dir(path: str) -> None:
    """
    Remove an empty directory asynchronously.

    Removes a single empty directory. The directory must be empty.
    All I/O operations execute outside the Python GIL using native Rust/Tokio.

    Args:
        path: Path to the directory to remove

    Raises:
        FileNotFoundError: If the directory does not exist
        IOError: If the directory is not empty or cannot be removed
        ValueError: If the path is invalid (empty or contains null bytes)

    Example:
        ```python
        await remove_dir("empty_directory")
        ```
    """
    await remove_dir_async(path)


async def remove_dir_all(path: str) -> None:
    """
    Remove a directory and all its contents asynchronously.

    Recursively removes a directory and all files and subdirectories within it.
    Equivalent to `rm -rf` in Unix. All I/O operations execute outside the
    Python GIL using native Rust/Tokio.

    Args:
        path: Path to the directory to remove

    Raises:
        FileNotFoundError: If the directory does not exist
        IOError: If the directory cannot be removed
        ValueError: If the path is invalid (empty or contains null bytes)

    Example:
        ```python
        await remove_dir_all("directory_to_remove")
        ```
    """
    await remove_dir_all_async(path)


async def list_dir(path: str) -> List[str]:
    """
    List directory contents asynchronously.

    Returns a list of file and directory names in the specified directory.
    All I/O operations execute outside the Python GIL using native Rust/Tokio.

    Args:
        path: Path to the directory to list

    Returns:
        List of file and directory names (strings)

    Raises:
        FileNotFoundError: If the directory does not exist
        IOError: If the directory cannot be read
        ValueError: If the path is invalid (empty or contains null bytes)

    Example:
        ```python
        files = await list_dir(".")
        for name in files:
            print(name)
        ```
    """
    return await list_dir_async(path)


async def exists(path: str) -> bool:
    """
    Check if a path exists asynchronously.

    Returns True if the path exists (file or directory), False otherwise.
    All I/O operations execute outside the Python GIL using native Rust/Tokio.

    Args:
        path: Path to check

    Returns:
        True if the path exists, False otherwise

    Raises:
        ValueError: If the path is invalid (empty or contains null bytes)

    Example:
        ```python
        if await exists("file.txt"):
            print("File exists!")
        ```
    """
    return await exists_async(path)


async def is_file(path: str) -> bool:
    """
    Check if a path is a file asynchronously.

    Returns True if the path exists and is a file, False otherwise.
    All I/O operations execute outside the Python GIL using native Rust/Tokio.

    Args:
        path: Path to check

    Returns:
        True if the path is a file, False otherwise

    Raises:
        IOError: If the path does not exist
        ValueError: If the path is invalid (empty or contains null bytes)

    Example:
        ```python
        if await is_file("file.txt"):
            print("It's a file!")
        ```
    """
    return await is_file_async(path)


async def is_dir(path: str) -> bool:
    """
    Check if a path is a directory asynchronously.

    Returns True if the path exists and is a directory, False otherwise.
    All I/O operations execute outside the Python GIL using native Rust/Tokio.

    Args:
        path: Path to check

    Returns:
        True if the path is a directory, False otherwise

    Raises:
        IOError: If the path does not exist
        ValueError: If the path is invalid (empty or contains null bytes)

    Example:
        ```python
        if await is_dir("directory"):
            print("It's a directory!")
        ```
    """
    return await is_dir_async(path)


# Metadata operations
async def stat(path: str) -> "FileMetadata":
    """
    Get file statistics asynchronously.

    Returns file metadata including size, timestamps, and type information.
    All I/O operations execute outside the Python GIL using native Rust/Tokio.

    Args:
        path: Path to the file or directory

    Returns:
        FileMetadata object with the following properties:
        - size: File size in bytes
        - is_file: True if path is a file
        - is_dir: True if path is a directory
        - modified: Modification time as Unix timestamp (float)
        - accessed: Access time as Unix timestamp (float)
        - created: Creation time as Unix timestamp (float)

    Raises:
        FileNotFoundError: If the path does not exist
        IOError: If metadata cannot be retrieved
        ValueError: If the path is invalid (empty or contains null bytes)

    Example:
        ```python
        meta = await stat("file.txt")
        print(f"Size: {meta.size} bytes")
        print(f"Modified: {meta.modified}")
        ```
    """
    return await stat_async(path)


async def metadata(path: str) -> "FileMetadata":
    """
    Get file metadata asynchronously (alias for stat).

    This is an alias for `stat()` function. Returns file metadata including
    size, timestamps, and type information. All I/O operations execute outside
    the Python GIL using native Rust/Tokio.

    Args:
        path: Path to the file or directory

    Returns:
        FileMetadata object with size, timestamps, and type information

    Raises:
        FileNotFoundError: If the path does not exist
        IOError: If metadata cannot be retrieved
        ValueError: If the path is invalid (empty or contains null bytes)

    Example:
        ```python
        meta = await metadata("file.txt")
        print(f"Size: {meta.size} bytes")
        ```
    """
    return await metadata_async(path)


# Directory traversal
async def walk_dir(path: str) -> List[Tuple[str, bool]]:
    """
    Recursively walk a directory asynchronously.

    Traverses a directory tree recursively and returns a list of all files
    and directories found. All I/O operations execute outside the Python GIL
    using native Rust/Tokio, ensuring true async behavior.

    Args:
        path: Directory path to walk

    Returns:
        List of (path, is_file) tuples where:
        - path: Full path to the file or directory
        - is_file: True if the path is a file, False if it's a directory

    Raises:
        FileNotFoundError: If the directory does not exist
        IOError: If the directory cannot be read
        ValueError: If the path is invalid (empty or contains null bytes)

    Example:
        ```python
        for path, is_file in await walk_dir("."):
            if is_file:
                print(f"File: {path}")
            else:
                print(f"Directory: {path}")
        ```
    """
    return await walk_dir_async(path)


# File manipulation operations
async def copy_file(src: str, dst: str) -> None:
    """
    Copy a file asynchronously.

    Copies a file from source to destination. If the destination file exists,
    it will be overwritten. All I/O operations execute outside the Python GIL
    using native Rust/Tokio, ensuring true async behavior.

    Args:
        src: Path to the source file
        dst: Path to the destination file

    Raises:
        FileNotFoundError: If the source file does not exist
        IOError: If the file cannot be copied
        ValueError: If the path is invalid (empty or contains null bytes)

    Example:
        ```python
        await copy_file("source.txt", "destination.txt")
        ```
    """
    await copy_file_async(src, dst)


async def move_file(src: str, dst: str) -> None:
    """
    Move or rename a file asynchronously.

    Moves a file from source to destination. This is an atomic operation when
    moving within the same filesystem. For cross-device moves, it will copy
    and then remove the source file. All I/O operations execute outside the
    Python GIL using native Rust/Tokio, ensuring true async behavior.

    Args:
        src: Path to the source file
        dst: Path to the destination file

    Raises:
        FileNotFoundError: If the source file does not exist
        IOError: If the file cannot be moved
        ValueError: If the path is invalid (empty or contains null bytes)

    Example:
        ```python
        await move_file("old_name.txt", "new_name.txt")
        ```
    """
    await move_file_async(src, dst)


async def rename(src: str, dst: str) -> None:
    """
    Rename a file asynchronously (alias for move_file).

    This is an alias for `move_file()`. Renames a file from source to destination.
    All I/O operations execute outside the Python GIL using native Rust/Tokio,
    ensuring true async behavior.

    Args:
        src: Path to the source file
        dst: Path to the destination file

    Raises:
        FileNotFoundError: If the source file does not exist
        IOError: If the file cannot be renamed
        ValueError: If the path is invalid (empty or contains null bytes)

    Example:
        ```python
        await rename("old_name.txt", "new_name.txt")
        ```
    """
    await move_file_async(src, dst)


async def remove_file(path: str) -> None:
    """
    Remove a file asynchronously.

    Deletes a file from the filesystem. This will not remove directories.
    All I/O operations execute outside the Python GIL using native Rust/Tokio,
    ensuring true async behavior.

    Args:
        path: Path to the file to remove

    Raises:
        FileNotFoundError: If the file does not exist
        IOError: If the file cannot be removed (e.g., if it's a directory)
        ValueError: If the path is invalid (empty or contains null bytes)

    Example:
        ```python
        await remove_file("file_to_delete.txt")
        ```
    """
    await remove_file_async(path)


async def hard_link(src: str, dst: str) -> None:
    """
    Create a hard link asynchronously.

    Creates a hard link from source to destination. Both files will refer
    to the same underlying file data. All I/O operations execute outside
    the Python GIL using native Rust/Tokio, ensuring true async behavior.

    Args:
        src: Path to the source file
        dst: Path to the destination link

    Raises:
        FileNotFoundError: If the source file does not exist
        IOError: If the link cannot be created
        ValueError: If the path is invalid (empty or contains null bytes)

    Example:
        ```python
        await hard_link("original.txt", "link.txt")
        ```
    """
    await hard_link_async(src, dst)


async def symlink(src: str, dst: str) -> None:
    """
    Create a symbolic link asynchronously.

    Creates a symbolic link from source to destination. The destination
    will point to the source path. All I/O operations execute outside
    the Python GIL using native Rust/Tokio, ensuring true async behavior.

    Args:
        src: Path that the symlink will point to
        dst: Path to the symbolic link to create

    Raises:
        IOError: If the symlink cannot be created
        ValueError: If the path is invalid (empty or contains null bytes)

    Example:
        ```python
        await symlink("/path/to/original", "/path/to/link")
        ```
    """
    await symlink_async(src, dst)


async def canonicalize(path: str) -> str:
    """
    Canonicalize a path asynchronously.

    Resolves all symbolic links and returns the absolute path. All I/O
    operations execute outside the Python GIL using native Rust/Tokio,
    ensuring true async behavior.

    Args:
        path: Path to canonicalize

    Returns:
        Canonical absolute path as a string

    Raises:
        FileNotFoundError: If the path does not exist
        IOError: If the path cannot be canonicalized
        ValueError: If the path is invalid (empty or contains null bytes)

    Example:
        ```python
        canonical_path = await canonicalize("./relative/path/../file.txt")
        print(canonical_path)  # /absolute/path/to/file.txt
        ```
    """
    return await canonicalize_async(path)


# Atomic file operations
async def atomic_write_file(path: str, contents: str) -> None:
    """
    Write a file atomically using a temporary file.

    Writes content to a temporary file first, then atomically replaces
    the target file by renaming. This ensures the target file is never
    in a partially-written state. All I/O operations execute outside
    the Python GIL using native Rust/Tokio, ensuring true async behavior.

    Args:
        path: Path to the file to write
        contents: Content to write to the file (will be encoded as UTF-8)

    Raises:
        IOError: If the file cannot be written
        PermissionError: If write permission is denied
        ValueError: If the path is invalid (empty or contains null bytes)

    Example:
        ```python
        await atomic_write_file("important.txt", "Critical data")
        ```
    """
    await atomic_write_file_async(path, contents)


async def atomic_write_file_bytes(path: str, contents: bytes) -> None:
    """
    Write bytes to a file atomically using a temporary file.

    Writes bytes to a temporary file first, then atomically replaces
    the target file by renaming. This ensures the target file is never
    in a partially-written state. All I/O operations execute outside
    the Python GIL using native Rust/Tokio, ensuring true async behavior.

    Args:
        path: Path to the file to write
        contents: Bytes to write to the file

    Raises:
        IOError: If the file cannot be written
        PermissionError: If write permission is denied
        ValueError: If the path is invalid (empty or contains null bytes)

    Example:
        ```python
        await atomic_write_file_bytes("data.bin", b"\\x00\\x01\\x02")
        ```
    """
    await atomic_write_file_bytes_async(path, contents)


async def atomic_move_file(src: str, dst: str) -> None:
    """
    Move a file atomically.

    Moves a file from source to destination atomically. For cross-device
    moves, it will copy atomically and then remove the source. All I/O
    operations execute outside the Python GIL using native Rust/Tokio,
    ensuring true async behavior.

    Args:
        src: Path to the source file
        dst: Path to the destination file

    Raises:
        FileNotFoundError: If the source file does not exist
        IOError: If the file cannot be moved
        ValueError: If the path is invalid (empty or contains null bytes)

    Example:
        ```python
        await atomic_move_file("old_name.txt", "new_name.txt")
        ```
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
    Lock a file asynchronously.

    Acquires an advisory file lock on the specified file. The lock can be
    shared (read) or exclusive (write). The file is created if it doesn't
    exist. All I/O operations execute outside the Python GIL using native
    Rust/Tokio, ensuring true async behavior.

    Args:
        path: Path to the file to lock
        exclusive: If True, acquire exclusive (write) lock; if False, acquire shared (read) lock

    Returns:
        FileLock: A file lock object that can be used as an async context manager

    Raises:
        IOError: If the file cannot be locked
        ValueError: If the path is invalid (empty or contains null bytes)

    Example:
        ```python
        async with lock_file("file.txt", exclusive=True) as lock:
            # File is locked here
            await write_file("file.txt", "content")
        # Lock is automatically released
        ```
    """
    coro = lock_file_async(path, exclusive)
    return _LockContextManager(coro)


def lock_file_shared(path: str) -> _LockContextManager:
    """
    Lock a file with shared (read) lock asynchronously.

    Convenience function for acquiring a shared lock. Equivalent to
    `lock_file(path, exclusive=False)`. All I/O operations execute outside
    the Python GIL using native Rust/Tokio, ensuring true async behavior.

    Args:
        path: Path to the file to lock

    Returns:
        FileLock: A file lock object that can be used as an async context manager

    Raises:
        IOError: If the file cannot be locked
        ValueError: If the path is invalid (empty or contains null bytes)

    Example:
        ```python
        async with lock_file_shared("file.txt") as lock:
            # File has shared lock - multiple readers can access
            content = await read_file("file.txt")
        # Lock is automatically released
        ```
    """
    coro = lock_file_async(path, exclusive=False)
    return _LockContextManager(coro)


# Batch operations
async def read_files(paths: List[str]) -> List[Tuple[str, bytes]]:
    """
    Read multiple files concurrently.

    Reads all specified files concurrently and returns their contents.
    All I/O operations execute outside the Python GIL using native Rust/Tokio,
    ensuring true async behavior.

    Args:
        paths: List of file paths to read

    Returns:
        List of (path, bytes) tuples where:
        - path: The file path
        - bytes: The file contents as bytes, or raises exception on error

    Raises:
        FileNotFoundError: If any file does not exist
        IOError: If any file cannot be read
        ValueError: If any path is invalid (empty or contains null bytes)

    Example:
        ```python
        files = await read_files(["file1.txt", "file2.txt", "file3.txt"])
        for path, content in files:
            print(f"{path}: {len(content)} bytes")
        ```
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
    dictionary mapping paths to contents. All I/O operations execute outside
    the Python GIL using native Rust/Tokio, ensuring true async behavior.

    Args:
        paths: List of file paths to read

    Returns:
        Dictionary mapping file paths to their contents (bytes)

    Raises:
        FileNotFoundError: If any file does not exist
        IOError: If any file cannot be read
        ValueError: If any path is invalid (empty or contains null bytes)

    Example:
        ```python
        files = await read_files_dict(["file1.txt", "file2.txt"])
        print(files["file1.txt"])  # b"content"
        ```
    """
    results = await read_files(paths)
    return dict(results)


async def write_files(files: Dict[str, bytes]) -> None:
    """
    Write multiple files concurrently.

    Writes contents to all specified files concurrently. All I/O operations
    execute outside the Python GIL using native Rust/Tokio, ensuring true async behavior.

    Args:
        files: Dictionary mapping file paths to their contents (bytes)

    Raises:
        IOError: If any file cannot be written
        PermissionError: If write permission is denied for any file
        ValueError: If any path is invalid (empty or contains null bytes)

    Example:
        ```python
        files = {
            "file1.txt": b"content1",
            "file2.txt": b"content2",
        }
        await write_files(files)
        ```
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

    Copies all specified files concurrently. All I/O operations execute
    outside the Python GIL using native Rust/Tokio, ensuring true async behavior.

    Args:
        files: List of (src, dst) tuples to copy

    Raises:
        FileNotFoundError: If any source file does not exist
        IOError: If any file cannot be copied
        ValueError: If any path is invalid (empty or contains null bytes)

    Example:
        ```python
        files = [
            ("source1.txt", "dest1.txt"),
            ("source2.txt", "dest2.txt"),
        ]
        await copy_files(files)
        ```
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

    Args:
        file: Path to the file (str or bytes)
        mode: File mode (r, r+, w, w+, a, a+, rb, rb+, wb, wb+, ab, ab+)
        buffering: Buffer size (not yet implemented, accepted for compatibility)
        encoding: Text encoding (not yet implemented, accepted for compatibility)
        errors: Error handling (not yet implemented, accepted for compatibility)
        newline: Newline handling (not yet implemented, accepted for compatibility)
        closefd: Close file descriptor (not yet implemented, accepted for compatibility)
        opener: Custom opener (not yet implemented, accepted for compatibility)

    Returns:
        AsyncFile: An async file handle that can be used with async context managers

    Example:
        ```python
        async with open("file.txt", "r") as f:
            content = await f.read()
        ```
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
