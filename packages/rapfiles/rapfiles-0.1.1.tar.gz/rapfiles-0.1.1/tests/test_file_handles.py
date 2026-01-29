"""Test file handle operations."""

import pytest
import tempfile
import os

from rapfiles import open, AsyncFile


@pytest.mark.asyncio
async def test_open_read():
    """Test opening and reading a file."""
    with tempfile.NamedTemporaryFile(mode="w", delete=False, suffix=".txt") as f:
        test_file = f.name
        f.write("test content")

    try:
        async with open(test_file, "r") as file:
            content = await file.read()
            assert content == "test content"
    finally:
        if os.path.exists(test_file):
            os.unlink(test_file)


@pytest.mark.asyncio
async def test_open_write():
    """Test opening and writing to a file."""
    with tempfile.NamedTemporaryFile(mode="w", delete=False, suffix=".txt") as f:
        test_file = f.name

    try:
        async with open(test_file, "w") as file:
            await file.write("new content")
        
        # Verify write
        async with open(test_file, "r") as file:
            content = await file.read()
            assert content == "new content"
    finally:
        if os.path.exists(test_file):
            os.unlink(test_file)


@pytest.mark.asyncio
async def test_open_binary():
    """Test opening a file in binary mode."""
    with tempfile.NamedTemporaryFile(mode="wb", delete=False, suffix=".bin") as f:
        test_file = f.name
        f.write(b"binary content")

    try:
        async with open(test_file, "rb") as file:
            content = await file.read()
            assert content == b"binary content"
            assert isinstance(content, bytes)
    finally:
        if os.path.exists(test_file):
            os.unlink(test_file)


@pytest.mark.asyncio
async def test_readline():
    """Test reading a line from a file."""
    with tempfile.NamedTemporaryFile(mode="w", delete=False, suffix=".txt") as f:
        test_file = f.name
        f.write("line 1\nline 2\nline 3")

    try:
        async with open(test_file, "r") as file:
            line1 = await file.readline()
            # Normalize line endings for cross-platform compatibility
            assert line1.rstrip('\r\n') == "line 1" and line1.endswith(('\n', '\r\n'))
            line2 = await file.readline()
            assert line2.rstrip('\r\n') == "line 2" and line2.endswith(('\n', '\r\n'))
            line3 = await file.readline()
            assert line3 == "line 3"
    finally:
        if os.path.exists(test_file):
            os.unlink(test_file)


@pytest.mark.asyncio
async def test_readlines():
    """Test reading all lines from a file."""
    with tempfile.NamedTemporaryFile(mode="w", delete=False, suffix=".txt") as f:
        test_file = f.name
        f.write("line 1\nline 2\nline 3\n")

    try:
        async with open(test_file, "r") as file:
            lines = await file.readlines()
            # Normalize line endings for cross-platform compatibility (Windows uses \r\n)
            # Replace \r\n with \n to match expected format
            normalized_lines = [line.replace('\r\n', '\n').replace('\r', '\n') for line in lines]
            assert normalized_lines == ["line 1\n", "line 2\n", "line 3\n"]
    finally:
        if os.path.exists(test_file):
            os.unlink(test_file)


@pytest.mark.asyncio
async def test_seek_tell():
    """Test seeking and telling position in a file."""
    with tempfile.NamedTemporaryFile(mode="w", delete=False, suffix=".txt") as f:
        test_file = f.name
        f.write("0123456789")

    try:
        async with open(test_file, "r") as file:
            pos = await file.tell()
            assert pos == 0
            
            content = await file.read(5)
            assert content == "01234"
            
            pos = await file.tell()
            assert pos == 5
            
            new_pos = await file.seek(0, 0)  # SEEK_SET
            assert new_pos == 0
            
            content = await file.read(3)
            assert content == "012"
    finally:
        if os.path.exists(test_file):
            os.unlink(test_file)


@pytest.mark.asyncio
async def test_append_mode():
    """Test appending to a file."""
    with tempfile.NamedTemporaryFile(mode="w", delete=False, suffix=".txt") as f:
        test_file = f.name
        f.write("initial")

    try:
        async with open(test_file, "a") as file:
            await file.write(" appended")
        
        async with open(test_file, "r") as file:
            content = await file.read()
            assert content == "initial appended"
    finally:
        if os.path.exists(test_file):
            os.unlink(test_file)


@pytest.mark.asyncio
async def test_read_size():
    """Test reading a specific size from a file."""
    with tempfile.NamedTemporaryFile(mode="w", delete=False, suffix=".txt") as f:
        test_file = f.name
        f.write("0123456789")

    try:
        async with open(test_file, "r") as file:
            content = await file.read(5)
            assert content == "01234"
            content = await file.read(3)
            assert content == "567"
    finally:
        if os.path.exists(test_file):
            os.unlink(test_file)
