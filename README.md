# Excel-to-Parquet Converter

![Python Version](https://img.shields.io/badge/python-%3E%3D3.12-blue)

> Discover Excel files in SOV folders, convert each sheet to normalized long format, and save as Parquet with full metadata tracking.

---

## Table of Contents

1. [Overview](#overview)
2. [Features](#features)
3. [Quick Start](#quick-start)
4. [Installation](#installation)
5. [Usage](#usage)
6. [How It Works](#how-it-works)
7. [Output Format](#output-format)
8. [TUI Guide](#tui-guide)
9. [CLI Reference](#cli-reference)
10. [Architecture](#architecture)
11. [Testing](#testing)
12. [Design Decisions](#design-decisions)
13. [Troubleshooting](#troubleshooting)
14. [Contributing](#contributing)
15. [License](#license)

---

## Overview

Excel-to-Parquet is a Python conversion tool designed for discovering and processing Excel files in SOV (Statement of Value) folder structures. It converts Excel sheets from wide format to normalized long format, preserving full data lineage through metadata columns.

The tool provides both a **command-line interface** for batch processing and automation, and an **interactive terminal UI** (TUI) for guided workflows with visual feedback. Both interfaces share the same robust conversion engine built on Polars for high-performance data processing.

**What makes this tool different:**
- **SOV-focused**: Automatically discovers files in paths containing `/SOV/` (case-sensitive)
- **Idempotent**: Skips already-processed files on repeated runs
- **Long format output**: Unpivots wide Excel data to normalized schema for analytical queries
- **Full lineage**: Every cell value tracked with source file, worksheet, row, and column
- **Multi-format support**: Handles `.xlsx`, `.xlsm`, `.xlsb`, and `.xls` files

**Ideal for:**
- Data engineers processing SOV folder structures
- Analysts needing normalized Excel data in data lakes
- ETL pipelines requiring reproducible Excel-to-Parquet conversion
- Teams working with heterogeneous Excel files that need consistent output schema

---

## Features

### Discovery
- Recursive directory scanning for Excel files
- SOV folder detection (case-sensitive `/SOV/` matching)
- File list caching with `data/files.csv` for fast repeated runs
- Support for multiple root directories in a single scan
- Cross-platform path handling (Windows and Unix)

### Processing
- Multi-format Excel support: `.xlsx`, `.xlsm`, `.xlsb`, `.xls`
- Automatic engine selection per file type (openpyxl, pyxlsb, xlrd)
- Multi-sheet processing (each sheet → separate Parquet file)
- Parallel processing with ThreadPoolExecutor for I/O-bound operations
- Graceful error handling (individual failures don't stop the pipeline)
- Idempotent operation (skips already-processed files)

### Output
- Normalized long format via unpivoting
- Consistent 6-column schema across all outputs
- Metadata tracking: `file_path`, `file_name`, `worksheet`, `row`, `column`, `value`
- UUID-based filenames prevent collisions
- Efficient Parquet format with compression

### Interface
- **CLI**: Batch processing with caching, logging, and exit codes
- **TUI**: Interactive screens for scan, browse, convert, and results inspection
- **Standalone CLI**: Direct file conversion without scanning/caching

---

## Quick Start

Get up and running in 5 steps:

```bash
# 1. Clone the repository
git clone https://github.com/mmadahar/excel-download.git
cd excel-download

# 2. Install dependencies (requires Python 3.12+ and uv)
uv sync

# 3. Launch the interactive TUI
uv run python tui.py

# 4. In the TUI: Press '1' to scan, enter directory path, start scan
# 5. Press '3' to convert, enter output path, start conversion
```

**Done!** Your Parquet files are ready in the output directory.

---

## Installation

### Prerequisites

- **Python 3.12 or higher**
- **[uv](https://docs.astral.sh/uv/)** package manager

### Setup

```bash
# Clone the repository
git clone https://github.com/mmadahar/excel-download.git
cd excel-download

# Install all dependencies from lockfile
uv sync

# Verify installation
uv run python --version  # Should show Python 3.12+
```

### Dependencies Installed

- `polars` (>=1.35.2) - High-performance DataFrame operations
- `openpyxl` (>=3.1.5) - Modern Excel format (.xlsx, .xlsm)
- `pyxlsb` (>=1.0.10) - Binary Excel format (.xlsb)
- `xlrd` (>=2.0.2) - Legacy Excel format (.xls)
- `pyarrow` (>=22.0.0) - Parquet file format support
- `textual` (>=6.6.0) - Terminal UI framework

---

## Usage

### TUI (Interactive Terminal UI)

**Best for:** Visual workflows, progress monitoring, file inspection

```bash
uv run python tui.py
```

See [TUI Guide](#tui-guide) for detailed screen documentation.

---

### CLI (Main) - Directory Scanning with Caching

**Best for:** Batch processing, automation, repeated runs on same directory

```bash
# Basic usage
uv run python excel_to_parquet.py /path/to/search -o /path/to/output

# Multiple root directories
uv run python excel_to_parquet.py /data/p1 /data/p2 -o /output

# Force rescan (ignore cache)
uv run python excel_to_parquet.py /data -o /output --rescan

# With debug logging
uv run python excel_to_parquet.py /data -o /output -l DEBUG

# Log to file
uv run python excel_to_parquet.py /data -o /output --log-file conversion.log
```

**Arguments:**
- `root_dirs` (required) - One or more directories to search
- `-o, --output` (required) - Output directory for Parquet files
- `-r, --rescan` (optional) - Force fresh scan, ignore cached file list
- `-l, --log-level` (optional) - DEBUG, INFO, WARNING, ERROR, CRITICAL (default: INFO)
- `--log-file` (optional) - Log file path (appends)

---

### CLI (Standalone) - Direct File Conversion

**Best for:** Specific file lists, no SOV filtering, simple conversion

```bash
# Single file
uv run python excel_to_parquet_polars.py input.xlsx -o /output

# Multiple files
uv run python excel_to_parquet_polars.py file1.xlsx file2.xlsm file3.xls -o /output

# With wildcards
uv run python excel_to_parquet_polars.py /data/*.xlsx -o /output
```

**Arguments:**
- `files` (required) - One or more Excel files to convert
- `-o, --output` (required) - Output directory
- `-l, --log-level` (optional) - Logging level
- `--log-file` (optional) - Log file path

---

## How It Works

### Pipeline Overview

```
┌──────────────────────────────────────────────────────────────────────┐
│ PHASE 1: DISCOVERY                                                   │
│   Scan directories → Filter by /SOV/ → Cache to data/files.csv      │
└────────────────────────────────┬─────────────────────────────────────┘
                                 ▼
┌──────────────────────────────────────────────────────────────────────┐
│ PHASE 2: FILTERING                                                   │
│   Load cached files → Skip already-processed → Validate existence    │
└────────────────────────────────┬─────────────────────────────────────┘
                                 ▼
┌──────────────────────────────────────────────────────────────────────┐
│ PHASE 3: CONVERSION (Parallel)                                       │
│   Read Excel → Unpivot to long format → Add metadata → Write Parquet│
└──────────────────────────────────────────────────────────────────────┘
```

### Phase 1: Discovery

1. **Directory Traversal**: Recursively search root directories using `Path.rglob("*")`
2. **SOV Filtering**: Keep only paths containing `/SOV/` (case-sensitive)
3. **Extension Matching**: Filter for `.xlsx`, `.xlsm`, `.xlsb`, `.xls` (case-insensitive)
4. **Cache Creation**: Save discovered files to `data/files.csv` with metadata
5. **Subsequent Runs**: Load from cache unless `--rescan` flag is set

### Phase 2: Filtering

1. **Load File List**: Read from `data/files.csv`
2. **Idempotent Check**: Scan existing Parquet files for `file_path` values
3. **Skip Processed**: Filter out files already in output directory
4. **Existence Check**: Verify files still exist on disk

### Phase 3: Conversion

1. **Engine Selection**: Choose reader based on extension (openpyxl, pyxlsb, xlrd)
2. **Sheet Reading**: Load all sheets with `has_header=False` (first row is data)
3. **Unpivoting**: Transform wide format to long format:
   ```
   Wide:  | Product | Q1  | Q2  |
          | Widget  | 100 | 150 |
   
   Long:  | row | column | value   |
          | 0   | 0      | Product |
          | 0   | 1      | Q1      |
          | 0   | 2      | Q2      |
          | 1   | 0      | Widget  |
          | 1   | 1      | 100     |
          | 1   | 2      | 150     |
   ```
4. **Metadata Addition**: Add `file_path`, `file_name`, `worksheet` columns
5. **UUID Naming**: Generate unique filename (e.g., `a7f2b3c4-...-ef012345.parquet`)
6. **Parallel Execution**: Process multiple files concurrently via ThreadPoolExecutor

---

## Output Format

### Schema

All Parquet files share this 6-column normalized schema:

| Column | Type | Description | Example |
|--------|------|-------------|---------|
| `file_path` | str | Absolute path to source Excel file | `/data/projects/SOV/2024/report.xlsx` |
| `file_name` | str | Basename of Excel file | `report.xlsx` |
| `worksheet` | str | Sheet name from Excel workbook | `Q1 Summary` |
| `row` | int | 0-indexed row number in original sheet | `0`, `1`, `2`, ... |
| `column` | int | 0-indexed column number | `0`, `1`, `2`, ... |
| `value` | str | Cell value cast to string | `"Revenue"`, `"1000.50"`, `""` |

### Example Output

**Source Excel** (`sales.xlsx`, sheet "Q1"):
```
     A        B      C
1    Product  Jan    Feb
2    Widget   100    150
3    Gadget   200    250
```

**Output Parquet** (`abc123...xyz.parquet`):
```
┌─────────────────────┬───────────┬───────────┬─────┬────────┬─────────┐
│ file_path           │ file_name │ worksheet │ row │ column │ value   │
├─────────────────────┼───────────┼───────────┼─────┼────────┼─────────┤
│ /data/sales.xlsx    │sales.xlsx │ Q1        │ 0   │ 0      │ Product │
│ /data/sales.xlsx    │sales.xlsx │ Q1        │ 0   │ 1      │ Jan     │
│ /data/sales.xlsx    │sales.xlsx │ Q1        │ 0   │ 2      │ Feb     │
│ /data/sales.xlsx    │sales.xlsx │ Q1        │ 1   │ 0      │ Widget  │
│ /data/sales.xlsx    │sales.xlsx │ Q1        │ 1   │ 1      │ 100     │
│ /data/sales.xlsx    │sales.xlsx │ Q1        │ 1   │ 2      │ 150     │
│ /data/sales.xlsx    │sales.xlsx │ Q1        │ 2   │ 0      │ Gadget  │
│ /data/sales.xlsx    │sales.xlsx │ Q1        │ 2   │ 1      │ 200     │
│ /data/sales.xlsx    │sales.xlsx │ Q1        │ 2   │ 2      │ 250     │
└─────────────────────┴───────────┴───────────┴─────┴────────┴─────────┘
```

### Querying Parquet Files

```python
import polars as pl

# Load all Parquet files
df = pl.read_parquet("output/*.parquet")

# Filter by worksheet
q1_data = df.filter(pl.col("worksheet") == "Q1")

# Get all values from first row (often headers)
headers = df.filter(pl.col("row") == 0).sort("column")

# Count rows per file
counts = df.group_by("file_path").agg(pl.count().alias("cell_count"))

# Reconstruct original wide format
wide = df.pivot(
    values="value",
    index=["file_path", "worksheet", "row"],
    on="column"
)
```

---

## TUI Guide

The interactive Text User Interface provides a user-friendly alternative to the CLI with visual feedback, progress tracking, and data exploration capabilities.

### Quick Start

```bash
# Launch the TUI
uv run python tui.py

# Complete workflow:
# 1. Press '1' to scan directories
# 2. Enter path: /Users/matthew/Python/excel-download/data/test_excel
# 3. Press 's' to start scan
# 4. Press 'ESC' then '3' for conversion
# 5. Press 'c' to convert files
# 6. Press 'ESC' then '4' to view results
# 7. Click any file to preview data
```

### Features

The TUI consists of 6 screens accessible from the main menu:

1. **Main Menu** - Navigation hub with keyboard shortcuts (1-5 for screens, q to quit)
2. **Scan Screen** - Directory scanning with multi-directory support, force rescan toggle, real-time progress, and extension breakdown
3. **File Browser** - Sortable table of discovered files with refresh capability
4. **Conversion Screen** - Excel-to-Parquet conversion with real-time progress, per-file/sheet status, and idempotent operation
5. **Results Viewer** - List of generated Parquet files with metadata and interactive preview
6. **Settings Screen** - Configuration view showing file registry, supported formats, and output schema

### Keyboard Shortcuts

#### Global Navigation
| Key | Context | Action |
|-----|---------|--------|
| `1` | MainMenu | Go to Scan Screen |
| `2` | MainMenu | Go to File Browser |
| `3` | MainMenu | Go to Conversion Screen |
| `4` | MainMenu | Go to Results Screen |
| `5` | MainMenu | Go to Settings Screen |
| `q` | MainMenu | Quit application |
| `ESC` | Any screen | Go back to MainMenu |

#### Screen-Specific
| Key | Screen | Action |
|-----|--------|--------|
| `s` | Scan | Start scan |
| `c` | Conversion | Start conversion |
| `r` | Browser, Results | Refresh data |
| `↑`/`↓` | Tables | Navigate rows |
| `PgUp`/`PgDn` | Tables | Scroll page |

### Screen Flow

```
                     ┌─────────────┐
                     │  MainMenu   │ ← Entry point (1-5 or q)
                     └──────┬──────┘
              ┌─────────────┼─────────────────────┐
              │             │             │        │
         [1] Scan      [2] Browse   [3] Convert   [4] Results
              │             │             │             │
              ▼             ▼             ▼             ▼
      ┌──────────────┐ ┌─────────────┐ ┌──────────────┐ ┌─────────────┐
      │ ScanScreen   │ │FileBrowser  │ │Conversion    │ │Results      │
      │              │ │Screen       │ │Screen        │ │Screen       │
      │• Enter path  │ │• View files │ │• Set output  │ │• List files │
      │• Force rescan│ │• Refresh    │ │• Run convert │ │• Preview    │
      │• View summary│ │• Sort/scroll│ │• View logs   │ │• Inspect    │
      └──────────────┘ └─────────────┘ └──────────────┘ └─────────────┘
           │                                   │
           └→ saves data/files.csv ←───────────┘
           └→ creates *.parquet ──────────────→ reads
```

### Screen Details

#### 1. Scan Screen
**Purpose:** Discover Excel files across directories

**Features:**
- Enter single or multiple directories (comma-separated)
- Toggle "Force Rescan" to ignore cached results
- Real-time progress bar during scanning
- Detailed log output showing discovered files
- Extension breakdown (.xlsx, .xlsm, .xlsb, .xls)

**Usage:**
- Enter path(s): `/data/projects` or `/data/p1,/data/p2`
- Toggle "Force Rescan" if needed
- Press `s` to start scan
- Monitor progress in log window

#### 2. File Browser
**Purpose:** View and explore discovered Excel files

**Features:**
- Sortable data table (filename, extension, directory, timestamp)
- Auto-loads from cached registry (`data/files.csv`)
- Refresh capability to reload list

**Usage:**
- Navigate with arrow keys
- Press `r` to refresh
- Press `ESC` to return to menu

#### 3. Conversion Screen
**Purpose:** Convert Excel files to Parquet format

**Features:**
- Configurable output directory
- Real-time progress indicator
- Per-file and per-sheet conversion status
- Automatic skip of already-processed files (idempotent)
- Error handling and reporting
- Final statistics summary

**Usage:**
- Enter output directory (default: `data/output`)
- Press `c` to start conversion
- Watch progress bar and detailed logs
- Review completion summary

**What happens:**
- Reads each Excel file using appropriate engine
- Processes all sheets within each file
- Converts wide format to long (unpivoted) format
- Adds metadata columns (file_path, file_name, worksheet, row, column, value)
- Saves each sheet to UUID-named Parquet file
- Skips files already in output directory

#### 4. Results Viewer
**Purpose:** Inspect generated Parquet files and preview data

**Features:**
- List all Parquet files in output directory
- File metadata: filename, size (KB), modified date, row count
- Interactive selection - click to preview
- Sample data preview (first 10 rows)
- Column information

**Usage:**
- Enter output directory path if different from default
- Browse list of Parquet files
- Click any row to preview data
- View first 10 rows with all columns

#### 5. Settings Screen
**Purpose:** View configuration and system information

**Displays:**
- File registry location and status
- Supported Excel formats and engines
- Output format specifications
- Schema definition
- Complete keyboard shortcut reference

### Tips

- Use comma-separated paths for multiple directories: `/path1,/path2`
- Enable "Force Rescan" to ignore cached file list
- Already-processed files are automatically skipped
- Click on Parquet files in Results to preview data
- Check Settings screen for format and engine details

### Implementation Notes

**Architecture:**
- Built with Textual 6.6.0 framework
- Async operations via `@work(thread=True)` for non-blocking UI
- Reuses core functions from `excel_to_parquet.py` (no code duplication)
- Reactive state management for progress updates
- Custom styling in `tui.tcss` (with inline CSS fallback)

**Integration:**
- Uses same file registry (`data/files.csv`) as CLI
- Identical output format to CLI tool
- Preserves idempotency (skips processed files)
- Compatible with CLI workflows

**Testing:**
```bash
# Run TUI test suite
uv run python test_tui.py
```

### Troubleshooting

**"No files discovered yet"**
- Run a scan first (Option 1)
- Verify directory path is correct
- Check that Excel files exist in `/SOV/` paths

**"Output directory does not exist"**
- TUI will create it automatically during conversion
- Verify write permissions on parent directory

**Scan finds no files**
- Verify directory exists
- Check for `/SOV/` in paths (case-sensitive)
- Ensure file extensions are .xlsx, .xlsm, .xlsb, or .xls

**Conversion errors**
- Check log output for specific error messages
- Verify Excel files are not corrupted
- Ensure appropriate engine is installed (openpyxl, pyxlsb, xlrd)

---

## CLI Reference

### Main CLI (excel_to_parquet.py)

#### Arguments

| Argument | Short | Type | Required | Default | Description |
|----------|-------|------|----------|---------|-------------|
| `root_dirs` | - | positional | Yes | - | One or more root directories to search |
| `--output` | `-o` | string | Yes | - | Output directory for Parquet files |
| `--rescan` | `-r` | flag | No | False | Force fresh scan, ignore cache |
| `--log-level` | `-l` | choice | No | INFO | DEBUG, INFO, WARNING, ERROR, CRITICAL |
| `--log-file` | - | string | No | None | Log file path (append mode) |

#### Exit Codes

| Code | Constant | Meaning |
|------|----------|---------|
| 0 | EXIT_SUCCESS | Successful completion |
| 1 | EXIT_USER_ERROR | Invalid arguments, missing directories, Ctrl+C |
| 3 | EXIT_UNEXPECTED_ERROR | Unhandled exceptions |

---

### Standalone CLI (excel_to_parquet_polars.py)

#### Arguments

| Argument | Short | Type | Required | Default | Description |
|----------|-------|------|----------|---------|-------------|
| `files` | - | positional | Yes | - | One or more Excel files to process |
| `--output` | `-o` | string | Yes | - | Output directory |
| `--log-level` | `-l` | choice | No | INFO | Logging level |
| `--log-file` | - | string | No | None | Log file path |

#### Exit Codes

| Code | Constant | Meaning |
|------|----------|---------|
| 0 | EXIT_SUCCESS | Successful completion |
| 1 | EXIT_USER_ERROR | File not found, invalid input, Ctrl+C |
| 2 | EXIT_PROCESSING_ERROR | Some sheets failed (non-fatal) |
| 3 | EXIT_UNEXPECTED_ERROR | Unhandled exceptions |

---

## Architecture

### Entry Points

| Script | Purpose | When to Use |
|--------|---------|-------------|
| `tui.py` | Interactive TUI with screens for scan, browse, convert, results | Visual workflows, progress monitoring, file inspection |
| `excel_to_parquet.py` | CLI with directory scanning, caching, SOV filtering | Batch processing, automation, repeated runs |
| `excel_to_parquet_polars.py` | Standalone converter for explicit file lists | Specific files, no SOV filtering, simple conversion |

### Data Flow Diagram

```
┌─────────────┐
│  Root Dirs  │
└──────┬──────┘
       │
       ▼
┌──────────────────────────────────┐
│  scan_for_excel_files()          │
│  • Recursive directory traversal │
│  • Extension filtering           │
│  • Timestamp recording           │
└──────┬───────────────────────────┘
       │
       ▼
┌──────────────────────────────────┐
│  data/files.csv (cache)          │
│  ┌────────────────────────────┐  │
│  │ file_path | ext | timestamp│  │
│  └────────────────────────────┘  │
└──────┬───────────────────────────┘
       │
       ▼
┌──────────────────────────────────┐
│  find_sov_folders()              │
│  • Filter paths with /SOV/       │
│  • Parallel traversal            │
│  • Deduplication                 │
└──────┬───────────────────────────┘
       │
       ▼
┌──────────────────────────────────┐
│  get_processed_file_paths()      │
│  • Scan existing Parquet files   │
│  • Extract file_path values      │
│  • Return set for O(1) lookup    │
└──────┬───────────────────────────┘
       │
       ▼
┌──────────────────────────────────┐
│  process_excel_files()           │
│  • ThreadPoolExecutor (parallel) │
│  • Engine selection per file     │
│  • Sheet reading & unpivoting    │
│  • Metadata addition             │
│  • UUID filename generation      │
└──────┬───────────────────────────┘
       │
       ▼
┌──────────────────────────────────┐
│  output/*.parquet                │
│  ┌────────────────────────────┐  │
│  │ file_path | file_name | .. │  │
│  │ worksheet | row | col | val│  │
│  └────────────────────────────┘  │
└──────────────────────────────────┘
```

### Core Functions

#### `find_sov_folders(root_dirs: List[str]) -> List[Path]`
Discovers directories containing `/SOV/` in their path using parallel traversal.

#### `scan_for_excel_files(root_dirs: List[Path]) -> pl.DataFrame`
Recursively scans directories for Excel files, returns DataFrame with metadata.

#### `load_or_scan_files(root_dirs: List[str], rescan: bool) -> pl.DataFrame`
Loads cached file list from `data/files.csv` or performs fresh scan.

#### `get_processed_file_paths(output_dir: Path) -> Set[str]`
Returns set of file paths already processed (for idempotent operation).

#### `process_excel_files(sov_folders: List[Path], output_dir: Path) -> None`
Converts Excel files to Parquet with parallel processing and metadata tracking.

---

## Testing

### Running Tests

```bash
# All tests with coverage
uv run pytest --cov

# Single test file
uv run pytest tests/test_find_sov_folders.py

# Single test class
uv run pytest tests/test_find_sov_folders.py::TestFindSovFoldersHappyPath

# Single test
uv run pytest tests/test_find_sov_folders.py::TestFindSovFoldersHappyPath::test_find_subdirs_in_sov_folder

# Verbose output
uv run pytest -v

# Coverage with missing lines report
uv run pytest --cov --cov-report=term-missing

# Stop at first failure
uv run pytest -x
```

### Test Organization

Tests follow a three-category pattern per function:

```python
# Normal expected behavior
class TestFindSovFoldersHappyPath:
    def test_find_subdirs_in_sov_folder(...)
    def test_results_are_sorted(...)

# Boundary conditions
class TestFindSovFoldersEdgeCases:
    def test_empty_root_dirs_returns_empty_list(...)
    def test_case_sensitive_matching(...)

# Error resilience
class TestFindSovFoldersErrorHandling:
    def test_nonexistent_root_dir_continues(...)
    def test_permission_denied_logs_warning(...)
```

### Test Fixtures

Shared fixtures in `tests/conftest.py`:

- **`sample_dataframe`** - 5-row Polars DataFrame for basic testing
- **`create_test_excel`** - Factory to create multi-sheet Excel files
- **`sov_folder_structure`** - Realistic SOV directory tree with test files
- **`disable_logging`** - Suppresses log output during tests

### Coverage Summary

| Module | Coverage | Notes |
|--------|----------|-------|
| `excel_to_parquet.py` | 75% | Core logic well-tested, some error paths uncovered |
| `tests/test_*.py` | 98-100% | Comprehensive test coverage |
| `tui.py` | 26% | TUI requires manual testing |

---

## Design Decisions

### Why SOV Folders Only?

**Decision:** Only process files in paths containing `/SOV/` (case-sensitive)

**Rationale:**
- Focus on Statement of Value data structures (organizational convention)
- Prevents accidental processing of unrelated Excel files
- Case sensitivity ensures deliberate folder naming
- Cross-platform consistency via POSIX path conversion

### Why Unpivot to Long Format?

**Decision:** Transform wide Excel data to normalized long format

**Rationale:**
- Consistent schema across all outputs regardless of source structure
- Normalized format is standard for relational databases and analytical queries
- Enables efficient filtering, grouping, and joining
- Most BI tools expect long format
- Handles heterogeneous Excel files with different column counts

**Trade-off:** Increased row count and file size (N columns × M rows = N×M output rows)

### Why has_header=False?

**Decision:** Treat first row as data, not column headers

**Rationale:**
- SOV files often have inconsistent or no headers
- Avoids assumptions about which row contains headers
- Preserves all information (first row not lost)
- Uniform processing regardless of source structure
- Users can implement custom header detection during analysis

### Why UUID Filenames?

**Decision:** Use `uuid4()` for output Parquet filenames

**Rationale:**
- Prevents collisions across sheets with identical names
- Parallel-safe (no coordination needed between workers)
- Simplicity (no sanitization, length limits, uniqueness checks)
- Source information preserved in `file_path` column

**Trade-off:** Filenames not human-readable (must read Parquet metadata)

### Why ThreadPoolExecutor?

**Decision:** Use thread-based parallelism instead of processes

**Rationale:**
- Excel reading and Parquet writing are I/O-bound, not CPU-bound
- GIL released during I/O operations (true parallelism)
- Lower overhead than multiprocessing
- Shared memory space (no serialization costs)
- Polars itself uses multi-threading internally

### Why Idempotent Processing?

**Decision:** Skip files already present in output Parquet files

**Rationale:**
- Safe to re-run conversion after errors or interruptions
- Enables incremental processing (add new files without reprocessing old)
- Reduces wasted computation time
- Preserves existing outputs (no accidental overwrites)

---

## Troubleshooting

### Common Issues

#### "No files discovered. Run a scan first."

**Cause:** Cache file `data/files.csv` doesn't exist or is empty

**Solution:**
```bash
# Run scan in TUI (Screen 1) or CLI
uv run python excel_to_parquet.py /data -o /output
```

#### "Root directory does not exist"

**Cause:** Provided directory path doesn't exist or has typo

**Solution:**
```bash
# Verify path exists
ls -la /data/projects

# Fix path or create directory
mkdir -p /data/projects
```

#### "Permission denied"

**Cause:** No read permissions on directory or write permissions on output

**Solution:**
```bash
# Check permissions
ls -ld /data/projects /output

# Fix permissions (if you have access)
chmod +r /data/projects
chmod +w /output
```

#### No Excel files found

**Cause:** No files in `/SOV/` paths or wrong directory

**Solution:**
- Verify files are in paths containing `/SOV/` (case-sensitive)
- Check spelling: `/SOV/` not `/sov/` or `/Sov/`
- Use standalone CLI for files outside SOV folders:
  ```bash
  uv run python excel_to_parquet_polars.py /data/*.xlsx -o /output
  ```

#### Cache is stale (missing new files)

**Cause:** Files added after initial scan, cache not updated

**Solution:**
```bash
# Force rescan to rebuild cache
uv run python excel_to_parquet.py /data -o /output --rescan
```

#### Conversion hangs or crashes

**Cause:** Corrupted Excel file or memory exhaustion

**Solution:**
```bash
# Enable debug logging to identify problematic file
uv run python excel_to_parquet.py /data -o /output -l DEBUG

# Review debug.log for errors
grep ERROR debug.log

# Skip corrupted file manually or fix source
```

#### Output files very large

**Cause:** Long format increases row count (N columns × M rows)

**Solution:**
- Expected behavior for normalized format
- Parquet compression helps (typically 30-50% of CSV size)
- Consider filtering during query time instead of at conversion

---

## Contributing

### Development Setup

```bash
# Clone and install with dev dependencies
git clone https://github.com/mmadahar/excel-download.git
cd excel-download
uv sync

# Run tests to verify setup
uv run pytest --cov
```

### Code Style

- **Type hints:** Use for all function parameters and return values
- **Docstrings:** Required for public functions (Google style)
- **Error handling:** Log errors, don't silently fail
- **Naming:** Descriptive names, avoid abbreviations
- **Imports:** Group by standard library, third-party, local

### Test Requirements

New features must include tests:

1. **Follow the pattern:** `Test{FunctionName}{Category}`
   - `HappyPath` - Normal behavior
   - `EdgeCases` - Boundary conditions
   - `ErrorHandling` - Error resilience

2. **Use existing fixtures** from `conftest.py`

3. **Maintain coverage:** Aim for 75%+ coverage on new code

4. **Test isolation:** Use `tmp_path` fixture, never write to permanent locations

### Pull Request Checklist

- [ ] Tests pass: `uv run pytest --cov`
- [ ] Coverage maintained or improved
- [ ] Type hints added for new functions
- [ ] Docstrings added for public APIs
- [ ] CLAUDE.md updated if architecture changed
- [ ] README updated if user-facing changes

---

## License

Not specified.

---

**Project Repository:** [https://github.com/mmadahar/excel-download](https://github.com/mmadahar/excel-download)

**Python Version:** 3.12+

**Last Updated:** 2025-11-27
