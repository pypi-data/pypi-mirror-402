"""Test extended file operations."""

import pytest
import tempfile
import os

from rapfiles import (
    read_file,
    write_file,
    read_file_bytes,
    write_file_bytes,
    append_file,
)


@pytest.mark.asyncio
async def test_read_file_bytes():
    """Test reading a file as bytes."""
    with tempfile.NamedTemporaryFile(mode="wb", delete=False, suffix=".bin") as f:
        test_file = f.name
        f.write(b"binary content")

    try:
        content = await read_file_bytes(test_file)
        assert content == b"binary content"
        assert isinstance(content, bytes)
    finally:
        if os.path.exists(test_file):
            os.unlink(test_file)


@pytest.mark.asyncio
async def test_write_file_bytes():
    """Test writing bytes to a file."""
    with tempfile.NamedTemporaryFile(mode="wb", delete=False, suffix=".bin") as f:
        test_file = f.name

    try:
        await write_file_bytes(test_file, b"binary content")
        
        # Verify write
        with open(test_file, "rb") as f:
            content = f.read()
            assert content == b"binary content"
    finally:
        if os.path.exists(test_file):
            os.unlink(test_file)


@pytest.mark.asyncio
async def test_append_file():
    """Test appending to a file."""
    with tempfile.NamedTemporaryFile(mode="w", delete=False, suffix=".txt") as f:
        test_file = f.name
        f.write("initial")

    try:
        await append_file(test_file, " appended")
        
        # Verify append
        content = await read_file(test_file)
        assert content == "initial appended"
    finally:
        if os.path.exists(test_file):
            os.unlink(test_file)


@pytest.mark.asyncio
async def test_append_file_multiple():
    """Test appending multiple times."""
    with tempfile.NamedTemporaryFile(mode="w", delete=False, suffix=".txt") as f:
        test_file = f.name
        f.write("start")

    try:
        await append_file(test_file, " middle")
        await append_file(test_file, " end")
        
        content = await read_file(test_file)
        assert content == "start middle end"
    finally:
        if os.path.exists(test_file):
            os.unlink(test_file)


@pytest.mark.asyncio
async def test_read_write_roundtrip_bytes():
    """Test reading and writing bytes in sequence."""
    with tempfile.NamedTemporaryFile(mode="wb", delete=False, suffix=".bin") as f:
        test_file = f.name

    try:
        # Write bytes
        await write_file_bytes(test_file, b"initial bytes")
        
        # Read bytes
        content = await read_file_bytes(test_file)
        assert content == b"initial bytes"
        
        # Write new bytes
        await write_file_bytes(test_file, b"new bytes")
        
        # Read new bytes
        content = await read_file_bytes(test_file)
        assert content == b"new bytes"
    finally:
        if os.path.exists(test_file):
            os.unlink(test_file)
