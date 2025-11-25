# CLAUDE.md

This file provides guidance to Claude Code (claude.ai/code) when working with code in this repository.

## Project Overview

Excel-to-Parquet conversion tool that recursively searches directories for folders containing `/SOV/` in their path, discovers Excel files (.xlsx, .xls) within those folders, and converts each sheet to a separate Parquet file with UUID-based naming and metadata columns.

## Commands

```bash
# Run the main conversion script
uv run python excel_to_parquet.py /path/to/search --output /path/to/output

# Run all tests with coverage
uv run pytest --cov

# Run a specific test file
uv run pytest tests/test_find_sov_folders.py

# Run a specific test
uv run pytest tests/test_find_sov_folders.py::TestFindSovFoldersHappyPath::test_find_subdirs_in_sov_folder

# Install dependencies
uv sync
```

## Architecture

### Core Functions (excel_to_parquet.py)

- `find_sov_folders(root_dirs)` - Recursively searches root directories for paths containing `/SOV/`. Returns subdirectories *within* SOV folders (not the SOV folder itself). Case-sensitive matching.

- `process_excel_files(sov_folders, output_dir)` - Converts Excel files to Parquet. Key behaviors:
  - Uses `header=None` to treat first row as data, not column headers
  - Adds `file_path` (column 0) and `row_number` (column 1) metadata columns
  - Each sheet becomes a separate Parquet file with UUID filename
  - Continues processing on individual file/sheet errors

- `validate_inputs()` - Pre-flight validation of directory existence and permissions

- `main()` - CLI entry point with argparse. Exit codes: 0=success, 1=user error, 2=processing error, 3=unexpected error

### Test Structure

Tests organized by function with three categories per function:
- `HappyPath` - Normal expected behavior
- `EdgeCases` - Boundary conditions (empty inputs, case sensitivity)
- `ErrorHandling` - Resilience (corrupted files, permission errors)

Shared fixtures in `conftest.py`: `sample_dataframe`, `create_test_excel`, `sov_folder_structure`, `disable_logging`
