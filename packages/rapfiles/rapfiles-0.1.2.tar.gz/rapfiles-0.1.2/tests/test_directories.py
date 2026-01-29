"""Test directory operations."""

import pytest
import tempfile
import os

from rapfiles import (
    create_dir,
    create_dir_all,
    remove_dir,
    remove_dir_all,
    list_dir,
    exists,
    is_file,
    is_dir,
    walk_dir,
)


@pytest.mark.asyncio
async def test_create_dir():
    """Test creating a directory."""
    with tempfile.TemporaryDirectory() as tmpdir:
        test_dir = os.path.join(tmpdir, "test_dir")
        
        await create_dir(test_dir)
        assert os.path.exists(test_dir)
        assert os.path.isdir(test_dir)


@pytest.mark.asyncio
async def test_create_dir_all():
    """Test creating nested directories."""
    with tempfile.TemporaryDirectory() as tmpdir:
        test_dir = os.path.join(tmpdir, "level1", "level2", "level3")
        
        await create_dir_all(test_dir)
        assert os.path.exists(test_dir)
        assert os.path.isdir(test_dir)


@pytest.mark.asyncio
async def test_remove_dir():
    """Test removing an empty directory."""
    with tempfile.TemporaryDirectory() as tmpdir:
        test_dir = os.path.join(tmpdir, "test_dir")
        os.mkdir(test_dir)
        
        await remove_dir(test_dir)
        assert not os.path.exists(test_dir)


@pytest.mark.asyncio
async def test_remove_dir_all():
    """Test removing a directory tree."""
    with tempfile.TemporaryDirectory() as tmpdir:
        test_dir = os.path.join(tmpdir, "test_dir")
        os.makedirs(os.path.join(test_dir, "subdir"))
        
        await remove_dir_all(test_dir)
        assert not os.path.exists(test_dir)


@pytest.mark.asyncio
async def test_list_dir():
    """Test listing directory contents."""
    with tempfile.TemporaryDirectory() as tmpdir:
        # Create test files
        with open(os.path.join(tmpdir, "file1.txt"), "w") as f:
            f.write("content1")
        with open(os.path.join(tmpdir, "file2.txt"), "w") as f:
            f.write("content2")
        os.mkdir(os.path.join(tmpdir, "subdir"))
        
        entries = await list_dir(tmpdir)
        assert "file1.txt" in entries
        assert "file2.txt" in entries
        assert "subdir" in entries
        assert len(entries) == 3


@pytest.mark.asyncio
async def test_exists():
    """Test checking if a path exists."""
    with tempfile.TemporaryDirectory() as tmpdir:
        test_file = os.path.join(tmpdir, "test.txt")
        with open(test_file, "w") as f:
            f.write("test")
        
        assert await exists(test_file) is True
        assert await exists(os.path.join(tmpdir, "nonexistent")) is False


@pytest.mark.asyncio
async def test_is_file():
    """Test checking if a path is a file."""
    with tempfile.TemporaryDirectory() as tmpdir:
        test_file = os.path.join(tmpdir, "test.txt")
        with open(test_file, "w") as f:
            f.write("test")
        
        assert await is_file(test_file) is True
        assert await is_file(tmpdir) is False


@pytest.mark.asyncio
async def test_is_dir():
    """Test checking if a path is a directory."""
    with tempfile.TemporaryDirectory() as tmpdir:
        test_file = os.path.join(tmpdir, "test.txt")
        with open(test_file, "w") as f:
            f.write("test")
        
        assert await is_dir(tmpdir) is True
        assert await is_dir(test_file) is False


@pytest.mark.asyncio
async def test_walk_dir():
    """Test walking a directory tree."""
    with tempfile.TemporaryDirectory() as tmpdir:
        # Create directory structure
        os.makedirs(os.path.join(tmpdir, "subdir1", "subdir2"))
        with open(os.path.join(tmpdir, "file1.txt"), "w") as f:
            f.write("content1")
        with open(os.path.join(tmpdir, "subdir1", "file2.txt"), "w") as f:
            f.write("content2")
        
        results = await walk_dir(tmpdir)
        
        # Check that we found all files and directories
        paths = [path for path, is_file in results]
        assert any("file1.txt" in p for p in paths)
        assert any("file2.txt" in p for p in paths)
        assert any("subdir1" in p for p in paths)
        assert any("subdir2" in p for p in paths)
