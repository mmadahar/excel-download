# CLI Documentation

## Overview

This project provides two complementary CLI tools for converting Excel files to Parquet format:

| Tool | Use Case | Key Features |
|------|----------|--------------|
| `excel_to_parquet.py` | **Directory scanning with caching** | Discovers Excel files, caches file list, filters by SOV folders, skips already-processed files |
| `excel_to_parquet_polars.py` | **Direct file conversion** | Processes explicit file lists, no scanning/caching, simpler standalone operation |

**When to use which tool:**

- **Use `excel_to_parquet.py`** when:
  - You need to scan large directory trees for Excel files
  - You want to cache discovered files for repeated runs
  - You only want to process files in `/SOV/` folders
  - You want idempotent operation (skip already-processed files)
  - You're processing the same directory structure multiple times

- **Use `excel_to_parquet_polars.py`** when:
  - You have a specific list of files to convert
  - You don't need directory scanning or caching
  - You want a simple, standalone converter
  - You're processing files outside of SOV folder structure
  - You want a lightweight tool with minimal dependencies

---

## excel_to_parquet.py (Main CLI)

### Purpose

The main CLI tool that performs directory scanning, file caching, SOV folder filtering, and idempotent Excel-to-Parquet conversion. It discovers Excel files across directory trees, caches the file list in `data/files.csv`, and only processes files in paths containing `/SOV/` (case-sensitive). Already-processed files are automatically skipped by checking existing Parquet outputs.

### Arguments

| Argument | Short | Required | Default | Type | Description |
|----------|-------|----------|---------|------|-------------|
| `root_dirs` | - | Yes | - | positional (1+) | One or more root directories to search for Excel files |
| `--output` | `-o` | Yes | - | string | Output directory for Parquet files |
| `--log-level` | `-l` | No | `INFO` | choice | Logging level: DEBUG, INFO, WARNING, ERROR, CRITICAL |
| `--log-file` | - | No | None | string | Optional log file path (appends to existing file) |
| `--rescan` | `-r` | No | False | flag | Force rescan for Excel files even if `data/files.csv` exists |

### Usage Examples

#### Basic Usage

```bash
# Scan one directory for SOV folders and convert Excel files
uv run python excel_to_parquet.py /data/projects --output /output/parquet
```

#### Multiple Root Directories

```bash
# Scan multiple directories
uv run python excel_to_parquet.py /data/p1 /data/p2 /data/p3 -o /output/parquet
```

#### Debug Logging

```bash
# Enable detailed debug logging to console
uv run python excel_to_parquet.py /data/projects -o /output -l DEBUG
```

#### Log to File

```bash
# Log to file for audit trail
uv run python excel_to_parquet.py /data/projects -o /output --log-file conversion.log
```

#### Force Rescan

```bash
# Force fresh scan even if data/files.csv exists
uv run python excel_to_parquet.py /data/projects -o /output --rescan
```

#### Production Workflow

```bash
# First run: scan and convert
uv run python excel_to_parquet.py /data/projects -o /output -l INFO --log-file conversion.log

# Subsequent runs: use cached file list, skip processed files
uv run python excel_to_parquet.py /data/projects -o /output

# After directory changes: force rescan
uv run python excel_to_parquet.py /data/projects -o /output --rescan
```

### Exit Codes

| Code | Constant | Meaning | Example Causes |
|------|----------|---------|----------------|
| 0 | `EXIT_SUCCESS` | Successful completion | All files processed successfully, or no files found |
| 1 | `EXIT_USER_ERROR` | User input error or interruption | Missing directory, invalid arguments, Ctrl+C interruption |
| 3 | `EXIT_UNEXPECTED_ERROR` | Unhandled exception | Unexpected runtime errors, system failures |

**Note:** Exit code 2 (`EXIT_PROCESSING_ERROR`) is defined but not currently returned by `excel_to_parquet.py`.

### Behavior Details

#### SOV Folder Filtering

- Only processes files in paths containing `/SOV/` (case-sensitive)
- Example valid paths:
  - `/data/projects/2024/SOV/Q1/report.xlsx` ✓
  - `/data/SOV/archive/data.xlsm` ✓
- Example invalid paths:
  - `/data/sov/report.xlsx` ✗ (wrong case)
  - `/data/projects/reports/data.xlsx` ✗ (no SOV folder)

#### Parallel Processing

The tool uses `ThreadPoolExecutor` for parallel file processing:
- SOV folder discovery: parallelized when > 10 branches found
- File conversion: parallelized across all files
- Uses system default thread count (can be customized via `max_workers` parameter in code)

#### Idempotent Operation

Files already present in existing Parquet outputs are automatically skipped:
1. Scans all `*.parquet` files in output directory
2. Extracts unique `file_path` values
3. Skips files already in the processed set
4. Logs skipped files at DEBUG level

---

## excel_to_parquet_polars.py (Standalone)

### Purpose

A standalone Excel-to-Parquet converter that processes explicit file lists without directory scanning, caching, or SOV filtering. This is a simpler, more focused tool for converting specific Excel files to unpivoted long-format Parquet files.

### Arguments

| Argument | Short | Required | Default | Type | Description |
|----------|-------|----------|---------|------|-------------|
| `files` | - | Yes | - | positional (1+) | One or more Excel files to process (.xlsx, .xlsm, .xlsb, .xls) |
| `--output` | `-o` | Yes | - | string | Output directory for Parquet files |
| `--log-level` | `-l` | No | `INFO` | choice | Logging level: DEBUG, INFO, WARNING, ERROR, CRITICAL |
| `--log-file` | - | No | None | string | Optional log file path |

### Usage Examples

#### Single File

```bash
# Convert one Excel file
uv run python excel_to_parquet_polars.py input.xlsx --output /output/parquet
```

#### Multiple Files

```bash
# Convert multiple specific files
uv run python excel_to_parquet_polars.py file1.xlsx file2.xlsm file3.xls -o /output
```

#### Wildcard Expansion

```bash
# Use shell wildcards to select files
uv run python excel_to_parquet_polars.py /data/*.xlsx -o /output

# Multiple wildcards
uv run python excel_to_parquet_polars.py /data/2024/*.xlsx /data/2025/*.xlsm -o /output
```

#### Debug Mode

```bash
# Enable debug logging for troubleshooting
uv run python excel_to_parquet_polars.py input.xlsx -o /output -l DEBUG
```

#### With Log File

```bash
# Log to file
uv run python excel_to_parquet_polars.py file1.xlsx file2.xlsx -o /output --log-file conversion.log
```

#### Mixed Formats

```bash
# Convert different Excel formats together
uv run python excel_to_parquet_polars.py \
  legacy.xls \
  modern.xlsx \
  macro.xlsm \
  binary.xlsb \
  -o /output
```

### Exit Codes

| Code | Constant | Meaning | Example Causes |
|------|----------|---------|----------------|
| 0 | `EXIT_SUCCESS` | Successful completion | All files processed without errors |
| 1 | `EXIT_USER_ERROR` | User input error or interruption | File not found, not a file, Ctrl+C interruption |
| 2 | `EXIT_PROCESSING_ERROR` | Processing errors occurred | Some sheets failed to process, but not fatal |
| 3 | `EXIT_UNEXPECTED_ERROR` | Unhandled exception | Unexpected runtime errors |

### Behavior Details

#### No Caching

Unlike `excel_to_parquet.py`, this tool does NOT:
- Create or use `data/files.csv` cache
- Skip already-processed files
- Filter by SOV folders
- Support `--rescan` flag

Every run processes all specified files from scratch.

#### Sequential Processing

Files are processed sequentially (not parallelized) for simpler, more predictable behavior.

---

## Comparison Table

| Feature | excel_to_parquet.py | excel_to_parquet_polars.py |
|---------|---------------------|----------------------------|
| **Input Method** | Directory scanning | Explicit file list |
| **Caching** | Yes (`data/files.csv`) | No |
| **SOV Filtering** | Yes (only `/SOV/` paths) | No (all files) |
| **Idempotent** | Yes (skips processed) | No (always processes) |
| **Parallel Processing** | Yes (ThreadPoolExecutor) | No (sequential) |
| **Rescan Flag** | Yes (`--rescan`) | N/A |
| **Complexity** | Higher (multi-phase) | Lower (single-pass) |
| **Best For** | Large directory trees | Specific file lists |
| **Output Schema** | Same (long format) | Same (long format) |
| **Exit Codes** | 0, 1, 3 | 0, 1, 2, 3 |
| **Engine Selection** | Automatic by extension | Automatic by extension |

---

## Configuration Details

### Caching (`excel_to_parquet.py` only)

#### How Caching Works

1. **First Run (no cache exists)**:
   ```bash
   uv run python excel_to_parquet.py /data/projects -o /output
   ```
   - Scans all directories for Excel files
   - Creates `data/files.csv` with discovered files
   - Converts files to Parquet

2. **Subsequent Runs (cache exists)**:
   ```bash
   uv run python excel_to_parquet.py /data/projects -o /output
   ```
   - Loads file list from `data/files.csv`
   - Skips directory scanning
   - Checks for already-processed files
   - Converts only new/unprocessed files

3. **Force Rescan (invalidate cache)**:
   ```bash
   uv run python excel_to_parquet.py /data/projects -o /output --rescan
   ```
   - Ignores existing `data/files.csv`
   - Performs fresh directory scan
   - Overwrites cache with new results
   - Processes all files (including already-processed)

#### Cache File Format

`data/files.csv` contains:
```csv
file_path,extension,discovered_at
/data/projects/SOV/file1.xlsx,.xlsx,2025-11-27T10:30:00
/data/projects/SOV/file2.xlsm,.xlsm,2025-11-27T10:30:00
```

**Columns:**
- `file_path`: Absolute path to Excel file
- `extension`: Lowercase file extension (`.xlsx`, `.xlsm`, `.xlsb`, `.xls`)
- `discovered_at`: ISO 8601 timestamp of discovery

#### When to Use `--rescan`

Use the `--rescan` flag when:
- New Excel files have been added to the directory tree
- Files have been moved or renamed
- You suspect the cache is stale or corrupted
- You want to force reprocessing of all files

**Example:**
```bash
# Initial scan
uv run python excel_to_parquet.py /data/projects -o /output

# ... time passes, new files added ...

# Force rescan to discover new files
uv run python excel_to_parquet.py /data/projects -o /output --rescan
```

### Logging

Both tools support flexible logging configuration with identical syntax.

#### Log Levels

| Level | When to Use | Example Output |
|-------|-------------|----------------|
| `DEBUG` | Detailed troubleshooting, file-by-file progress | `DEBUG - Processing sheet 'Sheet1' with shape (100, 5)` |
| `INFO` | Normal operation, high-level progress | `INFO - Processing 15 file(s) in parallel` |
| `WARNING` | Recoverable issues, skipped files | `WARNING - Skipping empty sheet 'Sheet2'` |
| `ERROR` | Processing failures, invalid inputs | `ERROR - Error reading /data/corrupt.xlsx: ...` |
| `CRITICAL` | Not used by these tools | N/A |

#### Console Logging

Always enabled by default to stdout:

```bash
# Info level (default)
uv run python excel_to_parquet.py /data -o /output

# Debug level for troubleshooting
uv run python excel_to_parquet.py /data -o /output -l DEBUG

# Quiet mode (errors only)
uv run python excel_to_parquet.py /data -o /output -l ERROR
```

#### File Logging

Optional append-mode logging to file:

```bash
# Log to file in addition to console
uv run python excel_to_parquet.py /data -o /output --log-file conversion.log

# Multiple runs append to same log
uv run python excel_to_parquet.py /data -o /output --log-file conversion.log  # First run
uv run python excel_to_parquet.py /data -o /output --log-file conversion.log  # Appends
```

#### Log Format

Both console and file use the same format:
```
2025-11-27 10:30:00 - __main__ - INFO - Starting Excel-to-Parquet conversion
2025-11-27 10:30:01 - __main__ - INFO - Found 15 Excel file(s)
2025-11-27 10:30:05 - __main__ - WARNING - Skipping empty sheet 'Sheet2'
```

**Format:** `{timestamp} - {logger_name} - {level} - {message}`

#### Logging Best Practices

```bash
# Production: log to file with INFO level
uv run python excel_to_parquet.py /data -o /output --log-file prod.log

# Development: debug to console only
uv run python excel_to_parquet.py /data -o /output -l DEBUG

# Automated scripts: errors only, log to file
uv run python excel_to_parquet.py /data -o /output -l ERROR --log-file errors.log

# Troubleshooting: verbose debug to both console and file
uv run python excel_to_parquet.py /data -o /output -l DEBUG --log-file debug.log
```

### Engine Selection

Both tools automatically select the appropriate Excel reading engine based on file extension. This is handled transparently by the `get_engine_for_extension()` function.

#### Engine Mapping

| Extension | Engine | Description | Python Package |
|-----------|--------|-------------|----------------|
| `.xlsx` | `openpyxl` | Modern XML-based Excel format (Excel 2007+) | `openpyxl` |
| `.xlsm` | `openpyxl` | Macro-enabled workbook format | `openpyxl` |
| `.xlsb` | `pyxlsb` (main) / `calamine` (standalone) | Binary workbook format (faster, smaller) | `pyxlsb` or `calamine` |
| `.xls` | `xlrd` (main) / `calamine` (standalone) | Legacy Excel format (Excel 97-2003) | `xlrd` or `calamine` |

#### Differences Between Tools

**excel_to_parquet.py:**
```python
engine_map = {
    ".xlsx": "openpyxl",
    ".xlsm": "openpyxl",
    ".xlsb": "pyxlsb",   # Uses pyxlsb
    ".xls": "xlrd",       # Uses xlrd
}
```

**excel_to_parquet_polars.py:**
```python
engine_map = {
    '.xlsx': 'openpyxl',
    '.xlsm': 'openpyxl',
    '.xlsb': 'calamine',   # Uses calamine (Rust-based)
    '.xls': 'calamine',    # Uses calamine
}
```

#### Engine Selection Process

1. Extract file extension using `Path.suffix.lower()` (case-insensitive)
2. Look up engine in mapping dictionary
3. Pass engine to `pl.read_excel(engine=...)`
4. Fall back to default engine if extension not recognized

**Example:**
```python
# File: /data/report.XLSX
# Extension: .xlsx (lowercased from .XLSX)
# Engine: openpyxl
```

#### Engine Capabilities

| Engine | Speed | Format Support | Special Features |
|--------|-------|----------------|------------------|
| `openpyxl` | Moderate | .xlsx, .xlsm | Full feature support, actively maintained |
| `pyxlsb` | Fast | .xlsb | Binary format support, memory efficient |
| `calamine` | Fast | .xlsx, .xls, .xlsb | Rust-based, cross-format support |
| `xlrd` | Moderate | .xls | Legacy format only, no longer updated |

#### Troubleshooting Engine Issues

If you encounter engine-related errors:

1. **Check package installation:**
   ```bash
   uv run python -c "import openpyxl; import pyxlsb; import xlrd"
   ```

2. **Install missing engines:**
   ```bash
   uv add openpyxl pyxlsb xlrd
   ```

3. **Check file extension:**
   ```bash
   # Verify actual file type matches extension
   file /data/report.xlsx
   ```

4. **Enable debug logging:**
   ```bash
   uv run python excel_to_parquet.py /data -o /output -l DEBUG
   # Look for: "Selected engine 'openpyxl' for extension '.xlsx'"
   ```

---

## Common Workflows

### Workflow 1: Initial Directory Scan

```bash
# Step 1: Scan directory and cache results
uv run python excel_to_parquet.py /data/projects -o /output/parquet --log-file initial_scan.log

# Step 2: Verify cache was created
cat data/files.csv

# Step 3: Check output
ls -lh /output/parquet/*.parquet
```

### Workflow 2: Incremental Processing

```bash
# Day 1: Initial conversion
uv run python excel_to_parquet.py /data/projects -o /output

# Day 2: Only new files processed (uses cache, skips existing)
uv run python excel_to_parquet.py /data/projects -o /output

# Day 3: Force rescan after directory changes
uv run python excel_to_parquet.py /data/projects -o /output --rescan
```

### Workflow 3: Specific File Conversion

```bash
# Convert only specific files (no scanning/caching)
uv run python excel_to_parquet_polars.py \
  /data/projects/2024/report1.xlsx \
  /data/projects/2024/report2.xlsx \
  -o /output/specific
```

### Workflow 4: Troubleshooting

```bash
# Enable verbose logging
uv run python excel_to_parquet.py /data/projects -o /output -l DEBUG --log-file debug.log

# Review log for errors
grep ERROR debug.log

# Check which files were skipped
grep "Skipping" debug.log
```

### Workflow 5: Production Batch Processing

```bash
#!/bin/bash
# production_convert.sh

LOG_DIR="/logs/conversion"
OUTPUT_DIR="/output/parquet"
DATA_DIR="/data/projects"

mkdir -p "$LOG_DIR" "$OUTPUT_DIR"

# Run conversion with timestamp
TIMESTAMP=$(date +%Y%m%d_%H%M%S)
LOG_FILE="$LOG_DIR/conversion_$TIMESTAMP.log"

uv run python excel_to_parquet.py \
  "$DATA_DIR" \
  -o "$OUTPUT_DIR" \
  -l INFO \
  --log-file "$LOG_FILE"

# Check exit code
if [ $? -eq 0 ]; then
  echo "Conversion successful" | tee -a "$LOG_FILE"
else
  echo "Conversion failed - check $LOG_FILE" >&2
  exit 1
fi
```

---

## Output Schema

Both tools produce identical output schema in long format.

### Schema Definition

All Parquet files contain these columns:

| Column | Type | Description | Example |
|--------|------|-------------|---------|
| `file_path` | `str` | Absolute path to source Excel file | `/data/projects/SOV/2024/report.xlsx` |
| `file_name` | `str` | Basename of Excel file | `report.xlsx` |
| `worksheet` | `str` | Name of the worksheet | `Sheet1` |
| `row` | `int` | 0-indexed row number in original sheet | `0`, `1`, `2`, ... |
| `column` | `int` | Column number as integer (main CLI) or string (standalone) | `1`, `2`, `3`, ... |
| `value` | `str` | Cell value cast to string | `"Total"`, `"123.45"`, `""` |

### Wide to Long Transformation

**Input (Excel - wide format):**
```
     A        B        C
1    Name     Age      City
2    Alice    25       NYC
3    Bob      30       LA
```

**Output (Parquet - long format):**
```
file_path                    file_name   worksheet  row  column  value
/data/report.xlsx            report.xlsx Sheet1     0    1       Name
/data/report.xlsx            report.xlsx Sheet1     0    2       Age
/data/report.xlsx            report.xlsx Sheet1     0    3       City
/data/report.xlsx            report.xlsx Sheet1     1    1       Alice
/data/report.xlsx            report.xlsx Sheet1     1    2       25
/data/report.xlsx            report.xlsx Sheet1     2    3       NYC
...
```

**Note:** Both tools use `has_header=False`, treating the first row as data, not column names. Columns are auto-named as `column_1`, `column_2`, etc.

### UUID Filenames

Both tools generate UUID-based filenames to prevent collisions:

```
/output/parquet/
├── 3f8c9a2b-1234-5678-90ab-cdef12345678.parquet  # Sheet1 from file1.xlsx
├── 7a2b3c4d-5678-90ab-cdef-123456789abc.parquet  # Sheet2 from file1.xlsx
└── 9d8e7f6c-90ab-cdef-1234-56789abcdef0.parquet  # Sheet1 from file2.xlsx
```

This ensures:
- No filename conflicts across sheets or files
- Each sheet gets its own Parquet file
- Deterministic processing (same file always generates new UUID)

---

## Error Handling

### Common Errors and Solutions

#### Error: "Root directory does not exist"

```bash
ERROR - Root directory does not exist: /data/missing
```

**Solution:** Verify the directory path exists:
```bash
ls -la /data/missing
# Fix the path or create the directory
mkdir -p /data/missing
```

#### Error: "File not found"

```bash
ERROR - File not found: /data/report.xlsx
```

**Solution:** Check file path and permissions:
```bash
ls -l /data/report.xlsx
# Ensure file exists and is readable
```

#### Error: "Permission denied"

```bash
WARNING - Permission denied accessing /restricted/data
```

**Solution:** Check directory permissions:
```bash
# View permissions
ls -ld /restricted/data

# Fix permissions (if you have sudo)
sudo chmod +r /restricted/data
```

#### Error: "Could not load processed file paths"

```bash
DEBUG - Could not load processed file paths: ...
```

**Meaning:** No existing Parquet files in output directory (not an error on first run).

**Solution:** This is normal on first run. Ignore unless recurring.

#### Error: "Error reading CSV file"

```bash
WARNING - Error reading CSV file: ... Performing fresh scan.
```

**Solution:** Cache file is corrupted. Tool automatically rescans. To prevent:
```bash
# Force clean rescan
rm data/files.csv
uv run python excel_to_parquet.py /data -o /output
```

### Validation Failures

Both tools validate inputs before processing:

```bash
# Invalid directory
uv run python excel_to_parquet.py /nonexistent -o /output
# Returns: EXIT_USER_ERROR (1)

# Invalid file
uv run python excel_to_parquet_polars.py /nonexistent.xlsx -o /output
# Returns: EXIT_USER_ERROR (1)

# Not writable output
uv run python excel_to_parquet.py /data -o /readonly
# Returns: EXIT_USER_ERROR (1)
```

---

## Performance Considerations

### Directory Scanning Performance

`excel_to_parquet.py` uses adaptive parallelization:

- **Small trees (< 10 branches):** Sequential traversal
- **Large trees (≥ 10 branches):** Parallel traversal with ThreadPoolExecutor

**Tuning:**
```python
# In code: adjust min_parallel_branches
sov_folders = find_sov_folders(
    root_dirs,
    min_parallel_branches=20,  # Higher = more sequential work before parallelizing
    max_workers=8              # Limit thread count
)
```

### File Processing Performance

`excel_to_parquet.py` processes files in parallel:
- Uses `ThreadPoolExecutor` for concurrent file processing
- Default: system-determined thread count
- I/O-bound operations benefit from threading

**Memory usage:** Proportional to file size × number of parallel workers

### Caching Performance

First run vs. cached run:

```bash
# First run: ~30 seconds (scan 10,000 files)
uv run python excel_to_parquet.py /large/tree -o /output

# Cached run: ~1 second (load CSV)
uv run python excel_to_parquet.py /large/tree -o /output
```

**Performance tip:** Use `--rescan` sparingly to maximize cache benefits.

---

## Version History

**Note:** This documentation reflects the current implementation. Key design decisions:

- **No headers:** `has_header=False` treats first row as data
- **Long format:** All sheets unpivoted to normalized schema
- **SOV filtering:** Main CLI only processes `/SOV/` paths
- **Idempotent:** Main CLI skips already-processed files
- **UUID naming:** Prevents output collisions

---

## Related Documentation

- Main README: `/Users/matthew/Python/excel-download/README.md`
- TUI Guide: `/Users/matthew/Python/excel-download/TUI_GUIDE.md`
- Project Instructions: `/Users/matthew/Python/excel-download/CLAUDE.md`
- Test Organization: `/Users/matthew/Python/excel-download/tests/`

---

## Quick Reference

### excel_to_parquet.py

```bash
# Basic
uv run python excel_to_parquet.py <root_dirs...> -o <output>

# Common flags
--rescan, -r         Force rescan
--log-level, -l      DEBUG|INFO|WARNING|ERROR
--log-file           Log file path
```

### excel_to_parquet_polars.py

```bash
# Basic
uv run python excel_to_parquet_polars.py <files...> -o <output>

# Common flags
--log-level, -l      DEBUG|INFO|WARNING|ERROR
--log-file           Log file path
```

### Exit Codes

- 0: Success
- 1: User error / interruption
- 2: Processing error (standalone only)
- 3: Unexpected error
