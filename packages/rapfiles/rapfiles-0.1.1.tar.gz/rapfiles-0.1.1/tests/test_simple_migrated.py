"""Simple tests migrated from aiofiles - basic functionality verification."""

import asyncio
import os
from pathlib import Path

import pytest

import rapfiles


async def test_serve_small_bin_file_sync(tmp_path, unused_tcp_port):
    """Fire up a small simple file server, and fetch a file.

    The file is read into memory synchronously, so this test doesn't actually
    test anything except the general test concept.
    """
    # First we'll write a small file.
    filename = "test.bin"
    file_content = b"0123456789"
    file_path = tmp_path / filename
    file_path.write_bytes(file_content)

    async def serve_file(reader, writer):
        full_filename = str(file_path)
        with open(full_filename, "rb") as f:
            writer.write(f.read())
        writer.close()

    server = await asyncio.start_server(serve_file, port=unused_tcp_port)

    reader, _ = await asyncio.open_connection(host="localhost", port=unused_tcp_port)
    payload = await reader.read()

    assert payload == file_content

    server.close()
    await server.wait_closed()


async def test_serve_small_bin_file(tmp_path, unused_tcp_port):
    """Fire up a small simple file server, and fetch a file using rapfiles."""
    # First we'll write a small file.
    filename = "test.bin"
    file_content = b"0123456789"
    file_path = tmp_path / filename
    file_path.write_bytes(file_content)

    async def serve_file(reader, writer):
        full_filename = str(file_path)
        async with rapfiles.open(full_filename, mode="rb") as f:
            data = await f.read()
            writer.write(data)
        writer.close()

    server = await asyncio.start_server(serve_file, port=unused_tcp_port)

    reader, _ = await asyncio.open_connection(host="localhost", port=unused_tcp_port)
    payload = await reader.read()

    assert payload == file_content

    server.close()
    await server.wait_closed()
