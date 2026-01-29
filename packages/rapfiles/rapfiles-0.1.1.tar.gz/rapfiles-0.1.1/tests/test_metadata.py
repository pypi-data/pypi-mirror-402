"""Test file metadata operations."""

import pytest
import tempfile
import os
import time

from rapfiles import stat, metadata, FileMetadata


@pytest.mark.asyncio
async def test_stat():
    """Test getting file statistics."""
    with tempfile.NamedTemporaryFile(mode="w", delete=False, suffix=".txt") as f:
        test_file = f.name
        f.write("test content")

    try:
        stat_result = await stat(test_file)
        
        assert isinstance(stat_result, FileMetadata)
        assert stat_result.size > 0
        assert stat_result.is_file is True
        assert stat_result.is_dir is False
        assert stat_result.modified > 0
        assert stat_result.accessed > 0
    finally:
        if os.path.exists(test_file):
            os.unlink(test_file)


@pytest.mark.asyncio
async def test_metadata():
    """Test getting file metadata (alias for stat)."""
    with tempfile.NamedTemporaryFile(mode="w", delete=False, suffix=".txt") as f:
        test_file = f.name
        f.write("test content")

    try:
        meta = await metadata(test_file)
        
        assert isinstance(meta, FileMetadata)
        assert meta.size > 0
        assert meta.is_file is True
    finally:
        if os.path.exists(test_file):
            os.unlink(test_file)


@pytest.mark.asyncio
async def test_stat_directory():
    """Test getting directory statistics."""
    with tempfile.TemporaryDirectory() as tmpdir:
        stat_result = await stat(tmpdir)
        
        assert isinstance(stat_result, FileMetadata)
        assert stat_result.is_dir is True
        assert stat_result.is_file is False


@pytest.mark.asyncio
async def test_stat_properties():
    """Test FileMetadata properties."""
    with tempfile.NamedTemporaryFile(mode="w", delete=False, suffix=".txt") as f:
        test_file = f.name
        f.write("test")

    try:
        stat_result = await stat(test_file)
        
        # Test property access
        size = stat_result.size
        is_file = stat_result.is_file
        is_dir = stat_result.is_dir
        modified = stat_result.modified
        accessed = stat_result.accessed
        created = stat_result.created
        
        assert isinstance(size, int)
        assert isinstance(is_file, bool)
        assert isinstance(is_dir, bool)
        assert isinstance(modified, float)
        assert isinstance(accessed, float)
        assert isinstance(created, float)
    finally:
        if os.path.exists(test_file):
            os.unlink(test_file)
