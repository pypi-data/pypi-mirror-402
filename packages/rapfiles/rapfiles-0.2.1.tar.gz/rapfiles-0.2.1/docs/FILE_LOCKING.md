# File Locking

`rapfiles` provides advisory file locking for coordinating access to files between multiple processes or coroutines.

## Exclusive Locks

Exclusive locks are used for writing operations. Only one process can hold an exclusive lock at a time.

```python
import asyncio
from rapfiles import lock_file, write_file

async def main():
    # Exclusive lock for writing
    # Note: On Windows, write after releasing the lock (see Windows Considerations below)
    async with lock_file("data.txt", exclusive=True) as lock:
        # Lock acquired - other processes cannot acquire exclusive lock
        pass
    # Lock released - now write safely on all platforms
    await write_file("data.txt", "Exclusive access")

asyncio.run(main())
```

## Shared Locks

Shared locks are used for reading operations. Multiple processes can hold shared locks simultaneously.

```python
import asyncio
from rapfiles import lock_file_shared, read_file

async def main():
    # Shared lock for reading
    async with lock_file_shared("data.txt") as lock:
        content = await read_file("data.txt")
        # Multiple readers can hold shared locks simultaneously
    # Lock automatically released

asyncio.run(main())
```

## Using the Lock Function Directly

```python
import asyncio
from rapfiles import lock_file

async def main():
    # Exclusive lock (default)
    async with lock_file("file.txt") as lock:
        # Write operations here
        pass
    
    # Shared lock
    async with lock_file("file.txt", exclusive=False) as lock:
        # Read operations here
        pass

asyncio.run(main())
```

## Real-World Example: Concurrent File Updates

```python
import asyncio
from rapfiles import lock_file, read_file, atomic_write_file

async def update_counter():
    """Safely increment a counter in a file (cross-platform)."""
    async with lock_file("counter.txt", exclusive=True):
        # Read current value
        try:
            current = int(await read_file("counter.txt"))
        except FileNotFoundError:
            current = 0
    
    # Release lock before writing (required on Windows)
    # Use atomic_write_file for true atomicity across all platforms
    await atomic_write_file("counter.txt", str(current + 1))

# Multiple coroutines can safely update the counter
async def main():
    await asyncio.gather(
        update_counter(),
        update_counter(),
        update_counter(),
    )

asyncio.run(main())
```

## Example: Reader-Writer Pattern

```python
import asyncio
from rapfiles import lock_file, lock_file_shared, read_file, write_file

async def reader(file_path: str):
    """Multiple readers can read simultaneously."""
    async with lock_file_shared(file_path):
        content = await read_file(file_path)
        print(f"Read: {content}")
        await asyncio.sleep(0.1)  # Simulate reading

async def writer(file_path: str, data: str):
    """Only one writer at a time (cross-platform)."""
    async with lock_file(file_path, exclusive=True):
        # Lock acquired - only this writer can proceed
        pass
    # Lock released - now write safely on all platforms
    await write_file(file_path, data)
    print(f"Wrote: {data}")

async def main():
    file_path = "shared.txt"
    await write_file(file_path, "Initial content")
    
    # Multiple readers can read simultaneously
    await asyncio.gather(
        reader(file_path),
        reader(file_path),
        reader(file_path),
    )
    
    # Only one writer at a time
    await asyncio.gather(
        writer(file_path, "Update 1"),
        writer(file_path, "Update 2"),
    )

asyncio.run(main())
```

## Important Notes

- **Advisory Locks**: These are advisory locks, meaning they only work if all processes respect them. They don't prevent file access, only coordinate it.
- **Automatic Release**: Locks are automatically released when exiting the `async with` block.
- **File Creation**: If the file doesn't exist, it will be created when acquiring the lock.
- **Cross-Platform**: Works on Unix-like systems and Windows.

## Windows Considerations

**⚠️ Important:** On Windows, file locking behavior differs from Unix systems. While holding an exclusive lock, you **cannot** write to the file through a different file handle (such as using `write_file()`, which opens a new handle).

### Windows-Compatible Pattern

On Windows, release the lock before writing:

```python
import asyncio
from rapfiles import lock_file, read_file, write_file

async def update_counter_windows_safe():
    """Windows-compatible: Release lock before writing."""
    async with lock_file("counter.txt", exclusive=True):
        # Read while holding lock (this works on Windows)
        try:
            current = int(await read_file("counter.txt"))
        except FileNotFoundError:
            current = 0
    
    # Lock released, now write safely
    await write_file("counter.txt", str(current + 1))
```

Or use atomic operations which don't require holding the lock during write:

```python
import asyncio
from rapfiles import lock_file, read_file, atomic_write_file

async def update_counter_atomic():
    """Use atomic_write_file - works on all platforms."""
    async with lock_file("counter.txt", exclusive=True):
        # Read current value
        try:
            current = int(await read_file("counter.txt"))
        except FileNotFoundError:
            current = 0
        
        # Atomic write uses the same locking mechanism internally
        await atomic_write_file("counter.txt", str(current + 1))
```

### What Works on All Platforms

- ✅ Acquiring and releasing locks
- ✅ Reading files while holding a lock (through different handles)
- ✅ Coordinating access between processes/coroutines
- ✅ Using `atomic_write_file()` while holding a lock (it handles this internally)

### What Only Works on Unix

- ❌ Writing through a different file handle (like `write_file()`) while holding an exclusive lock

## API Reference

### `lock_file(path: str, exclusive: bool = True) -> FileLock`

Acquire an advisory file lock as an async context manager.

**Parameters:**
- `path` (str): Path to the file to lock
- `exclusive` (bool): If True, acquire exclusive (write) lock; if False, acquire shared (read) lock

**Returns:**
- Async context manager that yields a `FileLock` instance

**Raises:**
- `IOError`: If the lock cannot be acquired
- `ValueError`: If the path is invalid

### `lock_file_shared(path: str) -> FileLock`

Acquire a shared (read) file lock as an async context manager.

**Parameters:**
- `path` (str): Path to the file to lock

**Returns:**
- Async context manager that yields a `FileLock` instance

**Raises:**
- `IOError`: If the lock cannot be acquired
- `ValueError`: If the path is invalid

### `FileLock` Class

File lock object returned by `lock_file()` and `lock_file_shared()`. Use with `async with` syntax.

**Methods:**
- `release() -> None`: Manually release the lock (usually not needed with context manager)

## See Also

- [File Operations](../README.md#basic-file-operations) - Basic file read/write
- [Atomic Operations](ATOMIC_OPERATIONS.md) - Atomic file writes
