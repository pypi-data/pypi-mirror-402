# Changelog

All notable changes to `rapfiles` will be documented in this file.

The format is based on [Keep a Changelog](https://keepachangelog.com/en/1.0.0/),
and this project adheres to [Semantic Versioning](https://semver.org/spec/v2.0.0.html).

## [0.2.0] - 2026-01-17

### Added - Phase 2: Advanced Filesystem Operations

#### File Manipulation Operations
- `copy_file()` - Copy files asynchronously with true async I/O
- `move_file()` - Move/rename files asynchronously (atomic within same filesystem)
- `rename()` - Rename files (alias for `move_file()`)
- `remove_file()` - Remove files asynchronously
- `hard_link()` - Create hard links asynchronously
- `symlink()` - Create symbolic links asynchronously (cross-platform)
- `canonicalize()` - Resolve symbolic links and return canonical paths

#### Atomic Operations
- `atomic_write_file()` - Atomic file writes using temporary files and rename
- `atomic_write_file_bytes()` - Atomic binary file writes
- `atomic_move_file()` - Atomic file moves ensuring destination is never partial

#### File Locking
- `lock_file()` - Advisory file locking (exclusive or shared) as async context manager
- `lock_file_shared()` - Convenience function for shared (read) locks
- `FileLock` class - Async context manager for file locks with manual release support
- Cross-platform locking support using `fs2` crate (Unix and Windows)

#### Batch Operations
- `read_files()` - Concurrently read multiple files, returns list of `(path, bytes)` tuples
- `read_files_dict()` - Concurrently read multiple files, returns dictionary mapping paths to contents
- `write_files()` - Concurrently write multiple files from dictionary
- `copy_files()` - Concurrently copy multiple files from list of `(src, dst)` tuples

### Changed
- All Phase 2 operations execute outside the Python GIL using native Rust/Tokio
- File locking uses `tokio::task::spawn_blocking` for blocking syscalls, properly isolated from async runtime
- Hard link operations use `spawn_blocking` (no async equivalent available)

### Testing
- Added comprehensive test suite for Phase 2 features:
  - `test_file_manipulation.py` - 19 tests for file manipulation operations
  - `test_atomic_operations.py` - 26 tests for atomic operations and file locking
  - `test_batch_operations.py` - 19 tests for batch operations
- All tests use unique file names for proper isolation
- All tests pass with parallel execution (`pytest -n 10`)
- Total test count: 188 tests (168 passing, 20 skipped)

### Documentation
- Updated README.md with Phase 2 features and usage examples
- Added comprehensive API documentation for all new functions
- Updated ROADMAP.md marking Phase 2 as complete
- Enhanced docstrings with examples and error documentation
- Updated type stubs (`.pyi` files) for all Phase 2 functions

### Code Quality
- Fixed all Rust clippy warnings (0 warnings remaining)
- All Python code formatted with ruff
- All ruff linting checks pass
- Type stubs updated for all Phase 2 functions

### Verification
- ✅ All async operations verified as true async (no Python thread pools)
- ✅ All file I/O uses `tokio::fs::*` (41 async operations)
- ✅ Only 4 legitimate `spawn_blocking` calls for operations without async equivalents
- ✅ No `asyncio.run_in_executor()` or Python thread pool usage
- ✅ All operations execute outside Python GIL

## [0.1.2] - 2026-01-16

### Added
- Python 3.14 support
  - Added Python 3.14 classifier to pyproject.toml
  - Updated CI/CD workflows to test for Python 3.14
  - Added ABI3 forward compatibility for Python 3.14

### Changed
- Python 3.13 support was added in v0.1.1, now with additional 3.14 support

### Compatibility
- Python 3.8 through 3.14 supported
- All platforms: Ubuntu (x86-64, aarch64), macOS (aarch64, x86-64), Windows (x86-64, aarch64)

## [0.1.1] - 2026-01-16

### Added
- Python 3.13 support
  - Added Python 3.13 classifier to pyproject.toml
  - Updated CI/CD workflows to test for Python 3.13

### Compatibility
- Python 3.8 through 3.13 supported (3.14 support added in v0.1.2)

## [0.1.0] - 2025-01-12

### Added - Phase 1: Core Filesystem Operations

#### File Operations
- `read_file()` - Read files asynchronously (text mode)
- `write_file()` - Write files asynchronously (text mode)
- `read_file_bytes()` - Read files asynchronously (binary mode)
- `write_file_bytes()` - Write files asynchronously (binary mode)
- `append_file()` - Append to files asynchronously

#### File Handles
- `open()` - Open files with async context managers (aiofiles compatible)
- `AsyncFile` class - File handle with async methods:
  - `read()`, `write()`, `readline()`, `readlines()`
  - `seek()`, `tell()`, `close()`
  - Async context manager support (`async with`)

#### Directory Operations
- `create_dir()` - Create directories (parent must exist)
- `create_dir_all()` - Create directories recursively
- `remove_dir()` - Remove empty directories
- `remove_dir_all()` - Remove directories recursively
- `list_dir()` - List directory contents
- `walk_dir()` - Recursively walk directories

#### Path Operations
- `exists()` - Check if path exists
- `is_file()` - Check if path is a file
- `is_dir()` - Check if path is a directory
- `rapfiles.ospath` module - Synchronous path operations (aiofiles compatible)

#### File Metadata
- `stat()` - Get file statistics
- `metadata()` - Alias for `stat()`
- `FileMetadata` class - File metadata structure with size, timestamps, type

### Features
- ✅ True async I/O - All operations use Tokio (no Python thread pools)
- ✅ GIL-independent - All I/O executes outside Python GIL
- ✅ aiofiles compatibility - Drop-in replacement for basic operations
- ✅ Cross-platform - Works on Windows, macOS, and Linux
- ✅ Type stubs - Complete `.pyi` files for IDE support
- ✅ Comprehensive testing - 34+ tests covering all features

### Initial Release
- Core filesystem operations for true async file I/O
- Native Rust/Tokio backend
- Python 3.8+ support

[0.2.0]: https://github.com/eddiethedean/rapfiles/releases/tag/v0.2.0
[0.1.2]: https://github.com/eddiethedean/rapfiles/releases/tag/v0.1.2
[0.1.1]: https://github.com/eddiethedean/rapfiles/releases/tag/v0.1.1
[0.1.0]: https://github.com/eddiethedean/rapfiles/releases/tag/v0.1.0
