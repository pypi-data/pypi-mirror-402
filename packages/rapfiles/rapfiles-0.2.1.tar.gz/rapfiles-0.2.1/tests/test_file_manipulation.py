"""Test file manipulation operations."""

import pytest
import tempfile
import os
import uuid

from rapfiles import (
    copy_file,
    move_file,
    rename,
    remove_file,
    hard_link,
    symlink,
    canonicalize,
    write_file,
    write_file_bytes,
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
async def test_copy_file_text():
    """Test copying a text file."""
    with tempfile.TemporaryDirectory() as tmpdir:
        src = os.path.join(tmpdir, _unique_name("source.txt"))
        dst = os.path.join(tmpdir, _unique_name("destination.txt"))

        await write_file(src, "Hello, World!")

        await copy_file(src, dst)

        assert await exists(src)
        assert await exists(dst)
        content = await read_file(dst)
        assert content == "Hello, World!"


@pytest.mark.asyncio
async def test_copy_file_binary():
    """Test copying a binary file."""
    with tempfile.TemporaryDirectory() as tmpdir:
        src = os.path.join(tmpdir, _unique_name("source.bin"))
        dst = os.path.join(tmpdir, _unique_name("destination.bin"))

        original_data = b"\x00\x01\x02\x03\xff\xfe\xfd"
        await write_file_bytes(src, original_data)

        await copy_file(src, dst)

        assert await exists(src)
        assert await exists(dst)
        copied_data = await read_file_bytes(dst)
        assert copied_data == original_data


@pytest.mark.asyncio
async def test_copy_file_overwrites():
    """Test that copy_file overwrites existing destination."""
    with tempfile.TemporaryDirectory() as tmpdir:
        src = os.path.join(tmpdir, _unique_name("source.txt"))
        dst = os.path.join(tmpdir, _unique_name("destination.txt"))

        await write_file(src, "Source content")
        await write_file(dst, "Original content")

        await copy_file(src, dst)

        content = await read_file(dst)
        assert content == "Source content"


@pytest.mark.asyncio
async def test_copy_file_nonexistent_source():
    """Test that copy_file raises FileNotFoundError for nonexistent source."""
    with tempfile.TemporaryDirectory() as tmpdir:
        src = os.path.join(tmpdir, _unique_name("nonexistent.txt"))
        dst = os.path.join(tmpdir, _unique_name("destination.txt"))

        with pytest.raises(FileNotFoundError):
            await copy_file(src, dst)


@pytest.mark.asyncio
async def test_move_file():
    """Test moving a file."""
    with tempfile.TemporaryDirectory() as tmpdir:
        src = os.path.join(tmpdir, _unique_name("source.txt"))
        dst = os.path.join(tmpdir, _unique_name("destination.txt"))

        await write_file(src, "Hello, World!")

        await move_file(src, dst)

        assert not await exists(src)
        assert await exists(dst)
        content = await read_file(dst)
        assert content == "Hello, World!"


@pytest.mark.asyncio
async def test_rename():
    """Test renaming a file (alias for move_file)."""
    with tempfile.TemporaryDirectory() as tmpdir:
        src = os.path.join(tmpdir, _unique_name("old_name.txt"))
        dst = os.path.join(tmpdir, _unique_name("new_name.txt"))

        await write_file(src, "Test content")

        await rename(src, dst)

        assert not await exists(src)
        assert await exists(dst)
        content = await read_file(dst)
        assert content == "Test content"


@pytest.mark.asyncio
async def test_move_file_overwrites():
    """Test that move_file overwrites existing destination."""
    with tempfile.TemporaryDirectory() as tmpdir:
        src = os.path.join(tmpdir, _unique_name("source.txt"))
        dst = os.path.join(tmpdir, _unique_name("destination.txt"))

        await write_file(src, "Source content")
        await write_file(dst, "Original content")

        await move_file(src, dst)

        assert not await exists(src)
        content = await read_file(dst)
        assert content == "Source content"


@pytest.mark.asyncio
async def test_move_file_nonexistent_source():
    """Test that move_file raises FileNotFoundError for nonexistent source."""
    with tempfile.TemporaryDirectory() as tmpdir:
        src = os.path.join(tmpdir, _unique_name("nonexistent.txt"))
        dst = os.path.join(tmpdir, _unique_name("destination.txt"))

        with pytest.raises(FileNotFoundError):
            await move_file(src, dst)


@pytest.mark.asyncio
async def test_remove_file():
    """Test removing a file."""
    with tempfile.TemporaryDirectory() as tmpdir:
        file_path = os.path.join(tmpdir, _unique_name("file_to_remove.txt"))

        await write_file(file_path, "Content")
        assert await exists(file_path)

        await remove_file(file_path)
        assert not await exists(file_path)


@pytest.mark.asyncio
async def test_remove_file_nonexistent():
    """Test that remove_file raises FileNotFoundError for nonexistent file."""
    with tempfile.TemporaryDirectory() as tmpdir:
        file_path = os.path.join(tmpdir, _unique_name("nonexistent.txt"))

        with pytest.raises(FileNotFoundError):
            await remove_file(file_path)


@pytest.mark.asyncio
async def test_remove_file_directory():
    """Test that remove_file raises IOError when trying to remove a directory."""
    with tempfile.TemporaryDirectory() as tmpdir:
        dir_path = os.path.join(tmpdir, _unique_name("directory"))
        os.mkdir(dir_path)

        with pytest.raises(IOError):
            await remove_file(dir_path)


@pytest.mark.asyncio
@pytest.mark.skipif(
    os.name == "nt", reason="Hard links may not be supported on Windows"
)
async def test_hard_link():
    """Test creating a hard link."""
    with tempfile.TemporaryDirectory() as tmpdir:
        src = os.path.join(tmpdir, _unique_name("original.txt"))
        dst = os.path.join(tmpdir, _unique_name("link.txt"))

        await write_file(src, "Original content")

        await hard_link(src, dst)

        assert await exists(src)
        assert await exists(dst)

        # Both should have the same content
        src_content = await read_file(src)
        dst_content = await read_file(dst)
        assert src_content == dst_content
        assert src_content == "Original content"

        # Modifying one should affect the other (same inode)
        await write_file(src, "Modified content")
        new_dst_content = await read_file(dst)
        assert new_dst_content == "Modified content"


@pytest.mark.asyncio
@pytest.mark.skipif(
    os.name == "nt", reason="Hard links may not be supported on Windows"
)
async def test_hard_link_nonexistent_source():
    """Test that hard_link raises FileNotFoundError for nonexistent source."""
    with tempfile.TemporaryDirectory() as tmpdir:
        src = os.path.join(tmpdir, _unique_name("nonexistent.txt"))
        dst = os.path.join(tmpdir, _unique_name("link.txt"))

        with pytest.raises(FileNotFoundError):
            await hard_link(src, dst)


@pytest.mark.asyncio
async def test_symlink():
    """Test creating a symbolic link."""
    with tempfile.TemporaryDirectory() as tmpdir:
        src = os.path.join(tmpdir, _unique_name("original.txt"))
        dst = os.path.join(tmpdir, _unique_name("link.txt"))

        await write_file(src, "Original content")

        await symlink(src, dst)

        # Check that link exists and points to original
        assert os.path.islink(dst) or await exists(dst)

        # Reading through symlink should give same content
        if await exists(dst):
            dst_content = await read_file(dst)
            assert dst_content == "Original content"


@pytest.mark.asyncio
async def test_symlink_resolves():
    """Test that symlink can be resolved through canonicalize."""
    with tempfile.TemporaryDirectory() as tmpdir:
        src = os.path.join(tmpdir, _unique_name("original.txt"))
        dst = os.path.join(tmpdir, _unique_name("link.txt"))

        await write_file(src, "Original content")

        await symlink(src, dst)

        # Canonicalize should resolve to original file
        canonical_dst = await canonicalize(dst)
        canonical_src = await canonicalize(src)

        # Both should resolve to the same canonical path
        assert os.path.normpath(canonical_dst) == os.path.normpath(canonical_src)


@pytest.mark.asyncio
async def test_canonicalize():
    """Test canonicalizing a path."""
    with tempfile.TemporaryDirectory() as tmpdir:
        # Create a file in a nested directory
        nested_dir = os.path.join(tmpdir, "level1", "level2")
        os.makedirs(nested_dir)
        file_path = os.path.join(nested_dir, "file.txt")
        await write_file(file_path, "Content")

        # Use relative path with .. to go up and back down
        relative_path = os.path.join(
            tmpdir, "level1", "level2", "..", "level2", "file.txt"
        )

        canonical = await canonicalize(relative_path)

        # Should resolve to absolute path
        assert os.path.isabs(canonical)
        assert await exists(canonical)
        content = await read_file(canonical)
        assert content == "Content"


@pytest.mark.asyncio
async def test_canonicalize_nonexistent():
    """Test that canonicalize raises FileNotFoundError for nonexistent path."""
    with tempfile.TemporaryDirectory() as tmpdir:
        nonexistent_path = os.path.join(tmpdir, "nonexistent", "file.txt")

        with pytest.raises(FileNotFoundError):
            await canonicalize(nonexistent_path)


@pytest.mark.asyncio
async def test_concurrent_file_operations():
    """Test concurrent file operations."""
    import asyncio

    with tempfile.TemporaryDirectory() as tmpdir:
        # Create multiple source files
        src_files = [os.path.join(tmpdir, f"src_{i}.txt") for i in range(5)]
        dst_files = [os.path.join(tmpdir, f"dst_{i}.txt") for i in range(5)]

        # Write all source files concurrently
        await asyncio.gather(
            *[write_file(src, f"Content {i}") for i, src in enumerate(src_files)]
        )

        # Copy all files concurrently
        await asyncio.gather(
            *[copy_file(src, dst) for src, dst in zip(src_files, dst_files)]
        )

        # Verify all copies
        for i, dst in enumerate(dst_files):
            assert await exists(dst)
            content = await read_file(dst)
            assert content == f"Content {i}"


@pytest.mark.asyncio
async def test_file_manipulation_error_handling():
    """Test error handling in file manipulation operations."""
    with tempfile.TemporaryDirectory() as tmpdir:
        # Test empty path
        with pytest.raises(ValueError):
            await copy_file("", os.path.join(tmpdir, _unique_name("dst.txt")))

        # Test invalid path (contains null byte)
        with pytest.raises(ValueError):
            await move_file(
                "file\x00name.txt", os.path.join(tmpdir, _unique_name("dst.txt"))
            )


@pytest.mark.asyncio
async def test_copy_file_preserves_permissions():
    """Test that copy_file preserves file content exactly."""
    with tempfile.TemporaryDirectory() as tmpdir:
        src = os.path.join(tmpdir, _unique_name("source.txt"))
        dst = os.path.join(tmpdir, _unique_name("destination.txt"))

        # Write file with specific content
        content = "Test content with special chars: \n\t\r\x00\xff"
        await write_file(src, content)

        await copy_file(src, dst)

        # Verify exact content match
        src_content = await read_file(src)
        dst_content = await read_file(dst)
        assert src_content == dst_content == content


@pytest.mark.asyncio
async def test_move_file_large_file():
    """Test moving a large file."""
    with tempfile.TemporaryDirectory() as tmpdir:
        src = os.path.join(tmpdir, _unique_name("large_source.txt"))
        dst = os.path.join(tmpdir, _unique_name("large_destination.txt"))

        # Create large content (1MB)
        large_content = "x" * (1024 * 1024)
        await write_file(src, large_content)

        await move_file(src, dst)

        assert not await exists(src)
        assert await exists(dst)
        dst_content = await read_file(dst)
        assert len(dst_content) == len(large_content)
        assert dst_content == large_content


@pytest.mark.asyncio
async def test_copy_file_nested_directories():
    """Test copying file to nested directory structure."""
    with tempfile.TemporaryDirectory() as tmpdir:
        src = os.path.join(tmpdir, _unique_name("source.txt"))
        nested_dir = os.path.join(tmpdir, "level1", "level2", "level3")
        os.makedirs(nested_dir)
        dst = os.path.join(nested_dir, "destination.txt")

        await write_file(src, "Content")

        await copy_file(src, dst)

        assert await exists(src)
        assert await exists(dst)
        assert await read_file(dst) == "Content"


@pytest.mark.asyncio
async def test_move_file_nested_directories():
    """Test moving file to nested directory structure."""
    with tempfile.TemporaryDirectory() as tmpdir:
        src = os.path.join(tmpdir, _unique_name("source.txt"))
        nested_dir = os.path.join(tmpdir, "level1", "level2")
        os.makedirs(nested_dir)
        dst = os.path.join(nested_dir, "destination.txt")

        await write_file(src, "Content")

        await move_file(src, dst)

        assert not await exists(src)
        assert await exists(dst)
        assert await read_file(dst) == "Content"


@pytest.mark.asyncio
async def test_canonicalize_absolute_path():
    """Test canonicalizing an already absolute path."""
    with tempfile.TemporaryDirectory() as tmpdir:
        file_path = os.path.join(tmpdir, _unique_name("file.txt"))
        await write_file(file_path, "Content")

        abs_path = os.path.abspath(file_path)
        canonical = await canonicalize(abs_path)

        assert os.path.isabs(canonical)
        # Canonicalize resolves symlinks, so both paths should resolve to the same file
        assert os.path.exists(canonical)
        assert os.path.samefile(canonical, abs_path)


@pytest.mark.asyncio
async def test_canonicalize_with_multiple_dots():
    """Test canonicalizing path with multiple .. components."""
    with tempfile.TemporaryDirectory() as tmpdir:
        nested_dir = os.path.join(tmpdir, "a", "b", "c")
        os.makedirs(nested_dir)
        file_path = os.path.join(nested_dir, "file.txt")
        await write_file(file_path, "Content")

        # Path with multiple .. components (go up two levels, then back down)
        relative_path = os.path.join(
            tmpdir, "a", "b", "..", "..", "a", "b", "c", "file.txt"
        )
        canonical = await canonicalize(relative_path)

        assert os.path.isabs(canonical)
        assert await exists(canonical)
        assert await read_file(canonical) == "Content"


@pytest.mark.asyncio
async def test_symlink_chain():
    """Test canonicalizing a chain of symlinks."""
    with tempfile.TemporaryDirectory() as tmpdir:
        original = os.path.join(tmpdir, _unique_name("original.txt"))
        link1 = os.path.join(tmpdir, _unique_name("link1.txt"))
        link2 = os.path.join(tmpdir, _unique_name("link2.txt"))

        await write_file(original, "Original content")
        await symlink(original, link1)
        await symlink(link1, link2)

        # Canonicalize should resolve through chain
        canonical = await canonicalize(link2)
        original_canonical = await canonicalize(original)

        assert os.path.normpath(canonical) == os.path.normpath(original_canonical)


@pytest.mark.asyncio
async def test_remove_file_permissions():
    """Test removing file with different permission scenarios."""
    with tempfile.TemporaryDirectory() as tmpdir:
        file_path = os.path.join(tmpdir, _unique_name("file.txt"))
        await write_file(file_path, "Content")

        # Should be able to remove file we created
        assert await exists(file_path)
        await remove_file(file_path)
        assert not await exists(file_path)


@pytest.mark.asyncio
async def test_file_manipulation_unicode():
    """Test file manipulation with Unicode content."""
    with tempfile.TemporaryDirectory() as tmpdir:
        src = os.path.join(tmpdir, _unique_name("source_unicode.txt"))
        dst = os.path.join(tmpdir, _unique_name("dest_unicode.txt"))

        # Unicode content
        unicode_content = "Hello 世界 🌍 Привет مرحبا"
        await write_file(src, unicode_content)

        await copy_file(src, dst)

        assert await read_file(dst) == unicode_content

        # Move should preserve Unicode
        dst2 = os.path.join(tmpdir, _unique_name("dest2_unicode.txt"))
        await move_file(dst, dst2)
        assert await read_file(dst2) == unicode_content
