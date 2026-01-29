# Batch Operations

`rapfiles` provides batch operations for processing multiple files concurrently, significantly improving performance when working with many files.

## Writing Multiple Files

```python
import asyncio
from rapfiles import write_files

async def main():
    # Write multiple files concurrently
    files = {
        "file1.txt": b"Content 1",
        "file2.txt": b"Content 2",
        "file3.txt": b"Content 3",
    }
    await write_files(files)
    # All files are written concurrently

asyncio.run(main())
```

## Reading Multiple Files

### As List of Tuples

```python
import asyncio
from rapfiles import read_files

async def main():
    # Read multiple files concurrently
    paths = ["file1.txt", "file2.txt", "file3.txt"]
    results = await read_files(paths)
    # Returns: [("file1.txt", b"Content 1"), ("file2.txt", b"Content 2"), ...]
    
    for path, content in results:
        print(f"{path}: {content.decode()}")

asyncio.run(main())
# Output:
# file1.txt: Content 1
# file2.txt: Content 2
# file3.txt: Content 3
```

### As Dictionary

```python
import asyncio
from rapfiles import read_files_dict

async def main():
    # Read multiple files concurrently as dictionary
    paths = ["file1.txt", "file2.txt", "file3.txt"]
    content_dict = await read_files_dict(paths)
    # Returns: {"file1.txt": b"Content 1", "file2.txt": b"Content 2", ...}
    
    print(content_dict["file1.txt"].decode())

asyncio.run(main())
# Output:
# Content 1
```

## Copying Multiple Files

```python
import asyncio
from rapfiles import copy_files

async def main():
    # Copy multiple files concurrently
    copy_pairs = [
        ("src1.txt", "dst1.txt"),
        ("src2.txt", "dst2.txt"),
        ("src3.txt", "dst3.txt"),
    ]
    await copy_files(copy_pairs)
    # All copies happen concurrently

asyncio.run(main())
```

## Complete Example: File Processing Pipeline

```python
import asyncio
from rapfiles import read_files_dict, write_files, copy_files

async def process_files():
    # Step 1: Read all source files concurrently
    source_files = ["input1.txt", "input2.txt", "input3.txt"]
    contents = await read_files_dict(source_files)
    
    # Step 2: Process contents (example: uppercase)
    processed = {
        path: content.upper()
        for path, content in contents.items()
    }
    
    # Step 3: Write processed files concurrently
    await write_files(processed)
    
    # Step 4: Copy to backup location concurrently
    backup_pairs = [
        (path, f"backup/{path}")
        for path in processed.keys()
    ]
    await copy_files(backup_pairs)

asyncio.run(process_files())
```

## Performance Benefits

Batch operations execute all file operations concurrently, providing significant performance improvements:

```python
import asyncio
import time
from rapfiles import read_file, read_files

async def compare_approaches():
    files = [f"file{i}.txt" for i in range(100)]
    
    # Sequential approach
    start = time.time()
    for file in files:
        await read_file(file)
    sequential_time = time.time() - start
    
    # Batch approach
    start = time.time()
    await read_files(files)
    batch_time = time.time() - start
    
    print(f"Sequential: {sequential_time:.2f}s")
    print(f"Batch: {batch_time:.2f}s")
    print(f"Speedup: {sequential_time / batch_time:.2f}x")

asyncio.run(compare_approaches())
```

## Error Handling

Batch operations continue processing even if some files fail:

```python
import asyncio
from rapfiles import read_files

async def main():
    paths = ["existing.txt", "missing.txt", "another.txt"]
    
    try:
        results = await read_files(paths)
        # Process successful reads
        for path, content in results:
            if content:  # Check if read succeeded
                print(f"{path}: {content.decode()}")
    except Exception as e:
        print(f"Some files failed: {e}")

asyncio.run(main())
```

## API Reference

### `read_files(paths: List[str]) -> List[Tuple[str, bytes]]`

Read multiple files concurrently.

**Parameters:**
- `paths` (List[str]): List of file paths to read

**Returns:**
- `List[Tuple[str, bytes]]`: List of (path, bytes) tuples for successfully read files

**Raises:**
- `IOError`: If all files fail to read (individual failures are included in results)

### `read_files_dict(paths: List[str]) -> Dict[str, bytes]`

Read multiple files concurrently as a dictionary.

**Parameters:**
- `paths` (List[str]): List of file paths to read

**Returns:**
- `Dict[str, bytes]`: Dictionary mapping paths to file contents

**Raises:**
- `IOError`: If all files fail to read

### `write_files(files: Dict[str, bytes]) -> None`

Write multiple files concurrently.

**Parameters:**
- `files` (Dict[str, bytes]): Dictionary mapping file paths to contents

**Raises:**
- `IOError`: If any file fails to write
- `ValueError`: If any path is invalid

### `copy_files(files: List[Tuple[str, str]]) -> None`

Copy multiple files concurrently.

**Parameters:**
- `files` (List[Tuple[str, str]]): List of (src_path, dst_path) tuples

**Raises:**
- `FileNotFoundError`: If any source file does not exist
- `IOError`: If any copy operation fails
- `ValueError`: If any path is invalid

## See Also

- [File Operations](../README.md#basic-file-operations) - Basic file read/write
- [File Manipulation](FILE_MANIPULATION.md) - Individual file operations
