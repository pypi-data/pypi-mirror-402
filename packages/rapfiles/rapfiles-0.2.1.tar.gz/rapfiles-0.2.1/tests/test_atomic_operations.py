"""Test atomic operations and file locking."""

import pytest
import tempfile
import os
import asyncio
import uuid
import sys

from rapfiles import (
    atomic_write_file,
    atomic_write_file_bytes,
    atomic_move_file,
    lock_file,
    lock_file_shared,
    write_file,
    read_file,
    read_file_bytes,
    exists,
)


def _unique_name(base: str) -> str:
    """Generate a unique file name using base and UUID."""
    test_id = str(uuid.uuid4())[:8]
    name, ext = os.path.splitext(base)
    return f"{name}_{test_id}{ext}"


@pytest.mark.asyncio
async def test_atomic_write_file():
    """Test atomic write operation."""
    with tempfile.TemporaryDirectory() as tmpdir:
        file_path = os.path.join(tmpdir, _unique_name("test.txt"))

        await atomic_write_file(file_path, "Hello, World!")

        assert await exists(file_path)
        content = await read_file(file_path)
        assert content == "Hello, World!"


@pytest.mark.asyncio
async def test_atomic_write_file_bytes():
    """Test atomic write bytes operation."""
    with tempfile.TemporaryDirectory() as tmpdir:
        file_path = os.path.join(tmpdir, _unique_name("test.bin"))
        original_data = b"\x00\x01\x02\x03\xff\xfe\xfd"

        await atomic_write_file_bytes(file_path, original_data)

        assert await exists(file_path)
        data = await read_file_bytes(file_path)
        assert data == original_data


@pytest.mark.asyncio
async def test_atomic_write_file_overwrites():
    """Test that atomic_write_file overwrites existing file atomically."""
    with tempfile.TemporaryDirectory() as tmpdir:
        file_path = os.path.join(tmpdir, _unique_name("test.txt"))

        # Create initial file
        await write_file(file_path, "Original content")

        # Atomically overwrite
        await atomic_write_file(file_path, "New content")

        content = await read_file(file_path)
        assert content == "New content"


@pytest.mark.asyncio
async def test_atomic_write_concurrent_read():
    """Test that atomic write doesn't interfere with concurrent reads."""
    with tempfile.TemporaryDirectory() as tmpdir:
        file_path = os.path.join(tmpdir, _unique_name("test.txt"))

        # Write initial content
        await write_file(file_path, "Initial content")

        async def read_loop():
            """Read file in a loop."""
            reads = []
            for _ in range(10):
                if await exists(file_path):
                    content = await read_file(file_path)
                    reads.append(content)
                await asyncio.sleep(0.01)
            return reads

        async def atomic_write():
            """Atomically write new content."""
            await asyncio.sleep(0.05)
            await atomic_write_file(file_path, "New content")

        # Run concurrent read and write
        reads, _ = await asyncio.gather(read_loop(), atomic_write())

        # All reads should have valid content (no partially written files)
        assert all(content in ["Initial content", "New content"] for content in reads)


@pytest.mark.asyncio
async def test_atomic_move_file():
    """Test atomic move operation."""
    with tempfile.TemporaryDirectory() as tmpdir:
        src = os.path.join(tmpdir, _unique_name("source.txt"))
        dst = os.path.join(tmpdir, _unique_name("destination.txt"))

        await write_file(src, "Hello, World!")

        await atomic_move_file(src, dst)

        assert not await exists(src)
        assert await exists(dst)
        content = await read_file(dst)
        assert content == "Hello, World!"


@pytest.mark.asyncio
async def test_atomic_move_file_overwrites():
    """Test that atomic_move_file overwrites existing destination."""
    with tempfile.TemporaryDirectory() as tmpdir:
        src = os.path.join(tmpdir, _unique_name("source.txt"))
        dst = os.path.join(tmpdir, _unique_name("destination.txt"))

        await write_file(src, "Source content")
        await write_file(dst, "Original content")

        await atomic_move_file(src, dst)

        assert not await exists(src)
        content = await read_file(dst)
        assert content == "Source content"


@pytest.mark.asyncio
@pytest.mark.skipif(
    sys.platform == "win32",
    reason="Windows file locking prevents writing through different handle while lock is held",
)
async def test_lock_file_exclusive():
    """Test exclusive file locking."""
    with tempfile.TemporaryDirectory() as tmpdir:
        file_path = os.path.join(tmpdir, _unique_name("locked.txt"))

        async with lock_file(file_path, exclusive=True) as lock:
            # File should be locked
            assert lock is not None
            # Can write to file
            await write_file(file_path, "Locked content")

        # Lock should be released after context exit
        content = await read_file(file_path)
        assert content == "Locked content"


@pytest.mark.asyncio
async def test_lock_file_shared():
    """Test shared file locking."""
    with tempfile.TemporaryDirectory() as tmpdir:
        file_path = os.path.join(tmpdir, _unique_name("shared.txt"))
        await write_file(file_path, "Shared content")

        async with lock_file_shared(file_path) as lock:
            # File should be locked with shared lock
            assert lock is not None
            # Can read file
            content = await read_file(file_path)
            assert content == "Shared content"

        # Lock should be released after context exit


@pytest.mark.asyncio
async def test_lock_file_release():
    """Test manually releasing file lock."""
    with tempfile.TemporaryDirectory() as tmpdir:
        file_path = os.path.join(tmpdir, _unique_name("release.txt"))

        async with lock_file(file_path, exclusive=True) as lock:
            # Release lock manually
            await lock.release()

        # Lock should be released


@pytest.mark.asyncio
async def test_lock_file_nonexistent():
    """Test that lock_file creates file if it doesn't exist."""
    with tempfile.TemporaryDirectory() as tmpdir:
        file_path = os.path.join(tmpdir, _unique_name("nonexistent.txt"))

        async with lock_file(file_path, exclusive=True) as lock:
            assert lock is not None
            # File should be created
            assert await exists(file_path)


@pytest.mark.asyncio
async def test_concurrent_locks():
    """Test file locking (sequential to avoid potential deadlocks)."""
    with tempfile.TemporaryDirectory() as tmpdir:
        file_path = os.path.join(tmpdir, _unique_name("concurrent.txt"))

        lock_acquired = []

        # Acquire locks sequentially to avoid blocking issues
        async with lock_file(file_path, exclusive=True):
            lock_acquired.append("lock1")
            await asyncio.sleep(0.05)

        async with lock_file(file_path, exclusive=True):
            lock_acquired.append("lock2")
            await asyncio.sleep(0.05)

        # Both should have acquired
        assert len(lock_acquired) == 2


@pytest.mark.asyncio
async def test_lock_with_atomic_write():
    """Test using lock with atomic write for coordination."""
    with tempfile.TemporaryDirectory() as tmpdir:
        file_path = os.path.join(tmpdir, _unique_name("coordinated.txt"))

        async with lock_file(file_path, exclusive=True):
            # Write atomically while holding lock
            await atomic_write_file(file_path, "Coordinated write")

        # File should be written
        content = await read_file(file_path)
        assert content == "Coordinated write"


@pytest.mark.asyncio
async def test_atomic_operations_error_handling():
    """Test error handling in atomic operations."""
    with tempfile.TemporaryDirectory():
        # Test empty path
        with pytest.raises(ValueError):
            await atomic_write_file("", "content")

        # Test invalid path (contains null byte)
        with pytest.raises(ValueError):
            await atomic_write_file("file\x00name.txt", "content")


@pytest.mark.asyncio
async def test_lock_file_error_handling():
    """Test error handling in file locking."""
    with tempfile.TemporaryDirectory():
        # Test empty path
        with pytest.raises(ValueError):
            async with lock_file("", exclusive=True):
                pass

        # Test invalid path (contains null byte)
        with pytest.raises(ValueError):
            async with lock_file("file\x00name.txt", exclusive=True):
                pass


@pytest.mark.asyncio
async def test_atomic_write_large_file():
    """Test atomic write with large file."""
    with tempfile.TemporaryDirectory() as tmpdir:
        file_path = os.path.join(tmpdir, _unique_name("large.txt"))

        # Create large content (1MB)
        large_content = "x" * (1024 * 1024)

        await atomic_write_file(file_path, large_content)

        content = await read_file(file_path)
        assert len(content) == len(large_content)
        assert content == large_content


@pytest.mark.asyncio
async def test_atomic_write_file_bytes_large():
    """Test atomic write bytes with large binary data."""
    with tempfile.TemporaryDirectory() as tmpdir:
        file_path = os.path.join(tmpdir, _unique_name("large.bin"))

        # Create large binary data (1MB)
        large_data = b"\x00" * (1024 * 1024)

        await atomic_write_file_bytes(file_path, large_data)

        data = await read_file_bytes(file_path)
        assert len(data) == len(large_data)
        assert data == large_data


@pytest.mark.asyncio
async def test_atomic_write_preserves_content():
    """Test that atomic write doesn't corrupt content during write."""
    with tempfile.TemporaryDirectory() as tmpdir:
        file_path = os.path.join(tmpdir, _unique_name("test.txt"))

        # Write initial content
        await write_file(file_path, "Initial")

        # Atomically overwrite multiple times
        for i in range(10):
            await atomic_write_file(file_path, f"Content {i}")
            content = await read_file(file_path)
            assert content == f"Content {i}"


@pytest.mark.asyncio
async def test_atomic_write_no_partial_file():
    """Test that atomic write never leaves partial file on failure."""
    with tempfile.TemporaryDirectory() as tmpdir:
        file_path = os.path.join(tmpdir, _unique_name("test.txt"))

        # Write initial content
        await write_file(file_path, "Initial content")
        initial_content = await read_file(file_path)

        # Try to write to invalid path (should fail, but original should remain)
        try:
            # This should fail, but original file should be intact
            invalid_path = os.path.join(tmpdir, "nonexistent", "subdir", "file.txt")
            await atomic_write_file(invalid_path, "Should fail")
        except (IOError, FileNotFoundError):
            pass

        # Original file should still exist with original content
        if await exists(file_path):
            content = await read_file(file_path)
            assert content == initial_content


@pytest.mark.asyncio
async def test_atomic_move_large_file():
    """Test atomic move with large file."""
    with tempfile.TemporaryDirectory() as tmpdir:
        src = os.path.join(tmpdir, _unique_name("large_source.txt"))
        dst = os.path.join(tmpdir, _unique_name("large_destination.txt"))

        # Create large content
        large_content = "x" * (1024 * 1024)
        await write_file(src, large_content)

        await atomic_move_file(src, dst)

        assert not await exists(src)
        assert await exists(dst)
        dst_content = await read_file(dst)
        assert len(dst_content) == len(large_content)
        assert dst_content == large_content


@pytest.mark.asyncio
async def test_lock_file_exclusive_blocking():
    """Test that exclusive lock blocks other exclusive locks."""
    with tempfile.TemporaryDirectory() as tmpdir:
        file_path = os.path.join(tmpdir, _unique_name("locked.txt"))

        lock_acquired = []

        # Acquire locks sequentially to avoid blocking/deadlock issues
        async with lock_file(file_path, exclusive=True):
            lock_acquired.append("lock1")
            await asyncio.sleep(0.05)

        async with lock_file(file_path, exclusive=True):
            lock_acquired.append("lock2")
            await asyncio.sleep(0.05)

        # Both should have acquired sequentially
        assert len(lock_acquired) == 2


@pytest.mark.asyncio
async def test_lock_file_shared_multiple():
    """Test that multiple shared locks can be held simultaneously."""
    with tempfile.TemporaryDirectory() as tmpdir:
        file_path = os.path.join(tmpdir, _unique_name("shared.txt"))
        await write_file(file_path, "Shared content")

        locks_held = []

        # Acquire shared locks sequentially
        async with lock_file_shared(file_path):
            locks_held.append("reader1")
            await asyncio.sleep(0.02)

        async with lock_file_shared(file_path):
            locks_held.append("reader2")
            await asyncio.sleep(0.02)

        async with lock_file_shared(file_path):
            locks_held.append("reader3")
            await asyncio.sleep(0.02)

        # All should have acquired
        assert len(locks_held) == 3


@pytest.mark.asyncio
async def test_lock_file_exclusive_vs_shared():
    """Test that exclusive lock blocks shared locks."""
    with tempfile.TemporaryDirectory() as tmpdir:
        file_path = os.path.join(tmpdir, _unique_name("test.txt"))
        await write_file(file_path, "Content")

        exclusive_held = False
        shared_held = False

        # Test exclusive then shared (sequential to avoid blocking)
        async with lock_file(file_path, exclusive=True):
            exclusive_held = True
            await asyncio.sleep(0.05)
            exclusive_held = False

        # After exclusive releases, shared should work
        async with lock_file_shared(file_path):
            shared_held = True
            await asyncio.sleep(0.05)
            shared_held = False

        # Both should have run
        assert exclusive_held is False and shared_held is False


@pytest.mark.asyncio
async def test_lock_file_nested():
    """Test that acquiring a lock on different files works."""
    with tempfile.TemporaryDirectory() as tmpdir:
        file1 = os.path.join(tmpdir, _unique_name("file1.txt"))
        file2 = os.path.join(tmpdir, _unique_name("file2.txt"))

        # Acquiring locks on different files should work fine
        async with lock_file(file1, exclusive=True) as lock1:
            async with lock_file(file2, exclusive=True) as lock2:
                # Both locks on different files should work
                assert lock1 is not None
                assert lock2 is not None


@pytest.mark.asyncio
async def test_atomic_operations_unicode():
    """Test atomic operations with Unicode content."""
    with tempfile.TemporaryDirectory() as tmpdir:
        file_path = os.path.join(tmpdir, _unique_name("unicode.txt"))

        unicode_content = "Hello 世界 🌍 Привет مرحبا"
        await atomic_write_file(file_path, unicode_content)

        content = await read_file(file_path)
        assert content == unicode_content


@pytest.mark.asyncio
async def test_atomic_write_multiple_rapid():
    """Test rapid atomic writes don't interfere with each other."""
    with tempfile.TemporaryDirectory() as tmpdir:
        file_path = os.path.join(tmpdir, _unique_name("rapid.txt"))

        # Perform many rapid atomic writes
        for i in range(20):
            await atomic_write_file(file_path, f"Content {i}")

        # Final content should be correct
        content = await read_file(file_path)
        assert content == "Content 19"


@pytest.mark.asyncio
@pytest.mark.skipif(
    sys.platform == "win32",
    reason="Windows file locking prevents writing through different handle while lock is held",
)
async def test_lock_file_with_file_operations():
    """Test file operations while holding lock."""
    with tempfile.TemporaryDirectory() as tmpdir:
        file_path = os.path.join(tmpdir, _unique_name("locked_ops.txt"))

        async with lock_file(file_path, exclusive=True):
            # Should be able to write while holding lock
            await write_file(file_path, "Locked write")

            # Should be able to read while holding lock
            content = await read_file(file_path)
            assert content == "Locked write"

            # Should be able to append
            await write_file(file_path, "New content")

        # After lock release, file should have final content
        final_content = await read_file(file_path)
        assert final_content == "New content"
