# Directory Operations

`rapfiles` provides comprehensive async directory operations for creating, removing, listing, and traversing directories.

## Basic Operations

### Create Directories

```python
import asyncio
from rapfiles import create_dir, create_dir_all

async def main():
    # Create a single directory (parent must exist)
    await create_dir("new_dir")
    
    # Create directory and all parent directories
    await create_dir_all("path/to/nested/dir")

asyncio.run(main())
```

### Remove Directories

```python
import asyncio
from rapfiles import remove_dir, remove_dir_all

async def main():
    # Remove empty directory
    await remove_dir("empty_dir")
    
    # Remove directory and all contents
    await remove_dir_all("directory_with_files")

asyncio.run(main())
```

### List Directory Contents

```python
import asyncio
from rapfiles import list_dir

async def main():
    # List all files and directories
    files = await list_dir(".")
    print(files)

asyncio.run(main())
# Output example:
# ['file1.txt', 'file2.txt', 'subdir']
```

### Check Path Types

```python
import asyncio
from rapfiles import exists, is_file, is_dir

async def main():
    # Check if path exists
    if await exists("file.txt"):
        print("File exists!")
    
    # Check if path is a file
    if await is_file("file.txt"):
        print("It's a file")
    
    # Check if path is a directory
    if await is_dir("directory"):
        print("It's a directory")

asyncio.run(main())
```

## Directory Traversal

### Recursive Directory Walking

```python
import asyncio
from rapfiles import walk_dir

async def main():
    # Recursively walk directory
    for path, is_file in await walk_dir("."):
        if is_file:
            print(f"File: {path}")
        else:
            print(f"Directory: {path}")

asyncio.run(main())
```

## API Reference

### `create_dir(path: str) -> None`

Create a directory asynchronously. Parent directories must exist.

**Parameters:**
- `path` (str): Path to the directory to create

**Raises:**
- `FileExistsError`: If the directory already exists
- `IOError`: If the directory cannot be created

### `create_dir_all(path: str) -> None`

Create a directory and all parent directories asynchronously.

**Parameters:**
- `path` (str): Path to the directory to create

**Raises:**
- `IOError`: If the directory cannot be created

### `remove_dir(path: str) -> None`

Remove an empty directory asynchronously.

**Parameters:**
- `path` (str): Path to the directory to remove

**Raises:**
- `FileNotFoundError`: If the directory does not exist
- `IOError`: If the directory is not empty or cannot be removed

### `remove_dir_all(path: str) -> None`

Remove a directory and all its contents asynchronously.

**Parameters:**
- `path` (str): Path to the directory to remove

**Raises:**
- `FileNotFoundError`: If the directory does not exist
- `IOError`: If the directory cannot be removed

### `list_dir(path: str) -> List[str]`

List directory contents asynchronously.

**Parameters:**
- `path` (str): Path to the directory

**Returns:**
- `List[str]`: List of file and directory names

**Raises:**
- `FileNotFoundError`: If the directory does not exist
- `IOError`: If the directory cannot be read

### `exists(path: str) -> bool`

Check if a path exists asynchronously.

**Parameters:**
- `path` (str): Path to check

**Returns:**
- `bool`: True if path exists, False otherwise

### `is_file(path: str) -> bool`

Check if a path is a file asynchronously.

**Parameters:**
- `path` (str): Path to check

**Returns:**
- `bool`: True if path is a file, False otherwise

**Raises:**
- `IOError`: If the path does not exist

### `is_dir(path: str) -> bool`

Check if a path is a directory asynchronously.

**Parameters:**
- `path` (str): Path to check

**Returns:**
- `bool`: True if path is a directory, False otherwise

**Raises:**
- `IOError`: If the path does not exist

### `walk_dir(path: str) -> List[Tuple[str, bool]]`

Recursively walk a directory asynchronously.

**Parameters:**
- `path` (str): Directory path to walk

**Returns:**
- `List[Tuple[str, bool]]`: List of (path, is_file) tuples for all files and directories found

**Raises:**
- `FileNotFoundError`: If the directory does not exist
- `IOError`: If the directory cannot be read

## See Also

- [File Operations](../README.md#basic-file-operations) - Basic file read/write
- [File Metadata](FILE_METADATA.md) - Getting file information
- [Path Operations](PATH_OPERATIONS.md) - Synchronous path utilities
