"""Test rapfiles async functionality."""

import pytest
import tempfile
import os

from rapfiles import read_file, write_file


@pytest.mark.asyncio
async def test_read_file():
    """Test async file read operation."""
    # Create a temporary file with content
    with tempfile.NamedTemporaryFile(mode="w", delete=False, suffix=".txt") as f:
        test_file = f.name
        f.write("test content")

    try:
        content = await read_file(test_file)
        assert content == "test content", f"Expected 'test content', got '{content}'"
    finally:
        if os.path.exists(test_file):
            os.unlink(test_file)


@pytest.mark.asyncio
async def test_write_file():
    """Test async file write operation."""
    with tempfile.NamedTemporaryFile(mode="w", delete=False, suffix=".txt") as f:
        test_file = f.name

    try:
        await write_file(test_file, "new content")
        # Verify write
        with open(test_file, "r") as f:
            content = f.read()
        assert content == "new content", f"Expected 'new content', got '{content}'"
    finally:
        if os.path.exists(test_file):
            os.unlink(test_file)


@pytest.mark.asyncio
async def test_read_write_roundtrip():
    """Test reading and writing in sequence."""
    with tempfile.NamedTemporaryFile(mode="w", delete=False, suffix=".txt") as f:
        test_file = f.name
        f.write("initial content")

    try:
        # Read initial content
        content = await read_file(test_file)
        assert content == "initial content"

        # Write new content
        await write_file(test_file, "updated content")

        # Read updated content
        content = await read_file(test_file)
        assert content == "updated content"
    finally:
        if os.path.exists(test_file):
            os.unlink(test_file)
