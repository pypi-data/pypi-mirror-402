# API Reference

Complete API reference for `rapfiles`.

## File Operations

### `read_file(path: str) -> str`

Read a file asynchronously and return its contents as a string.

**Parameters:**
- `path` (str): Path to the file to read

**Returns:**
- `str`: File contents as UTF-8 decoded string

**Raises:**
- `FileNotFoundError`: If the file does not exist
- `IOError`: If the file cannot be read
- `ValueError`: If the path is invalid (empty or contains null bytes)

### `write_file(path: str, contents: str) -> None`

Write content to a file asynchronously.

**Parameters:**
- `path` (str): Path to the file to write
- `contents` (str): Content to write to the file

**Raises:**
- `IOError`: If the file cannot be written
- `PermissionError`: If write permission is denied
- `ValueError`: If the path is invalid

### `read_file_bytes(path: str) -> bytes`

Read a file asynchronously and return its contents as bytes.

**Parameters:**
- `path` (str): Path to the file to read

**Returns:**
- `bytes`: File contents as raw bytes

**Raises:**
- `FileNotFoundError`: If the file does not exist
- `IOError`: If the file cannot be read
- `ValueError`: If the path is invalid

### `write_file_bytes(path: str, contents: bytes) -> None`

Write bytes to a file asynchronously.

**Parameters:**
- `path` (str): Path to the file to write
- `contents` (bytes): Bytes to write to the file

**Raises:**
- `IOError`: If the file cannot be written
- `PermissionError`: If write permission is denied
- `ValueError`: If the path is invalid

### `append_file(path: str, contents: str) -> None`

Append content to a file asynchronously.

**Parameters:**
- `path` (str): Path to the file to append to
- `contents` (str): Content to append to the file

**Raises:**
- `IOError`: If the file cannot be written
- `PermissionError`: If write permission is denied
- `ValueError`: If the path is invalid

## File Handles

### `open(file: Union[str, bytes], mode: str = "r", ...) -> AsyncFile`

Open a file asynchronously (aiofiles.open() compatible).

**Parameters:**
- `file` (Union[str, bytes]): Path to the file
- `mode` (str): File mode (r, r+, w, w+, a, a+, rb, rb+, wb, wb+, ab, ab+)
- `buffering` (int): Buffer size (accepted for compatibility, not yet implemented)
- `encoding` (Optional[str]): Text encoding (accepted for compatibility, not yet implemented)
- `errors` (Optional[str]): Error handling (accepted for compatibility, not yet implemented)
- `newline` (Optional[str]): Newline handling (accepted for compatibility, not yet implemented)
- `closefd` (bool): Close file descriptor (accepted for compatibility, not yet implemented)
- `opener` (Optional[Any]): Custom opener (accepted for compatibility, not yet implemented)

**Returns:**
- Async context manager that yields an `AsyncFile` instance

### `AsyncFile` Class

An async file handle for true async I/O operations.

**Methods:**
- `read(size: int = -1) -> Union[str, bytes]`: Read from file (returns str for text mode, bytes for binary)
- `write(data: Union[str, bytes]) -> int`: Write to file, returns number of bytes written
- `readline(size: int = -1) -> Union[str, bytes]`: Read a single line
- `readlines(hint: int = -1) -> List[Union[str, bytes]]`: Read all lines
- `seek(offset: int, whence: int = 0) -> int`: Seek to position (0=start, 1=current, 2=end)
- `tell() -> int`: Get current file position
- `close() -> None`: Close the file (automatic on context exit)

## Directory Operations

See [Directory Operations](DIRECTORY_OPERATIONS.md) for detailed documentation.

- `create_dir(path: str) -> None`
- `create_dir_all(path: str) -> None`
- `remove_dir(path: str) -> None`
- `remove_dir_all(path: str) -> None`
- `list_dir(path: str) -> List[str]`
- `exists(path: str) -> bool`
- `is_file(path: str) -> bool`
- `is_dir(path: str) -> bool`
- `walk_dir(path: str) -> List[Tuple[str, bool]]`

## File Metadata

See [File Metadata](FILE_METADATA.md) for detailed documentation.

- `stat(path: str) -> FileMetadata`
- `metadata(path: str) -> FileMetadata`
- `FileMetadata` class with properties: `size`, `is_file`, `is_dir`, `modified`, `accessed`, `created`

## File Manipulation

See [File Manipulation](FILE_MANIPULATION.md) for detailed documentation.

- `copy_file(src: str, dst: str) -> None`
- `move_file(src: str, dst: str) -> None`
- `rename(src: str, dst: str) -> None`
- `remove_file(path: str) -> None`
- `hard_link(src: str, dst: str) -> None`
- `symlink(src: str, dst: str) -> None`
- `canonicalize(path: str) -> str`

## Atomic Operations

See [Atomic Operations](ATOMIC_OPERATIONS.md) for detailed documentation.

- `atomic_write_file(path: str, contents: str) -> None`
- `atomic_write_file_bytes(path: str, contents: bytes) -> None`
- `atomic_move_file(src: str, dst: str) -> None`

## File Locking

See [File Locking](FILE_LOCKING.md) for detailed documentation.

- `lock_file(path: str, exclusive: bool = True) -> FileLock`
- `lock_file_shared(path: str) -> FileLock`
- `FileLock` class

## Batch Operations

See [Batch Operations](BATCH_OPERATIONS.md) for detailed documentation.

- `read_files(paths: List[str]) -> List[Tuple[str, bytes]]`
- `read_files_dict(paths: List[str]) -> Dict[str, bytes]`
- `write_files(files: Dict[str, bytes]) -> None`
- `copy_files(files: List[Tuple[str, str]]) -> None`

## Path Operations

See [Path Operations](PATH_OPERATIONS.md) for detailed documentation.

The `rapfiles.ospath` module provides synchronous path operations:

- `exists(path) -> bool`
- `isfile(path) -> bool`
- `isdir(path) -> bool`
- `getsize(path) -> int`
- `join(*paths) -> str`
- `normpath(path) -> str`
- `abspath(path) -> str`
- `dirname(path) -> str`
- `basename(path) -> str`
- `splitext(path) -> Tuple[str, str]`
- `split(path) -> Tuple[str, str]`

## Error Handling

All functions raise appropriate Python exceptions:

- `FileNotFoundError`: When a file or directory does not exist
- `IOError`: For general I/O errors
- `PermissionError`: When permission is denied
- `ValueError`: When a path is invalid (empty or contains null bytes)
- `FileExistsError`: When trying to create a file/directory that already exists

## See Also

- [README](../README.md) - Getting started and basic usage
- [Directory Operations](DIRECTORY_OPERATIONS.md) - Directory management
- [File Metadata](FILE_METADATA.md) - File information
- [File Manipulation](FILE_MANIPULATION.md) - File operations
- [Atomic Operations](ATOMIC_OPERATIONS.md) - Atomic writes
- [File Locking](FILE_LOCKING.md) - File locking
- [Batch Operations](BATCH_OPERATIONS.md) - Concurrent operations
- [Path Operations](PATH_OPERATIONS.md) - Path utilities
