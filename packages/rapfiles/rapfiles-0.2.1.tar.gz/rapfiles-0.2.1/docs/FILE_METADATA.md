# File Metadata

`rapfiles` provides async file metadata operations for getting file statistics, sizes, and timestamps.

## Getting File Statistics

### Basic Usage

```python
import asyncio
from rapfiles import stat, FileMetadata

async def main():
    # Get file statistics
    metadata: FileMetadata = await stat("file.txt")
    print(f"Size: {metadata.size} bytes")
    print(f"Is file: {metadata.is_file}")
    print(f"Is directory: {metadata.is_dir}")
    print(f"Modified: {metadata.modified}")
    print(f"Accessed: {metadata.accessed}")
    print(f"Created: {metadata.created}")

asyncio.run(main())
# Output:
# Size: 12 bytes
# Is file: True
# Is directory: False
# Modified: 1768696716.4495575
# Accessed: 1768696716.4494822
# Created: 1768696716.4494822
```

### Using the Alias

```python
import asyncio
from rapfiles import metadata

async def main():
    # metadata() is an alias for stat()
    meta = await metadata("file.txt")
    print(f"File size: {meta.size} bytes")

asyncio.run(main())
```

## FileMetadata Properties

The `FileMetadata` class provides the following properties:

- **`size`** (int): File size in bytes
- **`is_file`** (bool): True if path is a file
- **`is_dir`** (bool): True if path is a directory
- **`modified`** (float): Modification time as Unix timestamp (seconds since epoch)
- **`accessed`** (float): Access time as Unix timestamp
- **`created`** (float): Creation time as Unix timestamp (birth time on Unix, creation time on Windows)

## Example: File Information Display

```python
import asyncio
from datetime import datetime
from rapfiles import stat

async def display_file_info(path: str):
    """Display detailed file information."""
    meta = await stat(path)
    
    print(f"Path: {path}")
    print(f"Type: {'File' if meta.is_file else 'Directory'}")
    print(f"Size: {meta.size:,} bytes")
    print(f"Modified: {datetime.fromtimestamp(meta.modified)}")
    print(f"Accessed: {datetime.fromtimestamp(meta.accessed)}")
    print(f"Created: {datetime.fromtimestamp(meta.created)}")

asyncio.run(display_file_info("example.txt"))
# Output example:
# Path: example.txt
# Type: File
# Size: 12 bytes
# Modified: 2026-01-17 12:05:16.449557
# Accessed: 2026-01-17 12:05:16.449482
# Created: 2026-01-17 12:05:16.449482
```

## API Reference

### `stat(path: str) -> FileMetadata`

Get file statistics asynchronously.

**Parameters:**
- `path` (str): Path to the file or directory

**Returns:**
- `FileMetadata`: File metadata object with size, timestamps, and type information

**Raises:**
- `FileNotFoundError`: If the path does not exist
- `IOError`: If metadata cannot be retrieved
- `ValueError`: If the path is invalid (empty or contains null bytes)

### `metadata(path: str) -> FileMetadata`

Get file metadata asynchronously (alias for `stat`).

**Parameters:**
- `path` (str): Path to the file or directory

**Returns:**
- `FileMetadata`: File metadata object

**Raises:**
- Same as `stat()`

### `FileMetadata` Class

File metadata structure (aiofiles.stat_result compatible).

**Properties:**
- `size` (int): File size in bytes
- `is_file` (bool): True if path is a file
- `is_dir` (bool): True if path is a directory
- `modified` (float): Modification time as Unix timestamp
- `accessed` (float): Access time as Unix timestamp
- `created` (float): Creation time as Unix timestamp

## See Also

- [Directory Operations](DIRECTORY_OPERATIONS.md) - Directory management
- [File Operations](../README.md#basic-file-operations) - Basic file read/write
- [Path Operations](PATH_OPERATIONS.md) - Synchronous path utilities
