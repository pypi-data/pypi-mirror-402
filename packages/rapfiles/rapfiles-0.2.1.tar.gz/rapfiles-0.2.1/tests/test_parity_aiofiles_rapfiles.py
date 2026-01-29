"""Comprehensive parity tests between aiofiles and rapfiles.

This test suite runs the same operations against both libraries to verify
that rapfiles maintains full compatibility with aiofiles API and behavior.
"""

import asyncio
import os
import tempfile
from pathlib import Path
from typing import Any, Callable, Dict, Tuple

import pytest

import aiofiles
import rapfiles


class ParityTester:
    """Helper class to test parity between aiofiles and rapfiles."""

    def __init__(self, tmp_path: Path):
        self.tmp_path = tmp_path
        self.results: Dict[str, Dict[str, Any]] = {}

    async def test_basic_read_write_text(self) -> Tuple[bool, str]:
        """Test basic text file read/write operations."""
        test_content = "Hello, world!\nThis is a test file.\nWith multiple lines."

        # Test with aiofiles
        aiofiles_path = self.tmp_path / "aiofiles_test.txt"
        async with aiofiles.open(str(aiofiles_path), "w") as f:
            await f.write(test_content)
        async with aiofiles.open(str(aiofiles_path), "r") as f:
            aiofiles_result = await f.read()

        # Test with rapfiles
        rapfiles_path = self.tmp_path / "rapfiles_test.txt"
        async with rapfiles.open(str(rapfiles_path), "w") as f:
            await f.write(test_content)
        async with rapfiles.open(str(rapfiles_path), "r") as f:
            rapfiles_result = await f.read()

        success = aiofiles_result == rapfiles_result
        return success, f"aiofiles: {len(aiofiles_result)} chars, rapfiles: {len(rapfiles_result)} chars"

    async def test_basic_read_write_binary(self) -> Tuple[bool, str]:
        """Test basic binary file read/write operations."""
        test_content = b"Binary data: \x00\x01\x02\x03\xFF\xFE\xFD"

        # Test with aiofiles
        aiofiles_path = self.tmp_path / "aiofiles_test.bin"
        async with aiofiles.open(str(aiofiles_path), "wb") as f:
            await f.write(test_content)
        async with aiofiles.open(str(aiofiles_path), "rb") as f:
            aiofiles_result = await f.read()

        # Test with rapfiles
        rapfiles_path = self.tmp_path / "rapfiles_test.bin"
        async with rapfiles.open(str(rapfiles_path), "wb") as f:
            await f.write(test_content)
        async with rapfiles.open(str(rapfiles_path), "rb") as f:
            rapfiles_result = await f.read()

        success = aiofiles_result == rapfiles_result
        return success, f"aiofiles: {len(aiofiles_result)} bytes, rapfiles: {len(rapfiles_result)} bytes"

    async def test_readline_text(self) -> Tuple[bool, str]:
        """Test readline() functionality for text files."""
        test_content = "line 1\nline 2\nline 3\n"

        # Test with aiofiles
        aiofiles_path = self.tmp_path / "aiofiles_readline.txt"
        async with aiofiles.open(str(aiofiles_path), "w") as f:
            await f.write(test_content)
        
        aiofiles_lines = []
        async with aiofiles.open(str(aiofiles_path), "r") as f:
            while True:
                line = await f.readline()
                if not line:
                    break
                aiofiles_lines.append(line)

        # Test with rapfiles
        rapfiles_path = self.tmp_path / "rapfiles_readline.txt"
        async with rapfiles.open(str(rapfiles_path), "w") as f:
            await f.write(test_content)
        
        rapfiles_lines = []
        async with rapfiles.open(str(rapfiles_path), "r") as f:
            while True:
                line = await f.readline()
                if not line:
                    break
                rapfiles_lines.append(line)

        success = aiofiles_lines == rapfiles_lines
        return success, f"aiofiles: {len(aiofiles_lines)} lines, rapfiles: {len(rapfiles_lines)} lines"

    async def test_readline_binary(self) -> Tuple[bool, str]:
        """Test readline() functionality for binary files."""
        test_content = b"line 1\nline 2\nline 3\n"

        # Test with aiofiles
        aiofiles_path = self.tmp_path / "aiofiles_readline_bin.txt"
        async with aiofiles.open(str(aiofiles_path), "wb") as f:
            await f.write(test_content)
        
        aiofiles_lines = []
        async with aiofiles.open(str(aiofiles_path), "rb") as f:
            while True:
                line = await f.readline()
                if not line:
                    break
                aiofiles_lines.append(line)

        # Test with rapfiles
        rapfiles_path = self.tmp_path / "rapfiles_readline_bin.txt"
        async with rapfiles.open(str(rapfiles_path), "wb") as f:
            await f.write(test_content)
        
        rapfiles_lines = []
        async with rapfiles.open(str(rapfiles_path), "rb") as f:
            while True:
                line = await f.readline()
                if not line:
                    break
                rapfiles_lines.append(line)

        success = aiofiles_lines == rapfiles_lines
        return success, f"aiofiles: {len(aiofiles_lines)} lines, rapfiles: {len(rapfiles_lines)} lines"

    async def test_readlines_text(self) -> Tuple[bool, str]:
        """Test readlines() functionality for text files."""
        test_content = "line 1\nline 2\nline 3\n"

        # Test with aiofiles
        aiofiles_path = self.tmp_path / "aiofiles_readlines.txt"
        async with aiofiles.open(str(aiofiles_path), "w") as f:
            await f.write(test_content)
        
        async with aiofiles.open(str(aiofiles_path), "r") as f:
            aiofiles_lines = await f.readlines()

        # Test with rapfiles
        rapfiles_path = self.tmp_path / "rapfiles_readlines.txt"
        async with rapfiles.open(str(rapfiles_path), "w") as f:
            await f.write(test_content)
        
        async with rapfiles.open(str(rapfiles_path), "r") as f:
            rapfiles_lines = await f.readlines()

        success = aiofiles_lines == rapfiles_lines
        return success, f"aiofiles: {len(aiofiles_lines)} lines, rapfiles: {len(rapfiles_lines)} lines"

    async def test_readlines_binary(self) -> Tuple[bool, str]:
        """Test readlines() functionality for binary files."""
        test_content = b"line 1\nline 2\nline 3\n"

        # Test with aiofiles
        aiofiles_path = self.tmp_path / "aiofiles_readlines_bin.txt"
        async with aiofiles.open(str(aiofiles_path), "wb") as f:
            await f.write(test_content)
        
        async with aiofiles.open(str(aiofiles_path), "rb") as f:
            aiofiles_lines = await f.readlines()

        # Test with rapfiles
        rapfiles_path = self.tmp_path / "rapfiles_readlines_bin.txt"
        async with rapfiles.open(str(rapfiles_path), "wb") as f:
            await f.write(test_content)
        
        async with rapfiles.open(str(rapfiles_path), "rb") as f:
            rapfiles_lines = await f.readlines()

        success = aiofiles_lines == rapfiles_lines
        return success, f"aiofiles: {len(aiofiles_lines)} lines, rapfiles: {len(rapfiles_lines)} lines"

    async def test_seek_tell_text(self) -> Tuple[bool, str]:
        """Test seek() and tell() operations for text files."""
        test_content = "0123456789ABCDEF"

        # Test with aiofiles
        aiofiles_path = self.tmp_path / "aiofiles_seek.txt"
        async with aiofiles.open(str(aiofiles_path), "w") as f:
            await f.write(test_content)
        
        async with aiofiles.open(str(aiofiles_path), "r") as f:
            await f.seek(5)
            aiofiles_pos = await f.tell()
            aiofiles_char = await f.read(1)

        # Test with rapfiles
        rapfiles_path = self.tmp_path / "rapfiles_seek.txt"
        async with rapfiles.open(str(rapfiles_path), "w") as f:
            await f.write(test_content)
        
        async with rapfiles.open(str(rapfiles_path), "r") as f:
            await f.seek(5)
            rapfiles_pos = await f.tell()
            rapfiles_char = await f.read(1)

        success = (aiofiles_pos == rapfiles_pos == 5) and (aiofiles_char == rapfiles_char == "5")
        return success, f"Position: aiofiles={aiofiles_pos}, rapfiles={rapfiles_pos}, Char: {rapfiles_char}"

    async def test_seek_tell_binary(self) -> Tuple[bool, str]:
        """Test seek() and tell() operations for binary files."""
        test_content = b"0123456789ABCDEF"

        # Test with aiofiles
        aiofiles_path = self.tmp_path / "aiofiles_seek.bin"
        async with aiofiles.open(str(aiofiles_path), "wb") as f:
            await f.write(test_content)
        
        async with aiofiles.open(str(aiofiles_path), "rb") as f:
            await f.seek(5)
            aiofiles_pos = await f.tell()
            aiofiles_byte = await f.read(1)

        # Test with rapfiles
        rapfiles_path = self.tmp_path / "rapfiles_seek.bin"
        async with rapfiles.open(str(rapfiles_path), "wb") as f:
            await f.write(test_content)
        
        async with rapfiles.open(str(rapfiles_path), "rb") as f:
            await f.seek(5)
            rapfiles_pos = await f.tell()
            rapfiles_byte = await f.read(1)

        success = (aiofiles_pos == rapfiles_pos == 5) and (aiofiles_byte == rapfiles_byte == b"5")
        return success, f"Position: aiofiles={aiofiles_pos}, rapfiles={rapfiles_pos}, Byte: {rapfiles_byte}"

    async def test_append_mode_text(self) -> Tuple[bool, str]:
        """Test append mode for text files."""
        initial_content = "initial\n"
        append_content = "appended\n"

        # Test with aiofiles
        aiofiles_path = self.tmp_path / "aiofiles_append.txt"
        async with aiofiles.open(str(aiofiles_path), "w") as f:
            await f.write(initial_content)
        async with aiofiles.open(str(aiofiles_path), "a") as f:
            await f.write(append_content)
        async with aiofiles.open(str(aiofiles_path), "r") as f:
            aiofiles_result = await f.read()

        # Test with rapfiles
        rapfiles_path = self.tmp_path / "rapfiles_append.txt"
        async with rapfiles.open(str(rapfiles_path), "w") as f:
            await f.write(initial_content)
        async with rapfiles.open(str(rapfiles_path), "a") as f:
            await f.write(append_content)
        async with rapfiles.open(str(rapfiles_path), "r") as f:
            rapfiles_result = await f.read()

        success = aiofiles_result == rapfiles_result
        return success, f"Result: '{aiofiles_result}' == '{rapfiles_result}'"

    async def test_append_mode_binary(self) -> Tuple[bool, str]:
        """Test append mode for binary files."""
        initial_content = b"initial\n"
        append_content = b"appended\n"

        # Test with aiofiles
        aiofiles_path = self.tmp_path / "aiofiles_append.bin"
        async with aiofiles.open(str(aiofiles_path), "wb") as f:
            await f.write(initial_content)
        async with aiofiles.open(str(aiofiles_path), "ab") as f:
            await f.write(append_content)
        async with aiofiles.open(str(aiofiles_path), "rb") as f:
            aiofiles_result = await f.read()

        # Test with rapfiles
        rapfiles_path = self.tmp_path / "rapfiles_append.bin"
        async with rapfiles.open(str(rapfiles_path), "wb") as f:
            await f.write(initial_content)
        async with rapfiles.open(str(rapfiles_path), "ab") as f:
            await f.write(append_content)
        async with rapfiles.open(str(rapfiles_path), "rb") as f:
            rapfiles_result = await f.read()

        success = aiofiles_result == rapfiles_result
        return success, f"Result: {aiofiles_result} == {rapfiles_result}"

    async def test_chunked_read_text(self) -> Tuple[bool, str]:
        """Test chunked reading for text files."""
        test_content = "A" * 1000  # 1000 characters

        # Test with aiofiles
        aiofiles_path = self.tmp_path / "aiofiles_chunked.txt"
        async with aiofiles.open(str(aiofiles_path), "w") as f:
            await f.write(test_content)
        
        aiofiles_chunks = []
        async with aiofiles.open(str(aiofiles_path), "r") as f:
            while True:
                chunk = await f.read(100)  # Read 100 chars at a time
                if not chunk:
                    break
                aiofiles_chunks.append(chunk)

        # Test with rapfiles
        rapfiles_path = self.tmp_path / "rapfiles_chunked.txt"
        async with rapfiles.open(str(rapfiles_path), "w") as f:
            await f.write(test_content)
        
        rapfiles_chunks = []
        async with rapfiles.open(str(rapfiles_path), "r") as f:
            while True:
                chunk = await f.read(100)  # Read 100 chars at a time
                if not chunk:
                    break
                rapfiles_chunks.append(chunk)

        success = "".join(aiofiles_chunks) == "".join(rapfiles_chunks) == test_content
        return success, f"aiofiles: {len(aiofiles_chunks)} chunks, rapfiles: {len(rapfiles_chunks)} chunks"

    async def test_chunked_read_binary(self) -> Tuple[bool, str]:
        """Test chunked reading for binary files."""
        test_content = b"B" * 1000  # 1000 bytes

        # Test with aiofiles
        aiofiles_path = self.tmp_path / "aiofiles_chunked.bin"
        async with aiofiles.open(str(aiofiles_path), "wb") as f:
            await f.write(test_content)
        
        aiofiles_chunks = []
        async with aiofiles.open(str(aiofiles_path), "rb") as f:
            while True:
                chunk = await f.read(100)  # Read 100 bytes at a time
                if not chunk:
                    break
                aiofiles_chunks.append(chunk)

        # Test with rapfiles
        rapfiles_path = self.tmp_path / "rapfiles_chunked.bin"
        async with rapfiles.open(str(rapfiles_path), "wb") as f:
            await f.write(test_content)
        
        rapfiles_chunks = []
        async with rapfiles.open(str(rapfiles_path), "rb") as f:
            while True:
                chunk = await f.read(100)  # Read 100 bytes at a time
                if not chunk:
                    break
                rapfiles_chunks.append(chunk)

        success = b"".join(aiofiles_chunks) == b"".join(rapfiles_chunks) == test_content
        return success, f"aiofiles: {len(aiofiles_chunks)} chunks, rapfiles: {len(rapfiles_chunks)} chunks"

    async def test_unicode_text(self) -> Tuple[bool, str]:
        """Test Unicode handling in text files."""
        test_content = "Hello 世界 🌍\nЗдравствуй мир\nمرحبا بالعالم\n"

        # Test with aiofiles
        aiofiles_path = self.tmp_path / "aiofiles_unicode.txt"
        async with aiofiles.open(str(aiofiles_path), "w", encoding="utf-8") as f:
            await f.write(test_content)
        async with aiofiles.open(str(aiofiles_path), "r", encoding="utf-8") as f:
            aiofiles_result = await f.read()

        # Test with rapfiles
        rapfiles_path = self.tmp_path / "rapfiles_unicode.txt"
        async with rapfiles.open(str(rapfiles_path), "w", encoding="utf-8") as f:
            await f.write(test_content)
        async with rapfiles.open(str(rapfiles_path), "r", encoding="utf-8") as f:
            rapfiles_result = await f.read()

        success = aiofiles_result == rapfiles_result
        return success, f"Unicode preserved: {success}"

    async def test_context_manager(self) -> Tuple[bool, str]:
        """Test that context managers work correctly."""
        test_content = "context manager test"

        # Test with aiofiles
        aiofiles_path = self.tmp_path / "aiofiles_ctx.txt"
        try:
            async with aiofiles.open(str(aiofiles_path), "w") as f:
                await f.write(test_content)
            # File should be closed here
            async with aiofiles.open(str(aiofiles_path), "r") as f:
                aiofiles_result = await f.read()
            aiofiles_success = True
        except Exception as e:
            aiofiles_success = False
            aiofiles_result = str(e)

        # Test with rapfiles
        rapfiles_path = self.tmp_path / "rapfiles_ctx.txt"
        try:
            async with rapfiles.open(str(rapfiles_path), "w") as f:
                await f.write(test_content)
            # File should be closed here
            async with rapfiles.open(str(rapfiles_path), "r") as f:
                rapfiles_result = await f.read()
            rapfiles_success = True
        except Exception as e:
            rapfiles_success = False
            rapfiles_result = str(e)

        success = aiofiles_success and rapfiles_success and (aiofiles_result == rapfiles_result == test_content)
        return success, f"Both succeed: aiofiles={aiofiles_success}, rapfiles={rapfiles_success}"

    async def test_ospath_compatibility(self) -> Tuple[bool, str]:
        """Test ospath module compatibility.
        
        Note: aiofiles doesn't have an ospath module, so we compare rapfiles.ospath
        with standard os.path to ensure it behaves correctly.
        """
        import os.path
        test_file = self.tmp_path / "ospath_test.txt"
        test_file.write_text("test")

        try:
            # Test with standard os.path (what aiofiles users would use)
            os_exists = os.path.exists(str(test_file))
            os_isfile = os.path.isfile(str(test_file))
            os_getsize = os.path.getsize(str(test_file))

            # Test rapfiles.ospath
            rapfiles_exists = rapfiles.ospath.exists(str(test_file))  # type: ignore[attr-defined]
            rapfiles_isfile = rapfiles.ospath.isfile(str(test_file))  # type: ignore[attr-defined]
            rapfiles_getsize = rapfiles.ospath.getsize(str(test_file))  # type: ignore[attr-defined]

            success = (
                os_exists is True
                and rapfiles_exists is True
                and os_isfile is True
                and rapfiles_isfile is True
                and os_getsize == rapfiles_getsize
            )
            return success, f"exists: os={os_exists}/rapfiles={rapfiles_exists}, isfile: os={os_isfile}/rapfiles={rapfiles_isfile}, getsize: os={os_getsize}/rapfiles={rapfiles_getsize}"
        except AttributeError as e:
            return False, f"AttributeError: {e}"


@pytest.mark.asyncio
async def test_all_parity_operations(tmp_path):
    """Run all parity tests and report results."""
    tester = ParityTester(tmp_path)
    
    test_methods = [
        ("Basic Read/Write (Text)", tester.test_basic_read_write_text),
        ("Basic Read/Write (Binary)", tester.test_basic_read_write_binary),
        ("Readline (Text)", tester.test_readline_text),
        ("Readline (Binary)", tester.test_readline_binary),
        ("Readlines (Text)", tester.test_readlines_text),
        ("Readlines (Binary)", tester.test_readlines_binary),
        ("Seek/Tell (Text)", tester.test_seek_tell_text),
        ("Seek/Tell (Binary)", tester.test_seek_tell_binary),
        ("Append Mode (Text)", tester.test_append_mode_text),
        ("Append Mode (Binary)", tester.test_append_mode_binary),
        ("Chunked Read (Text)", tester.test_chunked_read_text),
        ("Chunked Read (Binary)", tester.test_chunked_read_binary),
        ("Unicode Text", tester.test_unicode_text),
        ("Context Manager", tester.test_context_manager),
        ("ospath Compatibility", tester.test_ospath_compatibility),
    ]

    results = {}
    for test_name, test_func in test_methods:
        try:
            success, message = await test_func()
            results[test_name] = {"success": success, "message": message}
        except Exception as e:
            results[test_name] = {"success": False, "message": f"Exception: {e}"}

    # Print summary
    print("\n" + "=" * 80)
    print("PARITY TEST SUMMARY: aiofiles vs rapfiles")
    print("=" * 80)
    
    passed = 0
    failed = 0
    
    for test_name, result in results.items():
        status = "✅ PASS" if result["success"] else "❌ FAIL"
        print(f"{status:8} | {test_name:35} | {result['message']}")
        if result["success"]:
            passed += 1
        else:
            failed += 1
    
    print("=" * 80)
    print(f"Total: {passed} passed, {failed} failed out of {len(results)} tests")
    print("=" * 80)
    
    # Assert all tests passed
    failed_tests = [name for name, result in results.items() if not result["success"]]
    if failed_tests:
        pytest.fail(f"Parity tests failed: {', '.join(failed_tests)}")
    
    assert failed == 0, f"Expected all parity tests to pass, but {failed} failed"
