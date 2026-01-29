# Path Operations

The `rapfiles.ospath` module provides synchronous path operations compatible with `aiofiles.ospath`. These operations work with path strings and do not perform file I/O, so they are synchronous and do not need to be async.

## Basic Usage

```python
import rapfiles.ospath as ospath

# Check if path exists
if ospath.exists("file.txt"):
    print("File exists")

# Check path type
if ospath.isfile("file.txt"):
    print("It's a file")
if ospath.isdir("directory"):
    print("It's a directory")

# Get file size
size = ospath.getsize("file.txt")
print(f"Size: {size} bytes")
```

## Path Manipulation

```python
import rapfiles.ospath as ospath

# Join paths
full_path = ospath.join("dir", "subdir", "file.txt")
print(full_path)  # Output: "dir/subdir/file.txt" (or "dir\\subdir\\file.txt" on Windows)

# Get absolute path
abs_path = ospath.abspath("./relative/path")
print(abs_path)  # Output example: "/absolute/path/to/file"

# Normalize path
normalized = ospath.normpath("dir/../other/./file.txt")
print(normalized)  # Output: "other/file.txt"

# Split path components
dirname = ospath.dirname("/path/to/file.txt")
basename = ospath.basename("/path/to/file.txt")
print(dirname)   # Output: "/path/to"
print(basename)  # Output: "file.txt"

# Split extension
name, ext = ospath.splitext("file.txt")
print(name)  # Output: "file"
print(ext)   # Output: ".txt"

# Split path
head, tail = ospath.split("/path/to/file.txt")
print(head)  # Output: "/path/to"
print(tail)  # Output: "file.txt"
```

## Complete Example

```python
import rapfiles.ospath as ospath

def process_path(path: str):
    """Process a file path and extract information."""
    if not ospath.exists(path):
        return None
    
    info = {
        "exists": True,
        "is_file": ospath.isfile(path),
        "is_dir": ospath.isdir(path),
        "size": ospath.getsize(path) if ospath.isfile(path) else 0,
        "absolute": ospath.abspath(path),
        "dirname": ospath.dirname(path),
        "basename": ospath.basename(path),
    }
    
    if ospath.isfile(path):
        name, ext = ospath.splitext(path)
        info["name"] = name
        info["extension"] = ext
    
    return info

# Usage
info = process_path("example.txt")
print(info)
```

## API Reference

### `exists(path: Union[str, bytes, Path]) -> bool`

Check if a path exists (synchronous).

**Parameters:**
- `path`: Path to check (str, bytes, or Path object)

**Returns:**
- `bool`: True if the path exists, False otherwise

### `isfile(path: Union[str, bytes, Path]) -> bool`

Check if a path is a file (synchronous).

**Parameters:**
- `path`: Path to check

**Returns:**
- `bool`: True if the path is a file, False otherwise

### `isdir(path: Union[str, bytes, Path]) -> bool`

Check if a path is a directory (synchronous).

**Parameters:**
- `path`: Path to check

**Returns:**
- `bool`: True if the path is a directory, False otherwise

### `getsize(path: Union[str, bytes, Path]) -> int`

Get the size of a file in bytes (synchronous).

**Parameters:**
- `path`: Path to the file

**Returns:**
- `int`: File size in bytes

**Raises:**
- `OSError`: If the path does not exist or is not a file

### `join(*paths: Union[str, bytes, Path]) -> str`

Join path components (synchronous).

**Parameters:**
- `*paths`: Path components to join

**Returns:**
- `str`: Joined path

### `normpath(path: Union[str, bytes, Path]) -> str`

Normalize a path (synchronous).

**Parameters:**
- `path`: Path to normalize

**Returns:**
- `str`: Normalized path

### `abspath(path: Union[str, bytes, Path]) -> str`

Get absolute path (synchronous).

**Parameters:**
- `path`: Path to convert

**Returns:**
- `str`: Absolute path

### `dirname(path: Union[str, bytes, Path]) -> str`

Get directory name (synchronous).

**Parameters:**
- `path`: Path to process

**Returns:**
- `str`: Directory name

### `basename(path: Union[str, bytes, Path]) -> str`

Get base name (synchronous).

**Parameters:**
- `path`: Path to process

**Returns:**
- `str`: Base name (filename or directory name)

### `splitext(path: Union[str, bytes, Path]) -> Tuple[str, str]`

Split path into name and extension (synchronous).

**Parameters:**
- `path`: Path to split

**Returns:**
- `Tuple[str, str]`: (name, extension) tuple

### `split(path: Union[str, bytes, Path]) -> Tuple[str, str]`

Split path into head and tail (synchronous).

**Parameters:**
- `path`: Path to split

**Returns:**
- `Tuple[str, str]`: (head, tail) tuple

## Compatibility

The `rapfiles.ospath` module is compatible with `aiofiles.ospath` API, making it easy to migrate from `aiofiles`:

```python
# Works the same way
import aiofiles.ospath as aio_ospath
import rapfiles.ospath as rap_ospath

# Both work identically
aio_ospath.exists("file.txt")
rap_ospath.exists("file.txt")
```

## See Also

- [Directory Operations](DIRECTORY_OPERATIONS.md) - Async directory operations
- [File Metadata](FILE_METADATA.md) - Async file metadata
- [File Operations](../README.md#basic-file-operations) - Basic file read/write
