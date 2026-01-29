# rapfiles

**True async filesystem I/O — no fake async, no GIL stalls.**

[![PyPI version](https://img.shields.io/pypi/v/rapfiles.svg)](https://pypi.org/project/rapfiles/)
[![Downloads](https://pepy.tech/badge/rapfiles)](https://pepy.tech/project/rapfiles)
[![Python 3.8+](https://img.shields.io/badge/python-3.8+-blue.svg)](https://www.python.org/downloads/)
[![License: MIT](https://img.shields.io/badge/License-MIT-yellow.svg)](https://opensource.org/licenses/MIT)

## Overview

`rapfiles` provides true async filesystem I/O operations for Python, backed by Rust and Tokio. Unlike libraries that wrap blocking I/O in `async` syntax, `rapfiles` guarantees that all I/O work executes **outside the Python GIL**, ensuring event loops never stall under load.

**Roadmap Goal**: Achieve drop-in replacement compatibility with `aiofiles`, enabling seamless migration with true async performance. See [docs/ROADMAP.md](docs/ROADMAP.md) for details.

## Why `rap*`?

Packages prefixed with **`rap`** stand for **Real Async Python**. Unlike many libraries that merely wrap blocking I/O in `async` syntax, `rap*` packages guarantee that all I/O work is executed **outside the Python GIL** using native runtimes (primarily Rust). This means event loops are never stalled by hidden thread pools, blocking syscalls, or cooperative yielding tricks. If a `rap*` API is `async`, it is *structurally non-blocking by design*, not by convention. The `rap` prefix is a contract: measurable concurrency, real parallelism, and verifiable async behavior under load.

See the [rap-manifesto](https://github.com/eddiethedean/rap-manifesto) for philosophy and guarantees.

## Features

- ✅ **True async** file reads and writes
- ✅ **Native Rust-backed** execution (Tokio)
- ✅ **Zero Python thread pools**
- ✅ **Event-loop-safe** concurrency under load
- ✅ **GIL-independent** I/O operations
- ✅ **Verified** by Fake Async Detector
- ✅ **File handles** with async context managers (`async with`)
- ✅ **Directory operations** (create, remove, list, walk)
- ✅ **File metadata** (stat, size, timestamps)
- ✅ **Path operations** (`rapfiles.ospath` module)
- ✅ **aiofiles compatibility** (Phase 1 complete)

## Requirements

- Python 3.8+
- Rust 1.70+ (for building from source)

## Installation

```bash
pip install rapfiles
```

### Building from Source

```bash
git clone https://github.com/eddiethedean/rapfiles.git
cd rapfiles
pip install maturin
maturin develop
```

---

## Usage

### Basic File Operations

```python
import asyncio
from rapfiles import read_file, write_file

async def main():
    # Write file asynchronously (true async, GIL-independent)
    await write_file("example.txt", "Hello from rapfiles!")
    
    # Read file asynchronously (true async, GIL-independent)
    content = await read_file("example.txt")
    print(content)  # Output: Hello from rapfiles!
    
    # Write another file
    await write_file("output.txt", content)

asyncio.run(main())
```

### File Handles (aiofiles compatible)

```python
import asyncio
from rapfiles import open

async def main():
    # Open file with async context manager
    async with open("file.txt", "r") as f:
        content = await f.read()
        print(content)
    
    # Write mode
    async with open("output.txt", "w") as f:
        await f.write("Hello, world!")
    
    # Binary mode
    async with open("image.png", "rb") as f:
        data = await f.read()
    
    # Read lines
    async with open("file.txt", "r") as f:
        line = await f.readline()
        lines = await f.readlines()

asyncio.run(main())
```

### Directory Operations

```python
import asyncio
from rapfiles import create_dir, list_dir, exists, is_file, is_dir, walk_dir

async def main():
    # Create directories
    await create_dir("new_dir")
    await create_dir_all("path/to/nested/dir")
    
    # Check if path exists
    if await exists("file.txt"):
        print("File exists!")
    
    # Check file/directory type
    if await is_file("file.txt"):
        print("It's a file")
    if await is_dir("directory"):
        print("It's a directory")
    
    # List directory contents
    files = await list_dir(".")
    print(files)
    
    # Recursively walk directory
    for path, is_file in await walk_dir("."):
        print(f"{path}: {'file' if is_file else 'dir'}")

asyncio.run(main())
```

### File Metadata

```python
import asyncio
from rapfiles import stat, FileMetadata

async def main():
    # Get file statistics
    metadata: FileMetadata = await stat("file.txt")
    print(f"Size: {metadata.size} bytes")
    print(f"Is file: {metadata.is_file}")
    print(f"Modified: {metadata.modified}")
    print(f"Created: {metadata.created}")

asyncio.run(main())
```

### Concurrent File Operations

```python
import asyncio
from rapfiles import read_file, write_file

async def main():
    # Process multiple files concurrently
    tasks = [
        write_file("file1.txt", "Content 1"),
        write_file("file2.txt", "Content 2"),
        write_file("file3.txt", "Content 3"),
    ]
    await asyncio.gather(*tasks)
    
    # Read all files concurrently
    contents = await asyncio.gather(
        read_file("file1.txt"),
        read_file("file2.txt"),
        read_file("file3.txt"),
    )
    print(contents)  # ['Content 1', 'Content 2', 'Content 3']

asyncio.run(main())
```

## API Reference

### File Operations

#### `read_file(path: str) -> str`

Read a file asynchronously and return its contents as a string.

**Parameters:**
- `path` (str): Path to the file to read

**Returns:**
- `str`: File contents as UTF-8 decoded string

**Raises:**
- `FileNotFoundError`: If the file does not exist
- `IOError`: If the file cannot be read
- `ValueError`: If the path is invalid

#### `write_file(path: str, contents: str) -> None`

Write content to a file asynchronously.

**Parameters:**
- `path` (str): Path to the file to write
- `contents` (str): Content to write to the file

**Raises:**
- `IOError`: If the file cannot be written
- `PermissionError`: If write permission is denied
- `ValueError`: If the path is invalid

#### `read_file_bytes(path: str) -> bytes`

Read a file asynchronously and return its contents as bytes.

**Parameters:**
- `path` (str): Path to the file to read

**Returns:**
- `bytes`: File contents as raw bytes

**Raises:**
- `FileNotFoundError`: If the file does not exist
- `IOError`: If the file cannot be read

#### `write_file_bytes(path: str, contents: bytes) -> None`

Write bytes to a file asynchronously.

**Parameters:**
- `path` (str): Path to the file to write
- `contents` (bytes): Bytes to write to the file

**Raises:**
- `IOError`: If the file cannot be written
- `PermissionError`: If write permission is denied

#### `append_file(path: str, contents: str) -> None`

Append content to a file asynchronously.

**Parameters:**
- `path` (str): Path to the file to append to
- `contents` (str): Content to append to the file

**Raises:**
- `IOError`: If the file cannot be written
- `PermissionError`: If write permission is denied

### File Handles

#### `open(file: Union[str, bytes], mode: str = "r", ...) -> AsyncFile`

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

**Example:**
```python
async with open("file.txt", "r") as f:
    content = await f.read()
```

#### `AsyncFile` Class

An async file handle for true async I/O operations.

**Methods:**
- `read(size: int = -1) -> Union[str, bytes]`: Read from file (returns str for text mode, bytes for binary)
- `write(data: Union[str, bytes]) -> int`: Write to file, returns number of bytes written
- `readline(size: int = -1) -> Union[str, bytes]`: Read a single line
- `readlines(hint: int = -1) -> List[Union[str, bytes]]`: Read all lines
- `seek(offset: int, whence: int = 0) -> int`: Seek to position (0=start, 1=current, 2=end)
- `tell() -> int`: Get current file position
- `close() -> None`: Close the file (automatic on context exit)

### Directory Operations

#### `create_dir(path: str) -> None`

Create a directory asynchronously. Parent directories must exist.

**Raises:**
- `FileExistsError`: If the directory already exists
- `IOError`: If the directory cannot be created

#### `create_dir_all(path: str) -> None`

Create a directory and all parent directories asynchronously.

**Raises:**
- `IOError`: If the directory cannot be created

#### `remove_dir(path: str) -> None`

Remove an empty directory asynchronously.

**Raises:**
- `FileNotFoundError`: If the directory does not exist
- `IOError`: If the directory is not empty or cannot be removed

#### `remove_dir_all(path: str) -> None`

Remove a directory and all its contents asynchronously.

**Raises:**
- `FileNotFoundError`: If the directory does not exist
- `IOError`: If the directory cannot be removed

#### `list_dir(path: str) -> List[str]`

List directory contents asynchronously.

**Returns:**
- `List[str]`: List of file and directory names

**Raises:**
- `FileNotFoundError`: If the directory does not exist
- `IOError`: If the directory cannot be read

#### `exists(path: str) -> bool`

Check if a path exists asynchronously.

**Returns:**
- `bool`: True if path exists, False otherwise

#### `is_file(path: str) -> bool`

Check if a path is a file asynchronously.

**Returns:**
- `bool`: True if path is a file, False otherwise

**Raises:**
- `IOError`: If the path does not exist

#### `is_dir(path: str) -> bool`

Check if a path is a directory asynchronously.

**Returns:**
- `bool`: True if path is a directory, False otherwise

**Raises:**
- `IOError`: If the path does not exist

#### `walk_dir(path: str) -> List[Tuple[str, bool]]`

Recursively walk a directory asynchronously.

**Parameters:**
- `path` (str): Directory path to walk

**Returns:**
- `List[Tuple[str, bool]]`: List of (path, is_file) tuples for all files and directories found

**Raises:**
- `FileNotFoundError`: If the directory does not exist
- `IOError`: If the directory cannot be read

### File Metadata

#### `stat(path: str) -> FileMetadata`

Get file statistics asynchronously.

**Returns:**
- `FileMetadata`: File metadata object with size, timestamps, and type information

**Raises:**
- `FileNotFoundError`: If the path does not exist
- `IOError`: If metadata cannot be retrieved

#### `metadata(path: str) -> FileMetadata`

Get file metadata asynchronously (alias for `stat`).

#### `FileMetadata` Class

File metadata structure (aiofiles.stat_result compatible).

**Properties:**
- `size` (int): File size in bytes
- `is_file` (bool): True if path is a file
- `is_dir` (bool): True if path is a directory
- `modified` (float): Modification time as Unix timestamp
- `accessed` (float): Access time as Unix timestamp
- `created` (float): Creation time as Unix timestamp

### Path Operations

The `rapfiles.ospath` module provides synchronous path operations compatible with `aiofiles.ospath`:

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

## Benchmarks

This package passes the [Fake Async Detector](https://github.com/eddiethedean/rap-bench). Benchmarks are available in the [rap-bench](https://github.com/eddiethedean/rap-bench) repository.

Run the detector yourself:

```bash
pip install rap-bench
rap-bench detect rapfiles
```

## Documentation

Comprehensive documentation is available in the [`docs/`](docs/) directory:
- [Roadmap](docs/ROADMAP.md) - Detailed development plans
- [Build and Test](docs/BUILD_AND_TEST.md) - Local development setup
- [Release Notes](docs/PYPI_RELEASE_NOTES.md) - Version history and changes
- [Security](SECURITY.md) - Security policy and reporting

## Roadmap

See [docs/ROADMAP.md](docs/ROADMAP.md) for detailed development plans. Key goals include:
- Drop-in replacement for `aiofiles` (Phase 1)
- Comprehensive filesystem operations (directories, metadata, permissions)
- Advanced I/O patterns and zero-copy optimizations
- Filesystem traversal and watching capabilities

## Related Projects

- [rap-manifesto](https://github.com/eddiethedean/rap-manifesto) - Philosophy and guarantees
- [rap-bench](https://github.com/eddiethedean/rap-bench) - Fake Async Detector CLI
- [rapsqlite](https://github.com/eddiethedean/rapsqlite) - True async SQLite
- [rapcsv](https://github.com/eddiethedean/rapcsv) - Streaming async CSV

## Current Status (v0.1.0)

**Phase 1 Complete ✅:**
- ✅ File handle operations (`AsyncFile` class with `async with` support)
- ✅ File operations: `read()`, `write()`, `readline()`, `readlines()`, `seek()`, `tell()`
- ✅ Binary file operations: `read_file_bytes()`, `write_file_bytes()`
- ✅ Append operations: `append_file()`
- ✅ Directory operations: `create_dir()`, `create_dir_all()`, `remove_dir()`, `remove_dir_all()`, `list_dir()`
- ✅ Path checking: `exists()`, `is_file()`, `is_dir()`
- ✅ Directory traversal: `walk_dir()` for recursive directory walking
- ✅ File metadata: `stat()`, `metadata()`, `FileMetadata` class
- ✅ Path operations: `rapfiles.ospath` module (aiofiles.ospath compatible)
- ✅ aiofiles compatibility: Drop-in replacement for basic `aiofiles` operations
- ✅ Comprehensive test suite: 34+ tests covering all features
- ✅ Type stubs: Complete `.pyi` files for IDE support
- ✅ Type checking: Full mypy support with Python 3.8+ compatibility
- ✅ Code quality: Ruff formatted and linted, clippy checked

**Known Limitations:**
- `buffering`, `encoding`, `errors`, `newline`, `closefd`, `opener` parameters accepted for API compatibility but not yet fully implemented
- No file watching capabilities (planned for future phases)
- No advanced I/O patterns like zero-copy (planned for future phases)

**Roadmap**: See [docs/ROADMAP.md](docs/ROADMAP.md) for planned improvements. Phase 1 (aiofiles compatibility) is complete. Future phases will add advanced features and optimizations.

## Contributing

Contributions are welcome! Please see our [contributing guidelines](https://github.com/eddiethedean/rapfiles/blob/main/docs/CONTRIBUTING.md) (coming soon).

## License

MIT

## Changelog

See [docs/PYPI_RELEASE_NOTES.md](docs/PYPI_RELEASE_NOTES.md) for version history and release notes.
