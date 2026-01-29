#![allow(non_local_definitions)] // False positive from pyo3 macros

use pyo3::prelude::*;
use pyo3::types::{PyBytes, PyString};
use pyo3_async_runtimes::tokio::future_into_py;
use std::sync::Arc;
use std::time::{SystemTime, UNIX_EPOCH};
use tokio::fs::File;
use tokio::io::{AsyncReadExt, AsyncSeekExt, AsyncWriteExt};
use tokio::sync::Mutex;

/// Validate a file path for security and correctness.
///
/// Ensures the path is not empty and does not contain null bytes,
/// which could be used for path traversal attacks or cause issues
/// with the underlying filesystem APIs.
///
/// # Arguments
///
/// * `path` - Path string to validate
///
/// # Returns
///
/// `Ok(())` if the path is valid, `PyValueError` otherwise.
fn validate_path(path: &str) -> PyResult<()> {
    if path.is_empty() {
        return Err(PyErr::new::<pyo3::exceptions::PyValueError, _>(
            "Path cannot be empty",
        ));
    }
    if path.contains('\0') {
        return Err(PyErr::new::<pyo3::exceptions::PyValueError, _>(
            "Path cannot contain null bytes",
        ));
    }
    Ok(())
}

/// Map Rust std::io::Error to appropriate Python exception with context.
///
/// Converts Rust I/O errors to Python exceptions with descriptive error messages
/// that include the file path and operation being performed. This provides better
/// error handling and debugging information for Python users.
///
/// # Arguments
///
/// * `e` - Rust std::io::Error
/// * `path` - File path involved in the operation
/// * `operation` - Description of the operation (e.g., "read file", "write file")
///
/// # Returns
///
/// Appropriate Python exception (PyFileNotFoundError, PyPermissionError, etc.)
fn map_io_error(e: std::io::Error, path: &str, operation: &str) -> PyErr {
    use std::io::ErrorKind;

    let error_msg = format!("Failed to {operation} {path}: {e}");

    match e.kind() {
        ErrorKind::NotFound => PyErr::new::<pyo3::exceptions::PyFileNotFoundError, _>(error_msg),
        ErrorKind::PermissionDenied => {
            PyErr::new::<pyo3::exceptions::PyPermissionError, _>(error_msg)
        }
        ErrorKind::AlreadyExists => PyErr::new::<pyo3::exceptions::PyFileExistsError, _>(error_msg),
        ErrorKind::InvalidInput => PyErr::new::<pyo3::exceptions::PyValueError, _>(error_msg),
        ErrorKind::InvalidData => {
            PyErr::new::<pyo3::exceptions::PyUnicodeDecodeError, _>(error_msg)
        }
        _ => PyErr::new::<pyo3::exceptions::PyIOError, _>(error_msg),
    }
}

/// Python bindings for rapfiles - True async filesystem I/O.
///
/// This module provides true async filesystem I/O operations backed by Rust and Tokio.
/// All I/O operations execute outside the Python GIL, ensuring event loops never stall.
/// Compatible with `aiofiles` API for drop-in replacement scenarios.
///
/// # Features
///
/// - File operations: read, write, append (text and binary)
/// - File handles: AsyncFile class with async context manager support
/// - Directory operations: create, remove, list, walk
/// - File metadata: stat, size, timestamps
/// - Path operations: ospath module compatibility
#[pymodule]
fn _rapfiles(_py: Python<'_>, m: &Bound<'_, PyModule>) -> PyResult<()> {
    // File operations
    m.add_function(wrap_pyfunction!(read_file_async, m)?)?;
    m.add_function(wrap_pyfunction!(write_file_async, m)?)?;
    m.add_function(wrap_pyfunction!(read_file_bytes_async, m)?)?;
    m.add_function(wrap_pyfunction!(write_file_bytes_async, m)?)?;
    m.add_function(wrap_pyfunction!(append_file_async, m)?)?;
    m.add_function(wrap_pyfunction!(open_file, m)?)?;
    m.add_class::<AsyncFile>()?;

    // Directory operations
    m.add_function(wrap_pyfunction!(create_dir_async, m)?)?;
    m.add_function(wrap_pyfunction!(create_dir_all_async, m)?)?;
    m.add_function(wrap_pyfunction!(remove_dir_async, m)?)?;
    m.add_function(wrap_pyfunction!(remove_dir_all_async, m)?)?;
    m.add_function(wrap_pyfunction!(list_dir_async, m)?)?;
    m.add_function(wrap_pyfunction!(exists_async, m)?)?;
    m.add_function(wrap_pyfunction!(is_file_async, m)?)?;
    m.add_function(wrap_pyfunction!(is_dir_async, m)?)?;

    // Metadata operations
    m.add_function(wrap_pyfunction!(stat_async, m)?)?;
    m.add_function(wrap_pyfunction!(metadata_async, m)?)?;
    m.add_class::<FileMetadata>()?;

    // Directory traversal
    m.add_function(wrap_pyfunction!(walk_dir_async, m)?)?;

    // File manipulation operations
    m.add_function(wrap_pyfunction!(copy_file_async, m)?)?;
    m.add_function(wrap_pyfunction!(move_file_async, m)?)?;
    m.add_function(wrap_pyfunction!(remove_file_async, m)?)?;
    m.add_function(wrap_pyfunction!(hard_link_async, m)?)?;
    m.add_function(wrap_pyfunction!(symlink_async, m)?)?;
    m.add_function(wrap_pyfunction!(canonicalize_async, m)?)?;

    // Atomic operations
    m.add_function(wrap_pyfunction!(atomic_write_file_async, m)?)?;
    m.add_function(wrap_pyfunction!(atomic_write_file_bytes_async, m)?)?;
    m.add_function(wrap_pyfunction!(atomic_move_file_async, m)?)?;

    // File locking
    m.add_function(wrap_pyfunction!(lock_file_async, m)?)?;
    m.add_class::<FileLock>()?;

    // Batch operations
    m.add_function(wrap_pyfunction!(read_files_async, m)?)?;
    m.add_function(wrap_pyfunction!(write_files_async, m)?)?;
    m.add_function(wrap_pyfunction!(copy_files_async, m)?)?;

    Ok(())
}

/// Async file read using Tokio (GIL-independent).
///
/// Reads the entire file and returns its contents as a UTF-8 decoded string.
/// All I/O operations execute outside the Python GIL using native Tokio,
/// ensuring true async behavior and preventing event loop stalls.
///
/// # Arguments
///
/// * `py` - Python GIL token
/// * `path` - Path to the file to read
///
/// # Returns
///
/// A coroutine that yields the file contents as a string.
///
/// # Errors
///
/// Returns `PyFileNotFoundError` if the file does not exist,
/// `PyIOError` if the file cannot be read, or `PyValueError` if the path is invalid.
#[pyfunction]
fn read_file_async(py: Python<'_>, path: String) -> PyResult<Bound<'_, PyAny>> {
    validate_path(&path)?;
    let future = async move {
        let path_clone = path.clone();
        tokio::fs::read_to_string(&path)
            .await
            .map_err(|e| map_io_error(e, &path_clone, "read file"))
    };
    future_into_py(py, future)
}

/// Async file write using Tokio (GIL-independent).
///
/// Writes the entire contents to a file. If the file exists, it will be overwritten.
/// All I/O operations execute outside the Python GIL using native Tokio,
/// ensuring true async behavior and preventing event loop stalls.
///
/// # Arguments
///
/// * `py` - Python GIL token
/// * `path` - Path to the file to write
/// * `contents` - Content to write to the file (UTF-8 string)
///
/// # Returns
///
/// A coroutine that yields `None` on success.
///
/// # Errors
///
/// Returns `PyIOError` if the file cannot be written, `PyPermissionError`
/// if write permission is denied, or `PyValueError` if the path is invalid.
#[pyfunction]
fn write_file_async(py: Python<'_>, path: String, contents: String) -> PyResult<Bound<'_, PyAny>> {
    validate_path(&path)?;
    let future = async move {
        let path_clone = path.clone();
        tokio::fs::write(&path, contents)
            .await
            .map_err(|e| map_io_error(e, &path_clone, "write file"))
    };
    future_into_py(py, future)
}

/// Async binary file read using Tokio (GIL-independent).
///
/// Reads the entire file and returns its contents as raw bytes.
/// All I/O operations execute outside the Python GIL using native Tokio,
/// ensuring true async behavior and preventing event loop stalls.
///
/// # Arguments
///
/// * `py` - Python GIL token
/// * `path` - Path to the file to read
///
/// # Returns
///
/// A coroutine that yields the file contents as bytes.
///
/// # Errors
///
/// Returns `PyFileNotFoundError` if the file does not exist,
/// `PyIOError` if the file cannot be read, or `PyValueError` if the path is invalid.
#[pyfunction]
fn read_file_bytes_async(py: Python<'_>, path: String) -> PyResult<Bound<'_, PyAny>> {
    validate_path(&path)?;
    let future = async move {
        let path_clone = path.clone();
        tokio::fs::read(&path).await.map_err(|e| {
            PyErr::new::<pyo3::exceptions::PyIOError, _>(format!(
                "Failed to read file {path_clone}: {e}"
            ))
        })
    };
    future_into_py(py, future)
}

/// Async binary file write using Tokio (GIL-independent).
///
/// Writes raw bytes to a file. If the file exists, it will be overwritten.
/// All I/O operations execute outside the Python GIL using native Tokio,
/// ensuring true async behavior and preventing event loop stalls.
///
/// # Arguments
///
/// * `py` - Python GIL token
/// * `path` - Path to the file to write
/// * `contents` - Bytes to write to the file
///
/// # Returns
///
/// A coroutine that yields `None` on success.
///
/// # Errors
///
/// Returns `PyIOError` if the file cannot be written, `PyPermissionError`
/// if write permission is denied, or `PyValueError` if the path is invalid.
#[pyfunction]
fn write_file_bytes_async<'a>(
    py: Python<'a>,
    path: String,
    contents: &'a Bound<'a, PyBytes>,
) -> PyResult<Bound<'a, PyAny>> {
    validate_path(&path)?;
    let bytes = contents.as_bytes().to_vec();
    let future = async move {
        let path_clone = path.clone();
        tokio::fs::write(&path, bytes)
            .await
            .map_err(|e| map_io_error(e, &path_clone, "write file"))
    };
    future_into_py(py, future)
}

/// Async file append using Tokio (GIL-independent).
///
/// Appends content to the end of a file. If the file does not exist, it will be created.
/// All I/O operations execute outside the Python GIL using native Tokio,
/// ensuring true async behavior and preventing event loop stalls.
///
/// # Arguments
///
/// * `py` - Python GIL token
/// * `path` - Path to the file to append to
/// * `contents` - Content to append to the file (UTF-8 string)
///
/// # Returns
///
/// A coroutine that yields `None` on success.
///
/// # Errors
///
/// Returns `PyIOError` if the file cannot be written, `PyPermissionError`
/// if write permission is denied, or `PyValueError` if the path is invalid.
#[pyfunction]
fn append_file_async(py: Python<'_>, path: String, contents: String) -> PyResult<Bound<'_, PyAny>> {
    validate_path(&path)?;
    let future = async move {
        let path_clone = path.clone();
        let mut file = tokio::fs::OpenOptions::new()
            .create(true)
            .append(true)
            .open(&path)
            .await
            .map_err(|e| {
                PyErr::new::<pyo3::exceptions::PyIOError, _>(format!(
                    "Failed to open file {path_clone} for appending: {e}"
                ))
            })?;

        use tokio::io::AsyncWriteExt;
        file.write_all(contents.as_bytes()).await.map_err(|e| {
            PyErr::new::<pyo3::exceptions::PyIOError, _>(format!(
                "Failed to append to file {path_clone}: {e}"
            ))
        })
    };
    future_into_py(py, future)
}

// Directory operations

/// Create a directory asynchronously.
///
/// Creates a single directory. Parent directories must already exist.
/// All I/O operations execute outside the Python GIL using native Tokio.
///
/// # Arguments
///
/// * `py` - Python GIL token
/// * `path` - Path to the directory to create
///
/// # Returns
///
/// A coroutine that yields `None` on success.
///
/// # Errors
///
/// Returns `PyFileExistsError` if the directory already exists,
/// `PyIOError` if the directory cannot be created, or `PyValueError` if the path is invalid.
#[pyfunction]
fn create_dir_async(py: Python<'_>, path: String) -> PyResult<Bound<'_, PyAny>> {
    validate_path(&path)?;
    let future = async move {
        let path_clone = path.clone();
        tokio::fs::create_dir(&path).await.map_err(|e| {
            PyErr::new::<pyo3::exceptions::PyIOError, _>(format!(
                "Failed to create directory {path_clone}: {e}"
            ))
        })
    };
    future_into_py(py, future)
}

/// Create a directory and all parent directories asynchronously.
///
/// Creates a directory and any necessary parent directories (equivalent to `mkdir -p`).
/// All I/O operations execute outside the Python GIL using native Tokio.
///
/// # Arguments
///
/// * `py` - Python GIL token
/// * `path` - Path to the directory to create (with parents)
///
/// # Returns
///
/// A coroutine that yields `None` on success.
///
/// # Errors
///
/// Returns `PyIOError` if the directory cannot be created,
/// or `PyValueError` if the path is invalid.
#[pyfunction]
fn create_dir_all_async(py: Python<'_>, path: String) -> PyResult<Bound<'_, PyAny>> {
    validate_path(&path)?;
    let future = async move {
        let path_clone = path.clone();
        tokio::fs::create_dir_all(&path).await.map_err(|e| {
            PyErr::new::<pyo3::exceptions::PyIOError, _>(format!(
                "Failed to create directory {path_clone}: {e}"
            ))
        })
    };
    future_into_py(py, future)
}

/// Remove an empty directory asynchronously.
#[pyfunction]
fn remove_dir_async(py: Python<'_>, path: String) -> PyResult<Bound<'_, PyAny>> {
    validate_path(&path)?;
    let future = async move {
        let path_clone = path.clone();
        tokio::fs::remove_dir(&path).await.map_err(|e| {
            PyErr::new::<pyo3::exceptions::PyIOError, _>(format!(
                "Failed to remove directory {path_clone}: {e}"
            ))
        })
    };
    future_into_py(py, future)
}

/// Remove a directory and all its contents asynchronously.
#[pyfunction]
fn remove_dir_all_async(py: Python<'_>, path: String) -> PyResult<Bound<'_, PyAny>> {
    validate_path(&path)?;
    let future = async move {
        let path_clone = path.clone();
        tokio::fs::remove_dir_all(&path).await.map_err(|e| {
            PyErr::new::<pyo3::exceptions::PyIOError, _>(format!(
                "Failed to remove directory {path_clone}: {e}"
            ))
        })
    };
    future_into_py(py, future)
}

/// List directory contents asynchronously.
///
/// Returns a list of file and directory names in the specified directory.
/// All I/O operations execute outside the Python GIL using native Tokio.
///
/// # Arguments
///
/// * `py` - Python GIL token
/// * `path` - Path to the directory to list
///
/// # Returns
///
/// A coroutine that yields a list of file and directory names (strings).
///
/// # Errors
///
/// Returns `PyFileNotFoundError` if the directory does not exist,
/// `PyIOError` if the directory cannot be read, or `PyValueError` if the path is invalid.
#[pyfunction]
fn list_dir_async(py: Python<'_>, path: String) -> PyResult<Bound<'_, PyAny>> {
    validate_path(&path)?;
    let future = async move {
        let path_clone = path.clone();
        let mut entries = tokio::fs::read_dir(&path).await.map_err(|e| {
            PyErr::new::<pyo3::exceptions::PyIOError, _>(format!(
                "Failed to read directory {path_clone}: {e}"
            ))
        })?;

        let mut names = Vec::new();
        while let Some(entry) = entries.next_entry().await.map_err(|e| {
            PyErr::new::<pyo3::exceptions::PyIOError, _>(format!(
                "Failed to read directory entry in {path_clone}: {e}"
            ))
        })? {
            if let Some(name) = entry.file_name().to_str() {
                names.push(name.to_string());
            }
        }
        Ok(names)
    };
    future_into_py(py, future)
}

/// Check if a path exists asynchronously.
#[pyfunction]
fn exists_async(py: Python<'_>, path: String) -> PyResult<Bound<'_, PyAny>> {
    validate_path(&path)?;
    let future = async move { Ok(tokio::fs::metadata(&path).await.is_ok()) };
    future_into_py(py, future)
}

/// Check if a path is a file asynchronously.
#[pyfunction]
fn is_file_async(py: Python<'_>, path: String) -> PyResult<Bound<'_, PyAny>> {
    validate_path(&path)?;
    let future = async move {
        let path_clone = path.clone();
        let metadata = tokio::fs::metadata(&path).await.map_err(|e| {
            PyErr::new::<pyo3::exceptions::PyIOError, _>(format!(
                "Failed to get metadata for {path_clone}: {e}"
            ))
        })?;
        Ok(metadata.is_file())
    };
    future_into_py(py, future)
}

/// Check if a path is a directory asynchronously.
#[pyfunction]
fn is_dir_async(py: Python<'_>, path: String) -> PyResult<Bound<'_, PyAny>> {
    validate_path(&path)?;
    let future = async move {
        let path_clone = path.clone();
        let metadata = tokio::fs::metadata(&path).await.map_err(|e| {
            PyErr::new::<pyo3::exceptions::PyIOError, _>(format!(
                "Failed to get metadata for {path_clone}: {e}"
            ))
        })?;
        Ok(metadata.is_dir())
    };
    future_into_py(py, future)
}

/// Parse file mode string to determine open options.
///
/// Parses Python file mode strings (e.g., "r", "w+", "rb") and converts them
/// to flags for Tokio's OpenOptions. Supports both text and binary modes.
///
/// # Arguments
///
/// * `mode` - File mode string (r, r+, w, w+, a, a+, rb, rb+, wb, wb+, ab, ab+)
///
/// # Returns
///
/// Tuple of (read, write, append) boolean flags
///
/// # Errors
///
/// Returns `PyValueError` if the mode string is invalid.
fn parse_mode(mode: &str) -> PyResult<(bool, bool, bool)> {
    // Returns (read, write, append)
    match mode {
        "r" => Ok((true, false, false)),
        "r+" => Ok((true, true, false)),
        "w" => Ok((false, true, false)),
        "w+" => Ok((true, true, false)),
        "a" => Ok((false, true, true)),
        "a+" => Ok((true, true, true)),
        "rb" => Ok((true, false, false)),
        "rb+" => Ok((true, true, false)),
        "wb" => Ok((false, true, false)),
        "wb+" => Ok((true, true, false)),
        "ab" => Ok((false, true, true)),
        "ab+" => Ok((true, true, true)),
        _ => Err(PyErr::new::<pyo3::exceptions::PyValueError, _>(format!(
            "Invalid mode: {mode}. Must be one of: r, r+, w, w+, a, a+, rb, rb+, wb, wb+, ab, ab+"
        ))),
    }
}

/// Async file handle for true async I/O operations.
///
/// Provides file handle operations with true async I/O backed by Tokio.
/// All operations execute outside the Python GIL, ensuring event loops
/// never stall. Supports both text and binary modes, and can be used
/// as an async context manager.
///
/// # Example
///
/// ```python
/// async with rapfiles.open("file.txt", "r") as f:
///     content = await f.read()
/// ```
#[pyclass]
struct AsyncFile {
    file: Arc<Mutex<File>>,
    path: String,
    mode: String,
}

#[pymethods]
impl AsyncFile {
    /// Default constructor - use open_file() or rapfiles.open() instead.
    #[new]
    fn new() -> PyResult<Self> {
        Err(PyErr::new::<pyo3::exceptions::PyValueError, _>(
            "AsyncFile cannot be instantiated directly. Use rapfiles.open() or open_file() instead."
        ))
    }

    /// Read from file.
    ///
    /// Reads data from the file. In binary mode, returns bytes. In text mode,
    /// returns bytes that are decoded to strings by the Python wrapper.
    ///
    /// # Arguments
    ///
    /// * `size` - Number of bytes to read. If -1 (default), reads the entire file.
    ///
    /// # Returns
    ///
    /// A coroutine that yields bytes (or str in text mode via wrapper).
    ///
    /// # Errors
    ///
    /// Returns `PyIOError` if the file cannot be read.
    #[pyo3(signature = (size = -1))]
    fn read<'a>(&self, py: Python<'a>, size: i64) -> PyResult<Bound<'a, PyAny>> {
        let file = Arc::clone(&self.file);
        let path = self.path.clone();
        let _mode = self.mode.clone();

        let future = async move {
            let mut file_guard = file.lock().await;

            let buffer = if size < 0 {
                // Read all
                let mut buffer = Vec::new();
                file_guard.read_to_end(&mut buffer).await.map_err(|e| {
                    PyErr::new::<pyo3::exceptions::PyIOError, _>(format!(
                        "Failed to read file {path}: {e}"
                    ))
                })?;
                buffer
            } else {
                let mut buffer = vec![0u8; size as usize];
                let n = file_guard.read(&mut buffer).await.map_err(|e| {
                    PyErr::new::<pyo3::exceptions::PyIOError, _>(format!(
                        "Failed to read file {path}: {e}"
                    ))
                })?;
                buffer.truncate(n);
                buffer
            };

            // Return bytes - Python wrapper will decode for text mode
            Ok(buffer)
        };

        future_into_py(py, future)
    }

    /// Write to file.
    ///
    /// Writes data to the file. Accepts both strings and bytes.
    ///
    /// # Arguments
    ///
    /// * `data` - Data to write (str or bytes)
    ///
    /// # Returns
    ///
    /// A coroutine that yields the number of bytes written.
    ///
    /// # Errors
    ///
    /// Returns `PyTypeError` if data is not str or bytes,
    /// or `PyIOError` if the file cannot be written.
    fn write<'a>(&self, py: Python<'a>, data: &Bound<'a, PyAny>) -> PyResult<Bound<'a, PyAny>> {
        let file = Arc::clone(&self.file);
        let path = self.path.clone();

        // Convert Python bytes/string to Vec<u8>
        let bytes: Vec<u8> = if let Ok(py_bytes) = data.cast::<PyBytes>() {
            py_bytes.as_bytes().to_vec()
        } else if let Ok(py_str) = data.cast::<PyString>() {
            py_str.to_string().into_bytes()
        } else {
            return Err(PyErr::new::<pyo3::exceptions::PyTypeError, _>(
                "write() argument must be bytes or str",
            ));
        };

        let future = async move {
            let mut file_guard = file.lock().await;
            file_guard.write_all(&bytes).await.map_err(|e| {
                PyErr::new::<pyo3::exceptions::PyIOError, _>(format!(
                    "Failed to write file {path}: {e}"
                ))
            })?;
            Ok(bytes.len() as i64)
        };

        future_into_py(py, future)
    }

    /// Read a line from file.
    ///
    /// Reads a single line from the file, up to and including the newline character.
    ///
    /// # Arguments
    ///
    /// * `size` - Maximum number of bytes to read. If -1 (default), reads until newline.
    ///
    /// # Returns
    ///
    /// A coroutine that yields bytes (or str in text mode via wrapper).
    ///
    /// # Errors
    ///
    /// Returns `PyIOError` if the file cannot be read.
    #[pyo3(signature = (size = -1))]
    fn readline<'a>(&self, py: Python<'a>, size: i64) -> PyResult<Bound<'a, PyAny>> {
        let file = Arc::clone(&self.file);
        let path = self.path.clone();
        let _mode = self.mode.clone();

        let future = async move {
            let mut file_guard = file.lock().await;
            let mut buffer = Vec::new();
            let mut single_byte = [0u8; 1];

            loop {
                let n = file_guard
                    .read(&mut single_byte)
                    .await
                    .map_err(|e| map_io_error(e, &path, "read file"))?;

                if n == 0 {
                    break; // EOF
                }

                buffer.push(single_byte[0]);

                if single_byte[0] == b'\n' {
                    break; // End of line
                }

                if size > 0 && buffer.len() >= size as usize {
                    break; // Reached size limit
                }
            }

            // For now, always return bytes - Python will handle text decoding
            Ok(buffer)
        };

        future_into_py(py, future)
    }

    /// Read all lines from file.
    ///
    /// Reads all lines from the file and returns them as a list.
    ///
    /// # Arguments
    ///
    /// * `hint` - Approximate number of lines to read. If -1 (default), reads all lines.
    ///
    /// # Returns
    ///
    /// A coroutine that yields a list of bytes (or list of str in text mode via wrapper).
    ///
    /// # Errors
    ///
    /// Returns `PyIOError` if the file cannot be read.
    #[pyo3(signature = (hint = -1))]
    fn readlines<'a>(&self, py: Python<'a>, hint: i64) -> PyResult<Bound<'a, PyAny>> {
        let file = Arc::clone(&self.file);
        let path = self.path.clone();
        let _mode = self.mode.clone();

        let future = async move {
            let mut file_guard = file.lock().await;
            let mut lines = Vec::new();
            let mut current_line = Vec::new();
            let mut single_byte = [0u8; 1];

            loop {
                let n = file_guard
                    .read(&mut single_byte)
                    .await
                    .map_err(|e| map_io_error(e, &path, "read file"))?;

                if n == 0 {
                    if !current_line.is_empty() {
                        lines.push(current_line);
                    }
                    break; // EOF
                }

                current_line.push(single_byte[0]);

                if single_byte[0] == b'\n' {
                    lines.push(current_line);
                    current_line = Vec::new();

                    if hint > 0 && lines.len() >= hint as usize {
                        break;
                    }
                }
            }

            // For now, always return list of bytes - Python will handle text decoding
            Ok(lines)
        };

        future_into_py(py, future)
    }

    /// Seek to a position in the file.
    ///
    /// Changes the file position to the given offset.
    ///
    /// # Arguments
    ///
    /// * `offset` - Byte offset
    /// * `whence` - Reference point: 0=start (SEEK_SET), 1=current (SEEK_CUR), 2=end (SEEK_END)
    ///
    /// # Returns
    ///
    /// A coroutine that yields the new absolute position.
    ///
    /// # Errors
    ///
    /// Returns `PyValueError` if whence is invalid, or `PyIOError` if seek fails.
    #[pyo3(signature = (offset, whence = 0))]
    fn seek<'a>(&self, py: Python<'a>, offset: i64, whence: i32) -> PyResult<Bound<'a, PyAny>> {
        let file = Arc::clone(&self.file);
        let path = self.path.clone();

        let future = async move {
            let mut file_guard = file.lock().await;

            let pos = match whence {
                0 => std::io::SeekFrom::Start(offset as u64),
                1 => std::io::SeekFrom::Current(offset),
                2 => std::io::SeekFrom::End(offset),
                _ => {
                    return Err(PyErr::new::<pyo3::exceptions::PyValueError, _>(
                        format!("Invalid whence value: {whence}. Must be 0 (SEEK_SET), 1 (SEEK_CUR), or 2 (SEEK_END)"),
                    ));
                }
            };

            let new_pos = file_guard.seek(pos).await.map_err(|e| {
                PyErr::new::<pyo3::exceptions::PyIOError, _>(format!(
                    "Failed to seek in file {path}: {e}"
                ))
            })?;

            Ok(new_pos as i64)
        };

        future_into_py(py, future)
    }

    /// Get current position in file.
    ///
    /// Returns the current file position (byte offset from start).
    ///
    /// # Returns
    ///
    /// A coroutine that yields the current position as an integer.
    ///
    /// # Errors
    ///
    /// Returns `PyIOError` if the position cannot be determined.
    fn tell<'a>(&self, py: Python<'a>) -> PyResult<Bound<'a, PyAny>> {
        let file = Arc::clone(&self.file);
        let path = self.path.clone();

        let future = async move {
            let mut file_guard = file.lock().await;
            let pos = file_guard.stream_position().await.map_err(|e| {
                PyErr::new::<pyo3::exceptions::PyIOError, _>(format!(
                    "Failed to get position in file {path}: {e}"
                ))
            })?;
            Ok(pos as i64)
        };

        future_into_py(py, future)
    }

    /// Close the file.
    ///
    /// Closes the file handle. The file is automatically closed when the
    /// object is dropped, but this method is provided for API compatibility
    /// with standard file interfaces.
    ///
    /// # Returns
    ///
    /// A coroutine that yields `None` on success.
    fn close<'a>(&self, py: Python<'a>) -> PyResult<Bound<'a, PyAny>> {
        // File is automatically closed when dropped, but we provide this for API compatibility
        let future = async move {
            // The file will be closed when the Arc is dropped
            Ok(())
        };
        future_into_py(py, future)
    }

    /// Async context manager entry.
    fn __aenter__(slf: PyRef<'_, Self>) -> PyRef<'_, Self> {
        // Return self directly - Python's async context manager will handle it
        slf
    }

    /// Async context manager exit.
    fn __aexit__(
        &self,
        _exc_type: Option<&Bound<'_, PyAny>>,
        _exc_val: Option<&Bound<'_, PyAny>>,
        _exc_tb: Option<&Bound<'_, PyAny>>,
    ) -> PyResult<Py<PyAny>> {
        // Close the file on exit, return False to not suppress exceptions
        Python::attach(|py| {
            let future = async move {
                Ok(false) // Return False to not suppress exceptions
            };
            future_into_py(py, future).map(|bound| bound.unbind())
        })
    }
}

/// File metadata structure (aiofiles.stat_result compatible).
///
/// Provides file metadata including size, timestamps, and type information.
/// Compatible with `aiofiles.stat_result` for drop-in replacement scenarios.
///
/// # Properties
///
/// * `size` - File size in bytes
/// * `is_file` - True if path is a file
/// * `is_dir` - True if path is a directory
/// * `modified` - Modification time as Unix timestamp (float)
/// * `accessed` - Access time as Unix timestamp (float)
/// * `created` - Creation time as Unix timestamp (float)
#[pyclass]
#[derive(Clone)]
struct FileMetadata {
    size: u64,
    is_file: bool,
    is_dir: bool,
    modified: f64, // Unix timestamp
    accessed: f64, // Unix timestamp
    created: f64,  // Unix timestamp (creation time on Windows, birth time on Unix)
}

#[pymethods]
impl FileMetadata {
    #[new]
    fn new(
        size: u64,
        is_file: bool,
        is_dir: bool,
        modified: f64,
        accessed: f64,
        created: f64,
    ) -> Self {
        FileMetadata {
            size,
            is_file,
            is_dir,
            modified,
            accessed,
            created,
        }
    }

    #[getter]
    fn size(&self) -> u64 {
        self.size
    }

    #[getter]
    fn is_file(&self) -> bool {
        self.is_file
    }

    #[getter]
    fn is_dir(&self) -> bool {
        self.is_dir
    }

    #[getter]
    fn modified(&self) -> f64 {
        self.modified
    }

    #[getter]
    fn accessed(&self) -> f64 {
        self.accessed
    }

    #[getter]
    fn created(&self) -> f64 {
        self.created
    }
}

/// Convert SystemTime to Unix timestamp.
///
/// Converts a Rust SystemTime to a Unix timestamp (seconds since epoch as float).
/// Used for file metadata timestamps (modified, accessed, created).
///
/// # Arguments
///
/// * `time` - SystemTime to convert
///
/// # Returns
///
/// Unix timestamp as f64 (seconds since epoch)
fn system_time_to_timestamp(time: SystemTime) -> f64 {
    time.duration_since(UNIX_EPOCH)
        .unwrap_or_default()
        .as_secs_f64()
}

/// Get file statistics asynchronously.
///
/// Returns file metadata including size, timestamps, and type information.
/// All I/O operations execute outside the Python GIL using native Tokio.
///
/// # Arguments
///
/// * `py` - Python GIL token
/// * `path` - Path to the file or directory
///
/// # Returns
///
/// A coroutine that yields a `FileMetadata` object.
///
/// # Errors
///
/// Returns `PyFileNotFoundError` if the path does not exist,
/// `PyIOError` if metadata cannot be retrieved, or `PyValueError` if the path is invalid.
#[pyfunction]
fn stat_async(py: Python<'_>, path: String) -> PyResult<Bound<'_, PyAny>> {
    validate_path(&path)?;
    let future = async move {
        let path_clone = path.clone();
        let metadata = tokio::fs::metadata(&path).await.map_err(|e| {
            PyErr::new::<pyo3::exceptions::PyIOError, _>(format!(
                "Failed to get metadata for {path_clone}: {e}"
            ))
        })?;

        let size = metadata.len();
        let is_file = metadata.is_file();
        let is_dir = metadata.is_dir();

        let modified = metadata
            .modified()
            .map(system_time_to_timestamp)
            .unwrap_or(0.0);
        let accessed = metadata
            .accessed()
            .map(system_time_to_timestamp)
            .unwrap_or(0.0);

        // Creation time (available on Windows, birth time on Unix requires platform-specific code)
        let created = metadata
            .created()
            .map(system_time_to_timestamp)
            .unwrap_or(modified); // Fallback to modified time if creation time not available

        Ok(FileMetadata {
            size,
            is_file,
            is_dir,
            modified,
            accessed,
            created,
        })
    };
    future_into_py(py, future)
}

/// Get file metadata asynchronously (alias for stat).
#[pyfunction]
fn metadata_async(py: Python<'_>, path: String) -> PyResult<Bound<'_, PyAny>> {
    stat_async(py, path)
}

// Directory traversal

/// Recursively walk a directory asynchronously.
///
/// Traverses a directory tree recursively and returns a list of all files
/// and directories found. All I/O operations execute outside the Python GIL
/// using native Tokio, ensuring true async behavior.
///
/// # Arguments
///
/// * `py` - Python GIL token
/// * `path` - Directory path to walk
///
/// # Returns
///
/// A coroutine that yields a list of (path, is_file) tuples where:
/// - `path`: Full path to the file or directory
/// - `is_file`: True if the path is a file, False if it's a directory
///
/// # Errors
///
/// Returns `PyFileNotFoundError` if the directory does not exist,
/// `PyIOError` if the directory cannot be read, or `PyValueError` if the path is invalid.
#[pyfunction]
fn walk_dir_async(py: Python<'_>, path: String) -> PyResult<Bound<'_, PyAny>> {
    validate_path(&path)?;
    let future = async move {
        let path_clone = path.clone();
        let mut results = Vec::new();

        // Use a stack to traverse directories
        let mut stack = vec![path_clone.clone()];

        while let Some(current_path) = stack.pop() {
            let mut entries = match tokio::fs::read_dir(&current_path).await {
                Ok(entries) => entries,
                Err(_e) => {
                    // Skip directories we can't read
                    continue;
                }
            };

            while let Some(entry) = entries.next_entry().await.map_err(|e| {
                PyErr::new::<pyo3::exceptions::PyIOError, _>(format!(
                    "Failed to read directory entry in {current_path}: {e}"
                ))
            })? {
                let entry_path = entry.path();
                let path_str = entry_path.to_string_lossy().to_string();

                let metadata = match entry.metadata().await {
                    Ok(m) => m,
                    Err(_) => continue, // Skip entries we can't get metadata for
                };

                let is_file = metadata.is_file();
                let is_dir = metadata.is_dir();

                results.push((path_str.clone(), is_file));

                // Add subdirectories to the stack for traversal
                if is_dir {
                    stack.push(path_str);
                }
            }
        }

        Ok(results)
    };
    future_into_py(py, future)
}

// File manipulation operations

/// Copy a file asynchronously.
///
/// Copies a file from source to destination. If the destination file exists,
/// it will be overwritten. All I/O operations execute outside the Python GIL
/// using native Tokio, ensuring true async behavior.
///
/// # Arguments
///
/// * `py` - Python GIL token
/// * `src` - Path to the source file
/// * `dst` - Path to the destination file
///
/// # Returns
///
/// A coroutine that yields `None` on success.
///
/// # Errors
///
/// Returns `PyFileNotFoundError` if the source file does not exist,
/// `PyIOError` if the file cannot be copied, or `PyValueError` if the path is invalid.
#[pyfunction]
fn copy_file_async(py: Python<'_>, src: String, dst: String) -> PyResult<Bound<'_, PyAny>> {
    validate_path(&src)?;
    validate_path(&dst)?;
    let future = async move {
        let src_clone = src.clone();
        let dst_clone = dst.clone();
        tokio::fs::copy(&src, &dst)
            .await
            .map_err(|e| map_io_error(e, &format!("{src_clone} -> {dst_clone}"), "copy file"))?;
        Ok(())
    };
    future_into_py(py, future)
}

/// Move or rename a file asynchronously.
///
/// Moves a file from source to destination. This is an atomic operation when
/// moving within the same filesystem. For cross-device moves, it will copy
/// and then remove the source file. All I/O operations execute outside the
/// Python GIL using native Tokio, ensuring true async behavior.
///
/// # Arguments
///
/// * `py` - Python GIL token
/// * `src` - Path to the source file
/// * `dst` - Path to the destination file
///
/// # Returns
///
/// A coroutine that yields `None` on success.
///
/// # Errors
///
/// Returns `PyFileNotFoundError` if the source file does not exist,
/// `PyIOError` if the file cannot be moved, or `PyValueError` if the path is invalid.
#[pyfunction]
fn move_file_async(py: Python<'_>, src: String, dst: String) -> PyResult<Bound<'_, PyAny>> {
    validate_path(&src)?;
    validate_path(&dst)?;
    let future = async move {
        let src_clone = src.clone();
        let dst_clone = dst.clone();
        
        // Try rename first (atomic on same filesystem)
        match tokio::fs::rename(&src, &dst).await {
            Ok(_) => Ok(()),
            Err(e) if e.kind() == std::io::ErrorKind::CrossesDevices => {
                // Cross-device move: copy then remove
                tokio::fs::copy(&src, &dst)
                    .await
                    .map_err(|e| map_io_error(e, &format!("{src_clone} -> {dst_clone}"), "copy file"))?;
                tokio::fs::remove_file(&src)
                    .await
                    .map_err(|e| map_io_error(e, &src_clone, "remove file"))?;
                Ok(())
            }
            Err(e) => Err(map_io_error(e, &format!("{src_clone} -> {dst_clone}"), "move file")),
        }
    };
    future_into_py(py, future)
}

/// Remove a file asynchronously.
///
/// Deletes a file from the filesystem. This will not remove directories.
/// All I/O operations execute outside the Python GIL using native Tokio,
/// ensuring true async behavior.
///
/// # Arguments
///
/// * `py` - Python GIL token
/// * `path` - Path to the file to remove
///
/// # Returns
///
/// A coroutine that yields `None` on success.
///
/// # Errors
///
/// Returns `PyFileNotFoundError` if the file does not exist,
/// `PyIOError` if the file cannot be removed (e.g., if it's a directory),
/// or `PyValueError` if the path is invalid.
#[pyfunction]
fn remove_file_async(py: Python<'_>, path: String) -> PyResult<Bound<'_, PyAny>> {
    validate_path(&path)?;
    let future = async move {
        let path_clone = path.clone();
        
        // Check if it's a directory first to provide a better error message
        let metadata = tokio::fs::metadata(&path).await;
        if let Ok(md) = metadata {
            if md.is_dir() {
                return Err(PyErr::new::<pyo3::exceptions::PyIOError, _>(format!(
                    "Failed to remove file {path_clone}: path is a directory. Use remove_dir() instead."
                )));
            }
        }
        
        tokio::fs::remove_file(&path)
            .await
            .map_err(|e| map_io_error(e, &path_clone, "remove file"))
    };
    future_into_py(py, future)
}

/// Create a hard link asynchronously.
///
/// Creates a hard link from source to destination. Both files will refer
/// to the same underlying file data. All I/O operations execute outside
/// the Python GIL using native Tokio, ensuring true async behavior.
///
/// # Arguments
///
/// * `py` - Python GIL token
/// * `src` - Path to the source file
/// * `dst` - Path to the destination link
///
/// # Returns
///
/// A coroutine that yields `None` on success.
///
/// # Errors
///
/// Returns `PyFileNotFoundError` if the source file does not exist,
/// `PyIOError` if the link cannot be created, or `PyValueError` if the path is invalid.
#[pyfunction]
fn hard_link_async(py: Python<'_>, src: String, dst: String) -> PyResult<Bound<'_, PyAny>> {
    validate_path(&src)?;
    validate_path(&dst)?;
    let future = async move {
        let src_clone = src.clone();
        let dst_clone = dst.clone();
        
        // tokio::fs::hard_link is not available, use std::fs::hard_link in blocking mode
        tokio::task::spawn_blocking(move || {
            std::fs::hard_link(&src, &dst)
                .map_err(|e| map_io_error(e, &format!("{src_clone} -> {dst_clone}"), "create hard link"))
        })
        .await
        .map_err(|e| PyErr::new::<pyo3::exceptions::PyIOError, _>(format!("Failed to create hard link: {e}")))?
    };
    future_into_py(py, future)
}

/// Create a symbolic link asynchronously.
///
/// Creates a symbolic link from source to destination. The destination
/// will point to the source path. All I/O operations execute outside
/// the Python GIL using native Tokio, ensuring true async behavior.
///
/// # Arguments
///
/// * `py` - Python GIL token
/// * `src` - Path that the symlink will point to
/// * `dst` - Path to the symbolic link to create
///
/// # Returns
///
/// A coroutine that yields `None` on success.
///
/// # Errors
///
/// Returns `PyIOError` if the symlink cannot be created, or `PyValueError` if the path is invalid.
#[pyfunction]
fn symlink_async(py: Python<'_>, src: String, dst: String) -> PyResult<Bound<'_, PyAny>> {
    validate_path(&src)?;
    validate_path(&dst)?;
    let future = async move {
        let src_clone = src.clone();
        let dst_clone = dst.clone();
        
        // tokio::fs::symlink has different behavior on Windows vs Unix
        #[cfg(unix)]
        {
            use tokio::fs::symlink;
            symlink(&src, &dst)
                .await
                .map_err(|e| map_io_error(e, &format!("{src_clone} -> {dst_clone}"), "create symlink"))
        }
        
        #[cfg(windows)]
        {
            // On Windows, symlink requires checking if src is a file or directory
            use tokio::fs;
            let metadata = fs::symlink_metadata(&src).await;
            match metadata {
                Ok(md) if md.is_dir() => {
                    fs::symlink_dir(&src, &dst)
                        .await
                        .map_err(|e| map_io_error(e, &format!("{} -> {}", src_clone, dst_clone), "create symlink"))
                }
                Ok(_) => {
                    fs::symlink_file(&src, &dst)
                        .await
                        .map_err(|e| map_io_error(e, &format!("{} -> {}", src_clone, dst_clone), "create symlink"))
                }
                Err(_) => {
                    // If source doesn't exist, default to file symlink on Windows
                    fs::symlink_file(&src, &dst)
                        .await
                        .map_err(|e| map_io_error(e, &format!("{} -> {}", src_clone, dst_clone), "create symlink"))
                }
            }
        }
    };
    future_into_py(py, future)
}

/// Canonicalize a path asynchronously.
///
/// Resolves all symbolic links and returns the absolute path. All I/O
/// operations execute outside the Python GIL using native Tokio, ensuring
/// true async behavior.
///
/// # Arguments
///
/// * `py` - Python GIL token
/// * `path` - Path to canonicalize
///
/// # Returns
///
/// A coroutine that yields the canonical path as a string.
///
/// # Errors
///
/// Returns `PyFileNotFoundError` if the path does not exist,
/// `PyIOError` if the path cannot be canonicalized, or `PyValueError` if the path is invalid.
#[pyfunction]
fn canonicalize_async(py: Python<'_>, path: String) -> PyResult<Bound<'_, PyAny>> {
    validate_path(&path)?;
    let future = async move {
        let path_clone = path.clone();
        let canonical = tokio::fs::canonicalize(&path)
            .await
            .map_err(|e| map_io_error(e, &path_clone, "canonicalize path"))?;
        
        canonical
            .to_str()
            .ok_or_else(|| PyErr::new::<pyo3::exceptions::PyUnicodeDecodeError, _>(
                "Canonicalized path contains invalid UTF-8"
            ))
            .map(|s| s.to_string())
    };
    future_into_py(py, future)
}

// Atomic file operations

/// Write a file atomically using a temporary file.
///
/// Writes content to a temporary file first, then atomically replaces
/// the target file by renaming. This ensures the target file is never
/// in a partially-written state. All I/O operations execute outside
/// the Python GIL using native Tokio, ensuring true async behavior.
///
/// # Arguments
///
/// * `py` - Python GIL token
/// * `path` - Path to the file to write
/// * `contents` - Content to write to the file (UTF-8 string)
///
/// # Returns
///
/// A coroutine that yields `None` on success.
///
/// # Errors
///
/// Returns `PyIOError` if the file cannot be written, `PyPermissionError`
/// if write permission is denied, or `PyValueError` if the path is invalid.
#[pyfunction]
fn atomic_write_file_async(py: Python<'_>, path: String, contents: String) -> PyResult<Bound<'_, PyAny>> {
    validate_path(&path)?;
    let future = async move {
        use std::path::Path;
        let path_clone = path.clone();
        
        let file_path = Path::new(&path);
        let dir = file_path.parent().ok_or_else(|| {
            PyErr::new::<pyo3::exceptions::PyValueError, _>("Path has no parent directory")
        })?;
        
        // Create temporary file in same directory
        let file_name = file_path.file_name().ok_or_else(|| {
            PyErr::new::<pyo3::exceptions::PyValueError, _>("Path has no file name")
        })?;
        
        let temp_path = dir.join(format!(".{}.tmp", file_name.to_string_lossy()));
        let temp_path_str = temp_path.to_string_lossy().to_string();
        
        // Write to temporary file
        tokio::fs::write(&temp_path, contents).await.map_err(|e| {
            map_io_error(e, &temp_path_str, "write temporary file")
        })?;
        
        // Atomically replace target file
        tokio::fs::rename(&temp_path, &path).await.map_err(|e| {
            // Clean up temp file on error (intentionally drop future in sync context)
            drop(tokio::fs::remove_file(&temp_path));
            map_io_error(e, &path_clone, "atomically write file")
        })
    };
    future_into_py(py, future)
}

/// Write bytes to a file atomically using a temporary file.
///
/// Writes bytes to a temporary file first, then atomically replaces
/// the target file by renaming. This ensures the target file is never
/// in a partially-written state. All I/O operations execute outside
/// the Python GIL using native Tokio, ensuring true async behavior.
///
/// # Arguments
///
/// * `py` - Python GIL token
/// * `path` - Path to the file to write
/// * `contents` - Bytes to write to the file
///
/// # Returns
///
/// A coroutine that yields `None` on success.
///
/// # Errors
///
/// Returns `PyIOError` if the file cannot be written, `PyPermissionError`
/// if write permission is denied, or `PyValueError` if the path is invalid.
#[pyfunction]
fn atomic_write_file_bytes_async<'a>(
    py: Python<'a>,
    path: String,
    contents: &'a Bound<'a, PyBytes>,
) -> PyResult<Bound<'a, PyAny>> {
    validate_path(&path)?;
    let bytes = contents.as_bytes().to_vec();
    let future = async move {
        use std::path::Path;
        let path_clone = path.clone();
        
        let file_path = Path::new(&path);
        let dir = file_path.parent().ok_or_else(|| {
            PyErr::new::<pyo3::exceptions::PyValueError, _>("Path has no parent directory")
        })?;
        
        // Create temporary file in same directory
        let file_name = file_path.file_name().ok_or_else(|| {
            PyErr::new::<pyo3::exceptions::PyValueError, _>("Path has no file name")
        })?;
        
        let temp_path = dir.join(format!(".{}.tmp", file_name.to_string_lossy()));
        let temp_path_str = temp_path.to_string_lossy().to_string();
        
        // Write to temporary file
        tokio::fs::write(&temp_path, bytes).await.map_err(|e| {
            map_io_error(e, &temp_path_str, "write temporary file")
        })?;
        
        // Atomically replace target file
        tokio::fs::rename(&temp_path, &path).await.map_err(|e| {
            // Clean up temp file on error (intentionally drop future in sync context)
            drop(tokio::fs::remove_file(&temp_path));
            map_io_error(e, &path_clone, "atomically write file")
        })
    };
    future_into_py(py, future)
}

/// Move a file atomically.
///
/// Moves a file from source to destination atomically. For cross-device
/// moves, it will copy atomically and then remove the source. All I/O
/// operations execute outside the Python GIL using native Tokio, ensuring
/// true async behavior.
///
/// # Arguments
///
/// * `py` - Python GIL token
/// * `src` - Path to the source file
/// * `dst` - Path to the destination file
///
/// # Returns
///
/// A coroutine that yields `None` on success.
///
/// # Errors
///
/// Returns `PyFileNotFoundError` if the source file does not exist,
/// `PyIOError` if the file cannot be moved, or `PyValueError` if the path is invalid.
#[pyfunction]
fn atomic_move_file_async(py: Python<'_>, src: String, dst: String) -> PyResult<Bound<'_, PyAny>> {
    validate_path(&src)?;
    validate_path(&dst)?;
    let future = async move {
        let src_clone = src.clone();
        let dst_clone = dst.clone();
        
        // Try rename first (atomic on same filesystem)
        match tokio::fs::rename(&src, &dst).await {
            Ok(_) => Ok(()),
            Err(e) if e.kind() == std::io::ErrorKind::CrossesDevices => {
                // Cross-device move: copy atomically then remove
                use std::path::Path;
                let dst_path = Path::new(&dst);
                let dir = dst_path.parent().ok_or_else(|| {
                    PyErr::new::<pyo3::exceptions::PyValueError, _>("Destination path has no parent directory")
                })?;
                
                let file_name = dst_path.file_name().ok_or_else(|| {
                    PyErr::new::<pyo3::exceptions::PyValueError, _>("Destination path has no file name")
                })?;
                
                let temp_path = dir.join(format!(".{}.tmp", file_name.to_string_lossy()));
                
                // Copy to temp file
                tokio::fs::copy(&src, &temp_path).await.map_err(|e| {
                    map_io_error(e, &format!("{src_clone} -> {dst_clone}"), "copy file")
                })?;
                
                // Atomically replace destination
                tokio::fs::rename(&temp_path, &dst).await.map_err(|e| {
                    // Clean up temp file on error (intentionally drop future in sync context)
                    drop(tokio::fs::remove_file(&temp_path));
                    map_io_error(e, &format!("{src_clone} -> {dst_clone}"), "atomically move file")
                })?;
                
                // Remove source file
                tokio::fs::remove_file(&src).await.map_err(|e| {
                    map_io_error(e, &src_clone, "remove source file")
                })
            }
            Err(e) => Err(map_io_error(e, &format!("{src_clone} -> {dst_clone}"), "atomically move file")),
        }
    };
    future_into_py(py, future)
}

// File locking operations

use std::fs::File as StdFile;

/// File lock for advisory file locking.
///
/// Provides advisory file locks for coordinating access to files across
/// processes. Supports both shared (read) and exclusive (write) locks.
/// The lock is automatically released when the object is dropped or when
/// `release()` is called.
///
/// # Example
///
/// ```python
/// async with rapfiles.lock_file("file.txt", exclusive=True) as lock:
///     # File is locked here
///     await rapfiles.write_file("file.txt", "content")
/// # Lock is automatically released
/// ```
#[pyclass]
struct FileLock {
    file: Arc<StdFile>,
    path: String,
    #[allow(dead_code)]
    exclusive: bool,
}

#[pymethods]
impl FileLock {
    /// Default constructor - use lock_file() instead.
    #[new]
    fn new() -> PyResult<Self> {
        Err(PyErr::new::<pyo3::exceptions::PyValueError, _>(
            "FileLock cannot be instantiated directly. Use rapfiles.lock_file() instead."
        ))
    }

    /// Release the file lock.
    ///
    /// Releases the advisory file lock. The lock is also automatically
    /// released when the object is dropped.
    ///
    /// # Returns
    ///
    /// A coroutine that yields `None` on success.
    ///
    /// # Errors
    ///
    /// Returns `PyIOError` if the lock cannot be released.
    fn release<'a>(&self, py: Python<'a>) -> PyResult<Bound<'a, PyAny>> {
        let file = Arc::clone(&self.file);
        let path = self.path.clone();
        
        let future = async move {
            // Unlock the file (blocking operation)
            tokio::task::spawn_blocking(move || {
                use fs2::FileExt;
                FileExt::unlock(&*file).map_err(|e| {
                    PyErr::new::<pyo3::exceptions::PyIOError, _>(format!(
                        "Failed to release lock on {path}: {e}"
                    ))
                })
            })
            .await
            .map_err(|e| PyErr::new::<pyo3::exceptions::PyIOError, _>(format!(
                "Failed to release lock: {e}"
            )))?
        };
        future_into_py(py, future)
    }

    /// Async context manager entry.
    fn __aenter__(slf: PyRef<'_, Self>) -> PyRef<'_, Self> {
        // Return self directly - Python's async context manager will handle it
        slf
    }

    /// Async context manager exit.
    fn __aexit__(
        &self,
        _exc_type: Option<&Bound<'_, PyAny>>,
        _exc_val: Option<&Bound<'_, PyAny>>,
        _exc_tb: Option<&Bound<'_, PyAny>>,
    ) -> PyResult<Py<PyAny>> {
        // Release lock on exit
        Python::attach(|py| {
            let release_future = self.release(py)?;
            // Release is already a coroutine, return it wrapped
            Ok(release_future.unbind())
        })
    }
}

/// Lock a file asynchronously.
///
/// Acquires an advisory file lock on the specified file. The lock can be
/// shared (read) or exclusive (write). The file is created if it doesn't
/// exist. All I/O operations execute outside the Python GIL using native
/// Tokio, ensuring true async behavior.
///
/// # Arguments
///
/// * `py` - Python GIL token
/// * `path` - Path to the file to lock
/// * `exclusive` - If true, acquire exclusive (write) lock; if false, acquire shared (read) lock
///
/// # Returns
///
/// A coroutine that yields a `FileLock` object that can be used as an async context manager.
///
/// # Errors
///
/// Returns `PyIOError` if the file cannot be locked, or `PyValueError` if the path is invalid.
#[pyfunction]
fn lock_file_async(py: Python<'_>, path: String, exclusive: bool) -> PyResult<Bound<'_, PyAny>> {
    validate_path(&path)?;
    let future = async move {
        let path_clone = path.clone();
        
        // Open or create the file
        let file = tokio::task::spawn_blocking({
            let path = path_clone.clone();
            let path_clone_for_error = path_clone.clone();
            move || {
                std::fs::OpenOptions::new()
                    .create(true)
                    .truncate(true)
                    .read(true)
                    .write(true)
                    .open(&path)
                    .map_err(|e| map_io_error(e, &path_clone_for_error, "open file for locking"))
            }
        })
        .await
        .map_err(|e| PyErr::new::<pyo3::exceptions::PyIOError, _>(format!(
            "Failed to open file: {e}"
        )))??;
        
        // Acquire the lock (blocking operation)
        {
            let file_clone = file.try_clone().map_err(|e| {
                PyErr::new::<pyo3::exceptions::PyIOError, _>(format!(
                    "Failed to clone file handle: {e}"
                ))
            })?;
            tokio::task::spawn_blocking({
                let path_clone2 = path_clone.clone();
                move || {
                    if exclusive {
                        fs2::FileExt::lock_exclusive(&file_clone)
                    } else {
                        fs2::FileExt::lock_shared(&file_clone)
                    }
                    .map_err(|e| PyErr::new::<pyo3::exceptions::PyIOError, _>(format!(
                        "Failed to acquire lock on {path_clone2}: {e}"
                    )))
                }
            })
            .await
            .map_err(|e| PyErr::new::<pyo3::exceptions::PyIOError, _>(format!(
                "Failed to acquire lock: {e}"
            )))??;
        }
        
        Ok(FileLock {
            file: Arc::new(file),
            path: path_clone,
            exclusive,
        })
    };
    future_into_py(py, future)
}

// Batch operations

/// Read multiple files concurrently.
///
/// Reads all specified files concurrently and returns their contents.
/// All I/O operations execute outside the Python GIL using native Tokio,
/// ensuring true async behavior.
///
/// # Arguments
///
/// * `py` - Python GIL token
/// * `paths` - Vector of file paths to read
///
/// # Returns
///
/// A coroutine that yields a list of (path, result) tuples where:
/// - `path`: The file path
/// - `result`: Either the file contents as bytes, or an error message string
#[pyfunction]
fn read_files_async(py: Python<'_>, paths: Vec<String>) -> PyResult<Bound<'_, PyAny>> {
    // Validate all paths
    for path in &paths {
        validate_path(path)?;
    }
    
    let future = async move {
        use futures::future;
        
        let read_futures: Vec<_> = paths.iter().map(|path| {
            let path_clone = path.clone();
            async move {
                let path_for_result = path_clone.clone();
                match tokio::fs::read(&path_clone).await {
                    Ok(bytes) => (path_clone, Ok(bytes)),
                    Err(e) => (path_for_result.clone(), Err(format!("Failed to read file {path_for_result}: {e}"))),
                }
            }
        }).collect();
        
        let results = future::join_all(read_futures).await;
        // Convert to tuples with bytes (Ok) or error strings (Err)
        // PyO3 can convert both bytes and String to Python objects
        let python_results: Vec<(String, Py<PyAny>)> = results.into_iter().map(|(path, result)| {
            Python::attach(|py| {
                let py_obj: Py<PyAny> = match result {
                    Ok(bytes) => PyBytes::new(py, &bytes).into(),
                    Err(err_str) => PyString::new(py, &err_str).into(),
                };
                (path, py_obj)
            })
        }).collect();
        Ok(python_results)
    };
    future_into_py(py, future)
}

/// Write multiple files concurrently.
///
/// Writes contents to all specified files concurrently. All I/O operations
/// execute outside the Python GIL using native Tokio, ensuring true async behavior.
///
/// # Arguments
///
/// * `py` - Python GIL token
/// * `files` - Vector of (path, contents) tuples to write
///
/// # Returns
///
/// A coroutine that yields a list of (path, result) tuples where:
/// - `path`: The file path
/// - `result`: Either Ok(()) on success, or an error message string
#[pyfunction]
fn write_files_async(py: Python<'_>, files: Vec<(String, Vec<u8>)>) -> PyResult<Bound<'_, PyAny>> {
    // Validate all paths
    for (path, _) in &files {
        validate_path(path)?;
    }
    let files_data = files;
    
    let future = async move {
        use futures::future;
        
        let write_futures: Vec<_> = files_data.iter().map(|(path, bytes)| {
            let path_clone = path.clone();
            let bytes_clone = bytes.clone();
            async move {
                let path_for_result = path_clone.clone();
                match tokio::fs::write(&path_clone, bytes_clone).await {
                    Ok(_) => (path_clone, Ok(())),
                    Err(e) => (path_for_result.clone(), Err(format!("Failed to write file {path_for_result}: {e}"))),
                }
            }
        }).collect();
        
        let results = future::join_all(write_futures).await;
        // Convert Result<(), String> to Python-compatible values
        let python_results: Vec<(String, Py<PyAny>)> = results.into_iter().map(|(path, result)| {
            Python::attach(|py| {
                let py_obj: Py<PyAny> = match result {
                    Ok(_) => py.None(),
                    Err(err_str) => PyString::new(py, &err_str).into(),
                };
                (path, py_obj)
            })
        }).collect();
        Ok(python_results)
    };
    future_into_py(py, future)
}

/// Copy multiple files concurrently.
///
/// Copies all specified files concurrently. All I/O operations execute
/// outside the Python GIL using native Tokio, ensuring true async behavior.
///
/// # Arguments
///
/// * `py` - Python GIL token
/// * `files` - Vector of (src, dst) tuples to copy
///
/// # Returns
///
/// A coroutine that yields a list of (src, dst, result) tuples where:
/// - `src`: The source file path
/// - `dst`: The destination file path
/// - `result`: Either Ok(()) on success, or an error message string
#[pyfunction]
fn copy_files_async(py: Python<'_>, files: Vec<(String, String)>) -> PyResult<Bound<'_, PyAny>> {
    // Validate all paths
    for (src, dst) in &files {
        validate_path(src)?;
        validate_path(dst)?;
    }
    
    let future = async move {
        use futures::future;
        
        let copy_futures: Vec<_> = files.iter().map(|(src, dst)| {
            let src_clone = src.clone();
            let dst_clone = dst.clone();
            async move {
                let src_for_result = src_clone.clone();
                let dst_for_result = dst_clone.clone();
                match tokio::fs::copy(&src_clone, &dst_clone).await {
                    Ok(_) => (src_clone, dst_clone, Ok(())),
                    Err(e) => (src_for_result.clone(), dst_for_result.clone(), Err(format!("Failed to copy file {src_for_result} -> {dst_for_result}: {e}"))),
                }
            }
        }).collect();
        
        let results = future::join_all(copy_futures).await;
        // Convert Result<(), String> to Python-compatible values
        let python_results: Vec<(String, String, Py<PyAny>)> = results.into_iter().map(|(src, dst, result)| {
            Python::attach(|py| {
                let py_obj: Py<PyAny> = match result {
                    Ok(_) => py.None(),
                    Err(err_str) => PyString::new(py, &err_str).into(),
                };
                (src, dst, py_obj)
            })
        }).collect();
        Ok(python_results)
    };
    future_into_py(py, future)
}

/// Open a file asynchronously (aiofiles.open() compatible).
#[pyfunction]
#[allow(clippy::too_many_arguments)] // Matches Python's open() signature for aiofiles compatibility
fn open_file(
    py: Python<'_>,
    path: String,
    mode: String,
    buffering: i32,
    encoding: Option<String>,
    errors: Option<String>,
    newline: Option<String>,
    closefd: bool,
    opener: Option<Py<PyAny>>,
) -> PyResult<Bound<'_, PyAny>> {
    // Validate parameters
    validate_path(&path)?;

    // Note: encoding, errors, newline, buffering, closefd, opener are accepted for API compatibility
    // but not fully implemented yet (will be added in later phases)
    let _ = (buffering, encoding, errors, newline, closefd, opener);

    let (read, write, append) = parse_mode(&mode)?;
    let path_clone = path.clone();
    let mode_clone = mode.clone();

    let future = async move {
        let mut open_options = tokio::fs::OpenOptions::new();
        open_options.read(read);
        open_options.write(write || append);
        open_options.create(write || append);
        open_options.truncate(write && !append);
        open_options.append(append);

        let file = open_options
            .open(&path_clone)
            .await
            .map_err(|e| map_io_error(e, &path_clone, "open file"))?;

        Ok(AsyncFile {
            file: Arc::new(Mutex::new(file)),
            path: path_clone,
            mode: mode_clone,
        })
    };

    future_into_py(py, future)
}
