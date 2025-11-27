# CLAUDE.md

This file provides guidance to Claude Code (claude.ai/code) when working with code in this repository.

## Project Overview

Excel-to-Parquet conversion tool that discovers Excel files in SOV folders, converts each sheet to unpivoted long format, and saves as Parquet with metadata columns. Supports `.xlsx`, `.xlsm`, `.xlsb`, and `.xls` formats.

## Commands

```bash
# Run interactive TUI
uv run excel-tui

# Run CLI conversion
uv run excel-converter /path/to/search -o /path/to/output
uv run excel-converter /path/to/search -o /output --rescan  # Force rescan

# Standalone converter (specific files, no SOV filtering or caching)
uv run python -m excel_converter.converter input.xlsx -o /output

# Generate test data
uv run python -m excel_converter.utils.test_data

# Tests
uv run pytest --cov                                    # All tests with coverage
uv run pytest tests/test_find_sov_folders.py           # Single file
uv run pytest tests/test_find_sov_folders.py::TestFindSovFoldersHappyPath::test_find_subdirs_in_sov_folder  # Single test
```

## Architecture

### Entry Points

| Module | Command | Purpose |
|--------|---------|---------|
| `src/excel_converter/tui.py` | `uv run excel-tui` | Interactive Textual TUI - screens for scan, browse, convert, results |
| `src/excel_converter/cli.py` | `uv run excel-converter` | CLI with directory scanning, caching (`data/files.csv`), SOV folder detection |
| `src/excel_converter/converter.py` | `python -m excel_converter.converter` | Standalone converter for explicit file lists (no scanning/caching) |

### Key Design Decisions

- **SOV folders**: Only processes files in paths containing `/SOV/` (case-sensitive)
- **No headers**: `has_header=False` - first row is data, columns named `column_1`, `column_2`, etc.
- **Unpivot to long format**: Wide data → normalized rows via `df.unpivot()`
- **Idempotent**: Skips files already in existing Parquet outputs
- **UUID filenames**: Prevents output collisions across sheets/files
- **Engine selection**: openpyxl (.xlsx/.xlsm), pyxlsb (.xlsb), xlrd (.xls)

### Output Schema

All Parquet files have this 6-column schema:
```
file_path (str), file_name (str), worksheet (str), row (int), column (int), value (str)
```

### Core Functions (src/excel_converter/cli.py)

- `scan_for_excel_files(root_dirs)` → DataFrame of discovered files
- `load_or_scan_files(root_dirs, rescan)` → Cached file list from `data/files.csv`
- `find_sov_folders(root_dirs)` → List of directories with `/SOV/` in path
- `process_excel_files(sov_folders, output_dir)` → Converts sheets to Parquet
- `get_processed_file_paths(output_dir)` → Set of already-processed file paths

### TUI Structure (src/excel_converter/tui.py)

Screens: `MainMenu` → `ScanScreen`, `FileBrowserScreen`, `ConversionScreen`, `ResultsScreen`, `SettingsScreen`
- Reuses core functions from `cli.py`
- Background workers via `@work(thread=True)` decorator
- Styles in `src/excel_converter/tui.tcss`

### Test Organization

Tests in `tests/` follow pattern: `Test{FunctionName}{Category}` where category is:
- `HappyPath` - Normal behavior
- `EdgeCases` - Boundary conditions
- `ErrorHandling` - Resilience to failures

Fixtures in `tests/conftest.py`: `sample_dataframe`, `create_test_excel`, `sov_folder_structure`, `disable_logging`
