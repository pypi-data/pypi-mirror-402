# Building and Testing rapfiles Phase 1

## Prerequisites

1. **Rust and Cargo** (required for building)
   ```bash
   # Install via rustup (recommended)
   curl --proto '=https' --tlsv1.2 -sSf https://sh.rustup.rs | sh
   source $HOME/.cargo/env
   
   # Verify installation
   rustc --version
   cargo --version
   ```

2. **Python 3.8+** (already installed)

3. **maturin** (Python package for building Rust extensions)
   ```bash
   pip install maturin
   ```

4. **pytest** (for running tests)
   ```bash
   pip install pytest pytest-asyncio
   ```

## Building the Project

### Development Build (Recommended for testing)

```bash
cd rapfiles
maturin develop
```

This will:
- Compile the Rust extension
- Install it in development mode
- Make it available for import in Python

### Production Build

```bash
maturin build
```

This creates wheel files in `dist/` directory.

## Running Tests

### Run All Tests

```bash
pytest
```

### Run Specific Test Files

```bash
# Basic operations
pytest test_rapfiles.py

# File handles
pytest test_file_handles.py

# Directory operations
pytest test_directories.py

# Metadata operations
pytest test_metadata.py

# Extended operations
pytest test_extended_operations.py

# aiofiles compatibility
pytest test_aiofiles_compatibility.py
```

### Run with Verbose Output

```bash
pytest -v
```

### Run with Coverage

```bash
pytest --cov=rapfiles --cov-report=html
```

## Testing aiofiles Compatibility

The compatibility tests verify that rapfiles can be used as a drop-in replacement:

```bash
pytest test_aiofiles_compatibility.py -v
```

These tests import `rapfiles as aiofiles` and use the same API patterns.

## Verifying True Async Behavior

### Using Fake Async Detector

```bash
# Install rap-bench if not already installed
pip install rap-bench

# Run the detector
rap-bench detect rapfiles
```

This verifies that all operations are truly async (GIL-independent) and not fake async.

## Common Issues

### Issue: "rustc not found"

**Solution**: Install Rust via rustup (see Prerequisites above)

### Issue: "maturin: command not found"

**Solution**: 
```bash
pip install maturin
# Or use: python3 -m maturin
```

### Issue: Import errors after building

**Solution**: Make sure you're in the correct Python environment:
```bash
# Check Python path
python3 -c "import sys; print(sys.path)"

# Rebuild
maturin develop --release
```

### Issue: Tests fail with "ModuleNotFoundError: No module named '_rapfiles'"

**Solution**: The Rust extension hasn't been built. Run `maturin develop` first.

## Next Steps After Building

1. **Run all tests** to verify functionality
2. **Run compatibility tests** to verify aiofiles drop-in replacement
3. **Run Fake Async Detector** to verify true async behavior
4. **Test with real-world scenarios** to validate performance

## Performance Testing

After building, you can compare performance with aiofiles:

```python
import asyncio
import time
import rapfiles

async def benchmark():
    start = time.time()
    # Your async file operations here
    end = time.time()
    print(f"Time: {end - start}s")
```

## Integration with CI/CD

For GitHub Actions or other CI systems, add:

```yaml
- name: Install Rust
  uses: actions-rs/toolchain@v1
  with:
    toolchain: stable

- name: Build
  run: maturin develop

- name: Test
  run: pytest
```
