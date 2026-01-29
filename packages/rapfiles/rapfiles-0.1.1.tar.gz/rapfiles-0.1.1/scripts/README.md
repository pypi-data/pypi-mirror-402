# rapfiles Scripts

This directory contains utility scripts for development and release management.

## Available Scripts

### `check_metadata.py`
Validates package metadata for PyPI releases. Checks wheel and source distribution metadata to ensure correctness.

**Usage:**
```bash
python3 scripts/check_metadata.py
```

### `test_pypi_build.sh`
Builds and tests the package locally to verify it's ready for PyPI release.

**Usage:**
```bash
bash scripts/test_pypi_build.sh
```

## Adding New Scripts

When adding new scripts:
1. Place them in this `scripts/` directory
2. Make them executable (`chmod +x script.sh`)
3. Add documentation to this README
4. Ensure they work from the project root directory
