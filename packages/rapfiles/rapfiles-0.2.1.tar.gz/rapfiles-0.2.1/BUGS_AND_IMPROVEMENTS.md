# Bugs and Improvements Report

## Critical Bugs

### 1. **Resource Leak: Temporary Files Not Cleaned Up** 🔴
**Location**: `src/lib.rs` lines 1443, 1504, 1565

**Issue**: In atomic write/move operations, temporary file cleanup uses `drop(tokio::fs::remove_file(&temp_path))` which drops a Future without awaiting it. The cleanup never executes, leaving temporary files behind on errors.

**Current Code**:
```rust
tokio::fs::rename(&temp_path, &path).await.map_err(|e| {
    // Clean up temp file on error (intentionally drop future in sync context)
    drop(tokio::fs::remove_file(&temp_path));  // ❌ This doesn't actually run!
    map_io_error(e, &path_clone, "atomically write file")
})
```

**Fix**: Use `tokio::spawn` or handle cleanup properly:
```rust
tokio::fs::rename(&temp_path, &path).await.map_err(|e| {
    // Spawn cleanup task (fire and forget)
    let temp_cleanup = temp_path.clone();
    tokio::spawn(async move {
        let _ = tokio::fs::remove_file(&temp_cleanup).await;
    });
    map_io_error(e, &path_clone, "atomically write file")
})
```

**Affected Functions**:
- `atomic_write_file_async` (line 1443)
- `atomic_write_file_bytes_async` (line 1504)
- `atomic_move_file_async` (line 1565)

---

### 2. **Data Loss Bug: File Locking Truncates Existing Files** 🔴
**Location**: `src/lib.rs` line 1706

**Issue**: When acquiring a file lock, the file is opened with `truncate(true)`, which truncates existing files to zero bytes. This causes data loss when locking files that already contain data.

**Current Code**:
```rust
std::fs::OpenOptions::new()
    .create(true)
    .truncate(true)  // ❌ This truncates existing files!
    .read(true)
    .write(true)
    .open(&path)
```

**Fix**: Remove `truncate(true)`. Lock files should not modify file content:
```rust
std::fs::OpenOptions::new()
    .create(true)
    // .truncate(true)  // ❌ REMOVE THIS
    .read(true)
    .write(true)
    .open(&path)
```

**Impact**: Any existing file that is locked will have its contents erased. This is a critical data loss bug.

---

### 3. **Inconsistent State: Atomic Move Source Removal Failure** 🟡
**Location**: `src/lib.rs` lines 1569-1572

**Issue**: In `atomic_move_file_async`, if the atomic move succeeds (copy + rename) but source removal fails, the source file is already gone but an error is returned. This leaves the system in an inconsistent state.

**Current Code**:
```rust
// Atomically replace destination
tokio::fs::rename(&temp_path, &dst).await.map_err(|e| {
    // ... cleanup ...
})?;

// Remove source file
tokio::fs::remove_file(&src).await.map_err(|e| {
    map_io_error(e, &src_clone, "remove source file")
})?;
```

**Fix**: Log a warning but don't fail if source removal fails after successful atomic move:
```rust
// Remove source file (best effort - move already succeeded)
if let Err(e) = tokio::fs::remove_file(&src).await {
    // Log warning but don't fail - the move was successful
    eprintln!("Warning: Failed to remove source file after atomic move: {}", e);
}
Ok(())
```

**Impact**: Medium - move operation succeeds but error is reported, confusing users.

---

## Medium Priority Issues

### 4. **Inconsistent Error Handling**
**Location**: `src/lib.rs` line 227-231

**Issue**: `read_file_bytes_async` creates `PyIOError` directly instead of using `map_io_error()` helper, making error messages inconsistent.

**Current Code**:
```rust
tokio::fs::read(&path).await.map_err(|e| {
    PyErr::new::<pyo3::exceptions::PyIOError, _>(format!(
        "Failed to read file {path_clone}: {e}"
    ))
})
```

**Fix**: Use `map_io_error` for consistency:
```rust
tokio::fs::read(&path).await.map_err(|e| {
    map_io_error(e, &path_clone, "read file")
})
```

**Affected Functions**:
- `read_file_bytes_async` (line 227)
- `append_file_async` (line 303-314)
- `create_dir_async` (line 344-347)
- `create_dir_all_async` (line 376-379)
- `remove_dir_async` (line 391-394)
- `remove_dir_all_async` (line 406-409)
- `list_dir_async` (line 438-441, 445-448)
- `is_file_async` (line 473-476)
- `is_dir_async` (line 489-492)
- `stat_async` (line 1008-1011)
- `walk_dir_async` (line 1093-1096)

---

### 5. **Race Condition in File Locking**
**Location**: `src/lib.rs` lines 1700-1716

**Issue**: There's a small window between opening the file and acquiring the lock where another process could also open the file. However, this is mitigated by the blocking lock acquisition, so it's a minor issue.

**Improvement**: Consider using `create_new(true)` instead of `create(true)` to fail if the lock file already exists, then handle the error appropriately. However, this might break existing behavior.

---

### 6. **Missing Error Context in Some Operations**
**Location**: Various locations in `src/lib.rs`

**Issue**: Some error messages don't include enough context. For example, `append_file_async` has two separate error messages that could be consolidated.

**Improvement**: Ensure all error messages include the operation being performed and the file path.

---

## Low Priority Improvements

### 7. **Path Validation Could Be More Comprehensive**
**Location**: `src/lib.rs` lines 25-37

**Current**: Only validates empty strings and null bytes.

**Improvement**: Consider validating:
- Maximum path length (platform-specific)
- Invalid characters (platform-specific)
- Path traversal sequences (though allowing `../` is intentional for relative paths)

**Note**: This is low priority as the current validation is reasonable for most use cases.

---

### 8. **Temporary File Naming Collision Risk**
**Location**: `src/lib.rs` lines 1432, 1493, 1555

**Issue**: Temporary files use pattern `.filename.tmp`. If multiple processes write to the same file atomically, they could create temp files with the same name, causing conflicts.

**Current Code**:
```rust
let temp_path = dir.join(format!(".{}.tmp", file_name.to_string_lossy()));
```

**Improvement**: Add process ID or random suffix to temp file names:
```rust
use std::process;
let temp_path = dir.join(format!(".{}.{}.tmp", 
    file_name.to_string_lossy(), 
    process::id()
));
```

Or use a UUID/random component for better uniqueness.

---

### 9. **Missing Cleanup on Write Failure in Atomic Operations**
**Location**: `src/lib.rs` lines 1436-1438, 1497-1499

**Issue**: If writing to the temporary file fails, the temp file is not cleaned up (though it wouldn't exist in this case). However, if a partial write occurs, the temp file might exist.

**Improvement**: Add cleanup in the write error handler as well.

---

### 10. **Documentation: Lock File Behavior**
**Location**: `rapfiles/__init__.py` docstrings for `lock_file`

**Issue**: Documentation doesn't mention that the lock file is created/truncated. Users should be aware that the lock file itself may be modified.

**Improvement**: Add note in docstring about lock file creation/truncation behavior.

---

## Summary

### Critical (Must Fix)
1. ✅ Temporary file cleanup not working (resource leak)
2. ✅ File locking truncates existing files (data loss)

### Medium Priority (Should Fix)
3. ⚠️ Atomic move source removal failure handling
4. ⚠️ Inconsistent error handling across functions

### Low Priority (Nice to Have)
5. 📝 Path validation enhancements
6. 📝 Temporary file naming improvements
7. 📝 Documentation improvements

---

## Recommended Fix Order

1. **Fix Bug #2** (File locking truncation) - Critical data loss
2. **Fix Bug #1** (Temporary file cleanup) - Resource leak
3. **Fix Issue #3** (Atomic move error handling) - User experience
4. **Fix Issue #4** (Error handling consistency) - Code quality
5. **Address improvements** (Items 5-10) - Polish
