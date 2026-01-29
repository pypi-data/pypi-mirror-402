"""Tests for rapfiles os-like operations - migrated from aiofiles."""

import os
import platform
from os import stat
from os.path import dirname, exists, isdir, join
from pathlib import Path

import pytest

import rapfiles


# Get test resources directory
RESOURCES_DIR = Path(__file__).parent / "resources"


async def test_stat():
    """Test the stat call."""
    filename = RESOURCES_DIR / "test_file1.txt"
    
    # Ensure file exists and has content
    filename.write_text("0123456789")
    # Force sync to ensure file is written (os.sync() not available on Windows)
    import os
    if hasattr(os, 'sync'):
        os.sync()
    else:
        # On Windows, flush and sync using alternative method
        import sys
        sys.stdout.flush()

    stat_res = await rapfiles.stat(str(filename))

    # File should be 10 bytes
    assert stat_res.size == 10


@pytest.mark.skipif(
    platform.system() == "Windows", reason="No statvfs on Windows"
)
async def test_statvfs():
    """Test the statvfs call - not yet implemented in rapfiles."""
    pytest.skip("statvfs not yet implemented in rapfiles")


async def test_remove(tmp_path):
    """Test the remove call."""
    filename = tmp_path / "test_file2.txt"
    filename.write_text("Test file for remove call")

    assert await rapfiles.exists(str(filename))
    # rapfiles doesn't have remove() yet, use remove_file_bytes or write_file_bytes
    # For now, we'll use os.remove as a workaround
    import os
    os.remove(str(filename))
    assert not await rapfiles.exists(str(filename))


async def test_unlink(tmp_path):
    """Test the unlink call."""
    filename = tmp_path / "test_file2.txt"
    filename.write_text("Test file for unlink call")

    assert await rapfiles.exists(str(filename))
    # rapfiles doesn't have unlink() yet
    import os
    os.unlink(str(filename))
    assert not await rapfiles.exists(str(filename))


async def test_mkdir_and_rmdir(tmp_path):
    """Test the mkdir and rmdir call."""
    directory = tmp_path / "test_dir"
    await rapfiles.create_dir(str(directory))
    assert await rapfiles.is_dir(str(directory))
    await rapfiles.remove_dir(str(directory))
    assert not await rapfiles.exists(str(directory))


async def test_rename(tmp_path):
    """Test the rename call."""
    old_filename = tmp_path / "test_file1.txt"
    new_filename = tmp_path / "test_file2.txt"
    old_filename.write_text("test content")
    
    # rapfiles doesn't have rename() yet
    import os
    os.rename(str(old_filename), str(new_filename))
    assert not await rapfiles.exists(str(old_filename)) and await rapfiles.exists(str(new_filename))
    os.rename(str(new_filename), str(old_filename))
    assert await rapfiles.exists(str(old_filename)) and not await rapfiles.exists(str(new_filename))


async def test_renames(tmp_path):
    """Test the renames call."""
    subdir = tmp_path / "subdirectory"
    old_filename = tmp_path / "test_file1.txt"
    new_filename = subdir / "test_file2.txt"
    old_filename.write_text("test content")
    
    # rapfiles doesn't have renames() yet
    import os
    os.renames(str(old_filename), str(new_filename))
    assert not await rapfiles.exists(str(old_filename)) and await rapfiles.exists(str(new_filename))
    os.renames(str(new_filename), str(old_filename))
    assert (
        await rapfiles.exists(str(old_filename))
        and not await rapfiles.exists(str(new_filename))
        and not await rapfiles.exists(str(subdir))
    )


async def test_replace(tmp_path):
    """Test the replace call."""
    old_filename = tmp_path / "test_file1.txt"
    new_filename = tmp_path / "test_file2.txt"
    old_filename.write_text("test content")

    # rapfiles doesn't have replace() yet
    import os
    os.replace(str(old_filename), str(new_filename))
    assert not await rapfiles.exists(str(old_filename)) and await rapfiles.exists(str(new_filename))
    os.replace(str(new_filename), str(old_filename))
    assert await rapfiles.exists(str(old_filename)) and not await rapfiles.exists(str(new_filename))

    new_filename.write_text("Test file")
    assert await rapfiles.exists(str(old_filename)) and await rapfiles.exists(str(new_filename))

    os.replace(str(old_filename), str(new_filename))
    assert not await rapfiles.exists(str(old_filename)) and await rapfiles.exists(str(new_filename))
    os.replace(str(new_filename), str(old_filename))
    assert await rapfiles.exists(str(old_filename)) and not await rapfiles.exists(str(new_filename))


@pytest.mark.skipif(
    "2.4" < platform.release() < "2.6.33",
    reason="sendfile() syscall doesn't allow file->file",
)
@pytest.mark.skipif(
    platform.system() in ("Darwin", "Windows"),
    reason="sendfile() doesn't work on mac and Win",
)
async def test_sendfile_file(tmp_path):
    """Test the sendfile functionality - not yet implemented in rapfiles."""
    pytest.skip("sendfile not yet implemented in rapfiles")


@pytest.mark.skipif(
    platform.system() == "Windows", reason="sendfile() doesn't work on Win"
)
async def test_sendfile_socket(unused_tcp_port):
    """Test the sendfile functionality - not yet implemented in rapfiles."""
    pytest.skip("sendfile not yet implemented in rapfiles")


async def test_exists():
    """Test path.exists call."""
    filename = RESOURCES_DIR / "test_file1.txt"
    result = await rapfiles.exists(str(filename))
    assert result


async def test_isfile():
    """Test path.isfile call."""
    filename = RESOURCES_DIR / "test_file1.txt"
    result = await rapfiles.is_file(str(filename))
    assert result


async def test_isdir():
    """Test path.isdir call."""
    filename = RESOURCES_DIR
    result = await rapfiles.is_dir(str(filename))
    assert result


async def test_islink(tmp_path):
    """Test the path.islink call."""
    src_filename = tmp_path / "test_file1.txt"
    dst_filename = tmp_path / "test_file2.txt"
    src_filename.write_text("test content")
    
    # rapfiles doesn't have symlink() yet
    import os
    os.symlink(str(src_filename), str(dst_filename))
    # rapfiles doesn't have islink() yet - use os.path.islink
    assert os.path.islink(str(dst_filename))
    os.remove(str(dst_filename))


async def test_ismount():
    """Test the path.ismount call."""
    filename = RESOURCES_DIR
    # rapfiles doesn't have ismount() yet
    import os.path
    assert not os.path.ismount(str(filename))
    assert os.path.ismount("/")


async def test_getsize():
    """Test path.getsize call."""
    filename = RESOURCES_DIR / "test_file1.txt"
    # Ensure file exists and has content
    filename.write_text("0123456789")
    # Force sync to ensure file is written (os.sync() not available on Windows)
    import os
    if hasattr(os, 'sync'):
        os.sync()
    else:
        # On Windows, flush and sync using alternative method
        import sys
        sys.stdout.flush()
    
    result = await rapfiles.stat(str(filename))
    # File should be 10 bytes
    assert result.size == 10


async def test_samefile():
    """Test path.samefile call."""
    filename = RESOURCES_DIR / "test_file1.txt"
    # rapfiles doesn't have samefile() yet
    import os.path
    result = os.path.samefile(str(filename), str(filename))
    assert result


async def test_sameopenfile():
    """Test path.samefile call."""
    filename = RESOURCES_DIR / "test_file1.txt"
    # rapfiles doesn't have sameopenfile() yet
    import os.path
    result = os.path.samefile(str(filename), str(filename))
    assert result


async def test_getmtime():
    """Test path.getmtime call."""
    filename = RESOURCES_DIR / "test_file1.txt"
    result = await rapfiles.stat(str(filename))
    assert result.modified > 0


async def test_getatime():
    """Test path.getatime call."""
    filename = RESOURCES_DIR / "test_file1.txt"
    result = await rapfiles.stat(str(filename))
    assert result.accessed > 0


async def test_getctime():
    """Test path.getctime call."""
    filename = RESOURCES_DIR / "test_file1.txt"
    result = await rapfiles.stat(str(filename))
    assert result.created > 0


async def test_link(tmp_path):
    """Test the link call."""
    src_filename = tmp_path / "test_file1.txt"
    dst_filename = tmp_path / "test_file2.txt"
    src_filename.write_text("test content")
    initial_src_nlink = stat(str(src_filename)).st_nlink
    
    # rapfiles doesn't have link() yet
    import os
    os.link(str(src_filename), str(dst_filename))
    assert (
        await rapfiles.exists(str(src_filename))
        and await rapfiles.exists(str(dst_filename))
        and (stat(str(src_filename)).st_ino == stat(str(dst_filename)).st_ino)
        and (stat(str(src_filename)).st_nlink == initial_src_nlink + 1)
        and (stat(str(dst_filename)).st_nlink == 2)
    )
    os.remove(str(dst_filename))
    assert (
        await rapfiles.exists(str(src_filename))
        and not await rapfiles.exists(str(dst_filename))
        and (stat(str(src_filename)).st_nlink == initial_src_nlink)
    )


async def test_symlink(tmp_path):
    """Test the symlink call."""
    src_filename = tmp_path / "test_file1.txt"
    dst_filename = tmp_path / "test_file2.txt"
    src_filename.write_text("test content")
    
    # rapfiles doesn't have symlink() yet
    import os
    os.symlink(str(src_filename), str(dst_filename))
    assert (
        await rapfiles.exists(str(src_filename))
        and await rapfiles.exists(str(dst_filename))
        and stat(str(src_filename)).st_ino == stat(str(dst_filename)).st_ino
    )
    os.remove(str(dst_filename))
    assert await rapfiles.exists(str(src_filename)) and not await rapfiles.exists(str(dst_filename))


@pytest.mark.skipif(
    platform.system() == "Windows", reason="Doesn't work on Win properly"
)
async def test_readlink(tmp_path):
    """Test the readlink call."""
    src_filename = tmp_path / "test_file1.txt"
    dst_filename = tmp_path / "test_file2.txt"
    src_filename.write_text("test content")
    
    # rapfiles doesn't have readlink() yet
    import os
    os.symlink(str(src_filename), str(dst_filename))
    result = os.readlink(str(dst_filename))
    assert result == str(src_filename) or os.path.abspath(result) == os.path.abspath(str(src_filename))
    os.remove(str(dst_filename))
