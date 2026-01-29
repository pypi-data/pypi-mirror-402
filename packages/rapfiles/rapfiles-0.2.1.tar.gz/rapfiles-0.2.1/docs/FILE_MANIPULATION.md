# File Manipulation Operations

`rapfiles` provides async file manipulation operations for copying, moving, renaming, removing, and linking files.

## Copying Files

```python
import asyncio
from rapfiles import copy_file

async def main():
    # Copy a file
    await copy_file("source.txt", "destination.txt")

asyncio.run(main())
```

## Moving and Renaming Files

```python
import asyncio
from rapfiles import move_file, rename

async def main():
    # Move a file (atomic within same filesystem)
    await move_file("old_name.txt", "new_name.txt")
    
    # Rename is an alias for move_file
    await rename("old.txt", "new.txt")

asyncio.run(main())
```

## Removing Files

```python
import asyncio
from rapfiles import remove_file

async def main():
    # Remove a file
    await remove_file("unwanted.txt")

asyncio.run(main())
```

## Creating Links

### Hard Links

```python
import asyncio
from rapfiles import hard_link

async def main():
    # Create a hard link
    await hard_link("original.txt", "link.txt")
    # Both files now refer to the same data

asyncio.run(main())
```

### Symbolic Links

```python
import asyncio
from rapfiles import symlink

async def main():
    # Create a symbolic link
    await symlink("/path/to/original", "/path/to/link")
    # The link points to the original path

asyncio.run(main())
```

## Canonicalizing Paths

```python
import asyncio
from rapfiles import canonicalize

async def main():
    # Resolve all symbolic links and return absolute path
    abs_path = await canonicalize("./relative/path/../file.txt")
    print(abs_path)  # /absolute/path/to/file.txt

asyncio.run(main())
```

## Complete Example

```python
import asyncio
from rapfiles import copy_file, move_file, remove_file, symlink, canonicalize

async def reorganize_files():
    # Copy important file
    await copy_file("important.txt", "backup/important.txt")
    
    # Move file to new location
    await move_file("old_location/file.txt", "new_location/file.txt")
    
    # Create symlink for easy access
    await symlink("new_location/file.txt", "current_file.txt")
    
    # Get canonical path
    canonical = await canonicalize("current_file.txt")
    print(f"Canonical path: {canonical}")
    
    # Clean up old file
    await remove_file("old_location/file.txt")

asyncio.run(reorganize_files())
```

## API Reference

### `copy_file(src: str, dst: str) -> None`

Copy a file asynchronously from source to destination.

**Parameters:**
- `src` (str): Path to the source file
- `dst` (str): Path to the destination file

**Raises:**
- `FileNotFoundError`: If the source file does not exist
- `IOError`: If the file cannot be copied
- `ValueError`: If the path is invalid

### `move_file(src: str, dst: str) -> None`

Move or rename a file asynchronously. Atomic within the same filesystem.

**Parameters:**
- `src` (str): Path to the source file
- `dst` (str): Path to the destination file

**Raises:**
- `FileNotFoundError`: If the source file does not exist
- `IOError`: If the file cannot be moved
- `ValueError`: If the path is invalid

### `rename(src: str, dst: str) -> None`

Rename a file asynchronously (alias for `move_file`).

**Parameters:**
- `src` (str): Path to the source file
- `dst` (str): Path to the destination file

**Raises:**
- Same as `move_file()`

### `remove_file(path: str) -> None`

Remove a file asynchronously.

**Parameters:**
- `path` (str): Path to the file to remove

**Raises:**
- `FileNotFoundError`: If the file does not exist
- `IOError`: If the file cannot be removed (e.g., if it's a directory)
- `ValueError`: If the path is invalid

### `hard_link(src: str, dst: str) -> None`

Create a hard link asynchronously.

**Parameters:**
- `src` (str): Path to the source file
- `dst` (str): Path to the destination link

**Raises:**
- `FileNotFoundError`: If the source file does not exist
- `IOError`: If the link cannot be created
- `ValueError`: If the path is invalid

### `symlink(src: str, dst: str) -> None`

Create a symbolic link asynchronously.

**Parameters:**
- `src` (str): Path that the symlink will point to
- `dst` (str): Path to the symbolic link to create

**Raises:**
- `IOError`: If the symlink cannot be created
- `ValueError`: If the path is invalid

### `canonicalize(path: str) -> str`

Resolve all symbolic links and return the canonical absolute path.

**Parameters:**
- `path` (str): Path to canonicalize

**Returns:**
- `str`: Canonical absolute path

**Raises:**
- `FileNotFoundError`: If the path does not exist
- `IOError`: If the path cannot be canonicalized
- `ValueError`: If the path is invalid

## See Also

- [Atomic Operations](ATOMIC_OPERATIONS.md) - Atomic file writes and moves
- [Batch Operations](BATCH_OPERATIONS.md) - Concurrent file operations
- [File Operations](../README.md#basic-file-operations) - Basic file read/write
