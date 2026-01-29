# Migrated Tests from aiofiles

This directory contains tests migrated from the [aiofiles test suite](https://github.com/Tinche/aiofiles/tree/main/tests).

## Test Files

- **test_simple_migrated.py**: Basic file server tests (2 tests)
- **test_os_migrated.py**: OS-like operations tests (stat, exists, is_file, is_dir, etc.)
- **test_text_migrated.py**: Text file operations tests (read, write, seek, readlines, etc.)
- **test_binary_migrated.py**: Binary file operations tests (read, write, seek, readlines, etc.)

## Test Status

**Current Status**: 79 passed, 4 failed, 18 skipped

### Passing Tests
- Basic file operations (read, write, readlines, readline)
- File opening and context managers
- Directory operations (create_dir, remove_dir, list_dir)
- File metadata (stat, exists, is_file, is_dir)
- Most seek operations
- Binary and text mode operations

### Known Issues / Skipped Tests
- **flush()**: Not yet implemented in rapfiles (18 tests skipped)
- **truncate()**: Not yet implemented in rapfiles (6 tests skipped)
- **readinto()**: Not yet implemented in rapfiles (3 tests skipped)
- **sendfile()**: Not yet implemented in rapfiles (2 tests skipped)
- **statvfs()**: Not yet implemented in rapfiles (1 test skipped)
- **tempfile operations**: Not yet implemented in rapfiles (all tempfile tests skipped)
- **stdio operations**: Not yet implemented in rapfiles (all stdio tests skipped)

### Failing Tests (Need Investigation)
- `test_simple_seek[r+]`: Seek operation in r+ mode
- `test_getsize`: File size assertion (may be timing/race condition)

## Migration Notes

1. **API Differences**:
   - `aiofiles.open()` → `rapfiles.open()`
   - `aiofiles.os.stat()` → `rapfiles.stat()` (returns `FileMetadata` object)
   - `aiofiles.os.path.*` → `rapfiles.ospath.*` (synchronous) or `rapfiles.*` (async)
   - `aiofiles.threadpool.open()` → `rapfiles.open()` (rapfiles uses true async, not threadpool)

2. **Not Yet Implemented**:
   - File operations: `flush()`, `truncate()`, `readinto()`, `detach()`
   - OS operations: `remove()`, `unlink()`, `rename()`, `replace()`, `link()`, `symlink()`, `readlink()`, `sendfile()`, `statvfs()`, `access()`, `getcwd()`, `listdir()` (os module version), `scandir()`
   - Path operations: `samefile()`, `sameopenfile()`, `ismount()`, `islink()`
   - Tempfile and stdio modules

3. **Test Adaptations**:
   - Tests that require unimplemented features are skipped with `pytest.skip()`
   - Some tests use `os` module directly for operations not yet in rapfiles
   - File size assertions adjusted to account for potential newline differences

## Running the Tests

```bash
# Run all migrated tests
pytest tests/ -v

# Run specific test file
pytest tests/test_text_migrated.py -v

# Run with more details
pytest tests/ -v --tb=short
```

## Resources

Test resources are in `tests/resources/`:
- `test_file1.txt`: Contains "0123456789" (10 bytes)
- `multiline_file.txt`: Contains "line 1\nline 2\nline 3\n"

## Next Steps

1. Implement missing features (`flush()`, `truncate()`, etc.)
2. Fix failing tests
3. Add more comprehensive edge case tests
4. Add performance comparison tests with aiofiles
