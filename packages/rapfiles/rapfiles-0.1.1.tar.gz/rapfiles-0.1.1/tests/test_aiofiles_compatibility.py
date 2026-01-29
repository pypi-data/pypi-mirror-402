"""Test aiofiles API compatibility."""

import pytest
import tempfile
import os

# Test that rapfiles can be used as a drop-in replacement for aiofiles
# by importing it as aiofiles and using the same API


@pytest.mark.asyncio
async def test_open_compatibility():
    """Test that open() matches aiofiles.open() signature."""
    import rapfiles as aiofiles
    
    with tempfile.NamedTemporaryFile(mode="w", delete=False, suffix=".txt") as f:
        test_file = f.name
        f.write("test content")

    try:
        # Test basic open and read (aiofiles pattern)
        async with aiofiles.open(test_file, "r") as f:
            content = await f.read()
            assert content == "test content"
        
        # Test write
        async with aiofiles.open(test_file, "w") as f:
            await f.write("new content")
        
        # Verify
        async with aiofiles.open(test_file, "r") as f:
            content = await f.read()
            assert content == "new content"
    finally:
        if os.path.exists(test_file):
            os.unlink(test_file)


@pytest.mark.asyncio
async def test_file_handle_methods():
    """Test that file handle methods match aiofiles API."""
    import rapfiles as aiofiles
    
    with tempfile.NamedTemporaryFile(mode="w", delete=False, suffix=".txt") as f:
        test_file = f.name
        f.write("line 1\nline 2\nline 3")

    try:
        async with aiofiles.open(test_file, "r") as f:
            # Test read()
            content = await f.read()
            assert isinstance(content, str)
            
            # Reset and test readline()
            await f.seek(0)
            line = await f.readline()
            # Normalize line endings for cross-platform compatibility
            assert line.rstrip('\r\n') == "line 1" and line.endswith(('\n', '\r\n'))
            
            # Test readlines()
            await f.seek(0)
            lines = await f.readlines()
            assert len(lines) == 3
            
            # Test seek() and tell()
            await f.seek(0)
            pos = await f.tell()
            assert pos == 0
            
            await f.seek(5)
            pos = await f.tell()
            assert pos == 5
    finally:
        if os.path.exists(test_file):
            os.unlink(test_file)


@pytest.mark.asyncio
async def test_ospath_compatibility():
    """Test that rapfiles.ospath matches aiofiles.ospath API."""
    import rapfiles
    
    with tempfile.NamedTemporaryFile(mode="w", delete=False, suffix=".txt") as f:
        test_file = f.name
        f.write("test")

    try:
        # Test ospath functions
        assert rapfiles.ospath.exists(test_file) is True
        assert rapfiles.ospath.isfile(test_file) is True
        assert rapfiles.ospath.isdir(test_file) is False
        assert rapfiles.ospath.getsize(test_file) > 0
        
        # Test path operations
        joined = rapfiles.ospath.join("dir", "file.txt")
        assert "dir" in joined
        assert "file.txt" in joined
        
        abspath = rapfiles.ospath.abspath(test_file)
        assert os.path.isabs(abspath)
        
        dirname = rapfiles.ospath.dirname(test_file)
        basename = rapfiles.ospath.basename(test_file)
        assert basename in test_file
    finally:
        if os.path.exists(test_file):
            os.unlink(test_file)


@pytest.mark.asyncio
async def test_binary_mode():
    """Test binary mode compatibility with aiofiles."""
    import rapfiles as aiofiles
    
    with tempfile.NamedTemporaryFile(mode="wb", delete=False, suffix=".bin") as f:
        test_file = f.name
        f.write(b"binary content")

    try:
        async with aiofiles.open(test_file, "rb") as f:
            content = await f.read()
            assert content == b"binary content"
            assert isinstance(content, bytes)
    finally:
        if os.path.exists(test_file):
            os.unlink(test_file)


@pytest.mark.asyncio
async def test_context_manager():
    """Test async context manager compatibility."""
    import rapfiles as aiofiles
    
    with tempfile.NamedTemporaryFile(mode="w", delete=False, suffix=".txt") as f:
        test_file = f.name

    try:
        # Test that context manager works
        async with aiofiles.open(test_file, "w") as f:
            await f.write("content")
        
        # File should be closed after context exit
        async with aiofiles.open(test_file, "r") as f:
            content = await f.read()
            assert content == "content"
    finally:
        if os.path.exists(test_file):
            os.unlink(test_file)
