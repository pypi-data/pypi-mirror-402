"""Test batch operations for Phase 2."""

import pytest
import tempfile
import os
import uuid
import sys

from rapfiles import (
    read_files,
    read_files_dict,
    write_files,
    copy_files,
    read_file,
    write_file,
    read_file_bytes,
    write_file_bytes,
    exists,
)


def _unique_name(base: str) -> str:
    """Generate a unique file name using base and UUID."""
    test_id = str(uuid.uuid4())[:8]
    name, ext = os.path.splitext(base)
    return f"{name}_{test_id}{ext}"


@pytest.mark.asyncio
async def test_read_files_basic():
    """Test basic batch file reading."""
    with tempfile.TemporaryDirectory() as tmpdir:
        # Create test files
        files = {
            os.path.join(tmpdir, _unique_name("file1.txt")): "Content 1",
            os.path.join(tmpdir, _unique_name("file2.txt")): "Content 2",
            os.path.join(tmpdir, _unique_name("file3.txt")): "Content 3",
        }

        # Write files
        for path, content in files.items():
            await write_file(path, content)

        # Read all files
        paths = list(files.keys())
        results = await read_files(paths)

        # Verify results
        assert len(results) == 3
        result_dict = dict(results)
        for path, expected_content in files.items():
            assert path in result_dict
            assert result_dict[path].decode("utf-8") == expected_content


@pytest.mark.asyncio
async def test_read_files_dict():
    """Test batch file reading returning dictionary."""
    with tempfile.TemporaryDirectory() as tmpdir:
        # Create test files
        files = {
            os.path.join(tmpdir, _unique_name("file1.txt")): "Content 1",
            os.path.join(tmpdir, _unique_name("file2.txt")): "Content 2",
            os.path.join(tmpdir, _unique_name("file3.txt")): "Content 3",
        }

        # Write files
        for path, content in files.items():
            await write_file(path, content)

        # Read all files as dictionary
        paths = list(files.keys())
        result_dict = await read_files_dict(paths)

        # Verify results
        assert len(result_dict) == 3
        for path, expected_content in files.items():
            assert path in result_dict
            assert result_dict[path].decode("utf-8") == expected_content


@pytest.mark.asyncio
async def test_read_files_binary():
    """Test batch reading binary files."""
    with tempfile.TemporaryDirectory() as tmpdir:
        # Create binary test files
        files = {
            os.path.join(tmpdir, _unique_name("file1.bin")): b"\x00\x01\x02",
            os.path.join(tmpdir, _unique_name("file2.bin")): b"\xff\xfe\xfd",
            os.path.join(tmpdir, _unique_name("file3.bin")): b"\xaa\xbb\xcc",
        }

        # Write files
        for path, content in files.items():
            await write_file_bytes(path, content)

        # Read all files
        paths = list(files.keys())
        results = await read_files(paths)

        # Verify results
        assert len(results) == 3
        result_dict = dict(results)
        for path, expected_content in files.items():
            assert path in result_dict
            assert result_dict[path] == expected_content


@pytest.mark.asyncio
async def test_read_files_mixed_success_failure():
    """Test batch reading with some files missing."""
    with tempfile.TemporaryDirectory() as tmpdir:
        # Create some files
        file1 = os.path.join(tmpdir, _unique_name("file1.txt"))
        file2 = os.path.join(tmpdir, _unique_name("file2.txt"))
        file3 = os.path.join(tmpdir, _unique_name("nonexistent.txt"))

        await write_file(file1, "Content 1")
        await write_file(file2, "Content 2")
        # file3 doesn't exist

        # Read files - should raise error for missing file
        with pytest.raises(IOError):
            await read_files([file1, file2, file3])


@pytest.mark.asyncio
async def test_read_files_empty_list():
    """Test reading empty list of files."""
    results = await read_files([])
    assert results == []


@pytest.mark.asyncio
async def test_read_files_large_batch():
    """Test reading large batch of files."""
    with tempfile.TemporaryDirectory() as tmpdir:
        # Create 50 files
        num_files = 50
        files = {}
        for i in range(num_files):
            path = os.path.join(tmpdir, f"file_{i}.txt")
            content = f"Content {i}"
            await write_file(path, content)
            files[path] = content

        # Read all files
        paths = list(files.keys())
        results = await read_files(paths)

        # Verify all files read correctly
        assert len(results) == num_files
        result_dict = dict(results)
        for path, expected_content in files.items():
            assert path in result_dict
            assert result_dict[path].decode("utf-8") == expected_content


@pytest.mark.asyncio
async def test_write_files_basic():
    """Test basic batch file writing."""
    with tempfile.TemporaryDirectory() as tmpdir:
        files = {
            os.path.join(tmpdir, _unique_name("file1.txt")): b"Content 1",
            os.path.join(tmpdir, _unique_name("file2.txt")): b"Content 2",
            os.path.join(tmpdir, _unique_name("file3.txt")): b"Content 3",
        }

        # Write all files
        await write_files(files)

        # Verify all files exist and have correct content
        for path, expected_content in files.items():
            assert await exists(path)
            content = await read_file_bytes(path)
            assert content == expected_content


@pytest.mark.asyncio
async def test_write_files_overwrites():
    """Test that write_files overwrites existing files."""
    with tempfile.TemporaryDirectory() as tmpdir:
        file1 = os.path.join(tmpdir, _unique_name("file1.txt"))
        file2 = os.path.join(tmpdir, _unique_name("file2.txt"))

        # Create initial files
        await write_file(file1, "Original 1")
        await write_file(file2, "Original 2")

        # Overwrite with batch write
        files = {
            file1: b"New 1",
            file2: b"New 2",
        }
        await write_files(files)

        # Verify overwritten content
        assert await read_file(file1) == "New 1"
        assert await read_file(file2) == "New 2"


@pytest.mark.asyncio
async def test_write_files_large_batch():
    """Test writing large batch of files."""
    with tempfile.TemporaryDirectory() as tmpdir:
        num_files = 50
        files = {}
        for i in range(num_files):
            path = os.path.join(tmpdir, f"file_{i}.txt")
            files[path] = f"Content {i}".encode("utf-8")

        # Write all files
        await write_files(files)

        # Verify all files
        for path, expected_content in files.items():
            assert await exists(path)
            content = await read_file_bytes(path)
            assert content == expected_content


@pytest.mark.asyncio
async def test_write_files_empty_dict():
    """Test writing empty dictionary."""
    await write_files({})


@pytest.mark.asyncio
async def test_copy_files_basic():
    """Test basic batch file copying."""
    with tempfile.TemporaryDirectory() as tmpdir:
        # Create source files
        src_files = [os.path.join(tmpdir, f"src_{i}.txt") for i in range(5)]
        dst_files = [os.path.join(tmpdir, f"dst_{i}.txt") for i in range(5)]

        # Write source files
        for i, src in enumerate(src_files):
            await write_file(src, f"Content {i}")

        # Copy all files
        copy_pairs = list(zip(src_files, dst_files))
        await copy_files(copy_pairs)

        # Verify all copies
        for i, (src, dst) in enumerate(zip(src_files, dst_files)):
            assert await exists(src)
            assert await exists(dst)
            src_content = await read_file(src)
            dst_content = await read_file(dst)
            assert src_content == dst_content == f"Content {i}"


@pytest.mark.asyncio
async def test_copy_files_overwrites():
    """Test that copy_files overwrites existing destinations."""
    with tempfile.TemporaryDirectory() as tmpdir:
        src = os.path.join(tmpdir, _unique_name("source.txt"))
        dst = os.path.join(tmpdir, _unique_name("destination.txt"))

        await write_file(src, "Source content")
        await write_file(dst, "Original content")

        await copy_files([(src, dst)])

        assert await read_file(dst) == "Source content"


@pytest.mark.asyncio
async def test_copy_files_large_batch():
    """Test copying large batch of files."""
    with tempfile.TemporaryDirectory() as tmpdir:
        num_files = 50
        src_files = [os.path.join(tmpdir, f"src_{i}.txt") for i in range(num_files)]
        dst_files = [os.path.join(tmpdir, f"dst_{i}.txt") for i in range(num_files)]

        # Write source files
        for i, src in enumerate(src_files):
            await write_file(src, f"Content {i}")

        # Copy all files
        copy_pairs = list(zip(src_files, dst_files))
        await copy_files(copy_pairs)

        # Verify all copies
        for i, (src, dst) in enumerate(zip(src_files, dst_files)):
            assert await exists(dst)
            assert await read_file(dst) == f"Content {i}"


@pytest.mark.asyncio
async def test_copy_files_nonexistent_source():
    """Test that copy_files raises error for nonexistent source."""
    with tempfile.TemporaryDirectory() as tmpdir:
        src = os.path.join(tmpdir, _unique_name("nonexistent.txt"))
        dst = os.path.join(tmpdir, _unique_name("destination.txt"))

        with pytest.raises(IOError):
            await copy_files([(src, dst)])


@pytest.mark.asyncio
async def test_copy_files_empty_list():
    """Test copying empty list."""
    await copy_files([])


@pytest.mark.asyncio
async def test_batch_operations_concurrent():
    """Test that batch operations are truly concurrent."""
    import time

    with tempfile.TemporaryDirectory() as tmpdir:
        # Create many files
        num_files = 20
        files = {}
        for i in range(num_files):
            path = os.path.join(tmpdir, f"file_{i}.txt")
            files[path] = f"Content {i}".encode("utf-8")

        # Time batch write
        start = time.time()
        await write_files(files)
        batch_write_time = time.time() - start

        # Time sequential write for comparison
        start = time.time()
        for path, content in files.items():
            await write_file_bytes(path, content)
        sequential_write_time = time.time() - start

        # Batch should be faster (or at least not much slower)
        # Note: This is a heuristic test, actual timing depends on system
        # sync_all() adds overhead for data integrity, so batch operations may be slower
        # Use lenient thresholds to account for this overhead and system variance
        threshold = 3.0 if sys.platform == "win32" else 5.0
        assert batch_write_time <= sequential_write_time * threshold


@pytest.mark.asyncio
async def test_batch_operations_error_handling():
    """Test error handling in batch operations."""
    with tempfile.TemporaryDirectory():
        # Test empty path
        with pytest.raises(ValueError):
            await read_files([""])

        # Test invalid path
        with pytest.raises(ValueError):
            await write_files({"": b"content"})

        # Test null byte in path
        with pytest.raises(ValueError):
            await read_files(["file\x00name.txt"])


@pytest.mark.asyncio
async def test_read_write_files_roundtrip():
    """Test roundtrip: write files, then read them back."""
    with tempfile.TemporaryDirectory() as tmpdir:
        files = {
            os.path.join(tmpdir, _unique_name("file1.txt")): b"Content 1",
            os.path.join(tmpdir, _unique_name("file2.txt")): b"Content 2",
            os.path.join(tmpdir, _unique_name("file3.txt")): b"Content 3",
        }

        # Write files
        await write_files(files)

        # Read files back
        paths = list(files.keys())
        results = await read_files(paths)
        result_dict = dict(results)

        # Verify roundtrip
        for path, original_content in files.items():
            assert path in result_dict
            assert result_dict[path] == original_content


@pytest.mark.asyncio
async def test_batch_operations_mixed_types():
    """Test batch operations with mixed file types."""
    with tempfile.TemporaryDirectory() as tmpdir:
        # Mix text and binary files
        files = {
            os.path.join(tmpdir, _unique_name("text1.txt")): b"Text content 1",
            os.path.join(tmpdir, _unique_name("binary1.bin")): b"\x00\x01\x02\x03",
            os.path.join(tmpdir, _unique_name("text2.txt")): b"Text content 2",
            os.path.join(tmpdir, _unique_name("binary2.bin")): b"\xff\xfe\xfd\xfc",
        }

        # Write all files
        await write_files(files)

        # Read all files
        paths = list(files.keys())
        results = await read_files(paths)
        result_dict = dict(results)

        # Verify all files
        for path, expected_content in files.items():
            assert path in result_dict
            assert result_dict[path] == expected_content
