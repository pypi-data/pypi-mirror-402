# Atomic File Operations

`rapfiles` provides atomic file operations that ensure files are never in a partially-written state, making them ideal for critical data writes.

## Atomic Writes

### Text Files

```python
import asyncio
from rapfiles import atomic_write_file

async def main():
    # Atomic write ensures file is never partially written
    await atomic_write_file("important.txt", "Critical data")
    # File is written to temp file first, then atomically renamed

asyncio.run(main())
```

### Binary Files

```python
import asyncio
from rapfiles import atomic_write_file_bytes

async def main():
    # Atomic write for binary data
    await atomic_write_file_bytes("data.bin", b"\x00\x01\x02\x03")
    # Ensures binary file is never corrupted

asyncio.run(main())
```

## Atomic Moves

```python
import asyncio
from rapfiles import atomic_move_file

async def main():
    # Atomic move ensures destination is never in partial state
    await atomic_move_file("source.txt", "destination.txt")
    # For cross-device moves, copies atomically then removes source

asyncio.run(main())
```

## Use Cases

### Configuration Files

```python
import asyncio
import json
from rapfiles import atomic_write_file

async def save_config(config: dict):
    """Save configuration atomically."""
    config_json = json.dumps(config, indent=2)
    await atomic_write_file("config.json", config_json)
    # If process crashes, config.json is never corrupted

asyncio.run(save_config({"key": "value"}))
```

### Database Updates

```python
import asyncio
from rapfiles import atomic_write_file_bytes, atomic_move_file

async def update_database(data: bytes):
    """Update database file atomically."""
    # Write to temporary file
    await atomic_write_file_bytes("database.tmp", data)
    
    # Atomically replace old database
    await atomic_move_file("database.tmp", "database.db")
    # Database is never in a corrupted state

asyncio.run(update_database(b"database content"))
```

### Log Rotation

```python
import asyncio
from rapfiles import atomic_move_file

async def rotate_logs():
    """Rotate log files atomically."""
    # Move current log to archive
    await atomic_move_file("app.log", "logs/app.log.1")
    # New log file will be created fresh

asyncio.run(rotate_logs())
```

## How Atomic Operations Work

1. **Atomic Write**: 
   - Writes content to a temporary file
   - Atomically renames the temp file to the target
   - If the process crashes, the original file remains intact

2. **Atomic Move**:
   - Within the same filesystem: Uses atomic rename operation
   - Cross-device: Copies to temp file, then atomically replaces destination

## API Reference

### `atomic_write_file(path: str, contents: str) -> None`

Write a file atomically using a temporary file.

**Parameters:**
- `path` (str): Path to the file to write
- `contents` (str): Content to write (will be encoded as UTF-8)

**Raises:**
- `IOError`: If the file cannot be written
- `PermissionError`: If write permission is denied
- `ValueError`: If the path is invalid

### `atomic_write_file_bytes(path: str, contents: bytes) -> None`

Write bytes to a file atomically using a temporary file.

**Parameters:**
- `path` (str): Path to the file to write
- `contents` (bytes): Bytes to write to the file

**Raises:**
- `IOError`: If the file cannot be written
- `PermissionError`: If write permission is denied
- `ValueError`: If the path is invalid

### `atomic_move_file(src: str, dst: str) -> None`

Move a file atomically.

**Parameters:**
- `src` (str): Path to the source file
- `dst` (str): Path to the destination file

**Raises:**
- `FileNotFoundError`: If the source file does not exist
- `IOError`: If the file cannot be moved
- `ValueError`: If the path is invalid

## See Also

- [File Manipulation](FILE_MANIPULATION.md) - Regular file operations
- [File Operations](../README.md#basic-file-operations) - Basic file read/write
