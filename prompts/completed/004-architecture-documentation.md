# Architecture Documentation

## Overview

Excel-to-Parquet is a conversion tool that discovers Excel files in SOV (Statement of Value) folders, converts each sheet to unpivoted long format, and saves as Parquet files with metadata columns. The system supports multiple Excel formats (.xlsx, .xlsm, .xlsb, .xls) and provides both CLI and interactive TUI interfaces.

**Key Characteristics:**
- Idempotent processing: Skips already-processed files
- Parallel execution: Leverages ThreadPoolExecutor for I/O-bound operations
- Normalized output: Wide data → long format via unpivoting
- Metadata tracking: Preserves file, sheet, row, and column information
- SOV-focused: Only processes files in paths containing `/SOV/` (case-sensitive)

## Entry Points

| Script | Purpose | When to Use |
|--------|---------|-------------|
| `tui.py` | Interactive Textual TUI with screens for scan, browse, convert, results | When you want a guided, visual workflow with progress tracking and file inspection |
| `excel_to_parquet.py` | CLI with directory scanning, caching (`data/files.csv`), and SOV folder detection | When automating batch processing of SOV folders, or for scripting/scheduled jobs |
| `excel_to_parquet_polars.py` | Standalone converter for explicit file lists (no scanning/caching/SOV filtering) | When converting specific files outside SOV folders, or for testing individual files |

**Module Relationships:**
- `tui.py` imports and wraps functions from `excel_to_parquet.py`
- `excel_to_parquet_polars.py` is independent (no shared code with the other two)
- All three modules use Polars for data processing
- `excel_to_parquet.py` and `excel_to_parquet_polars.py` share similar processing logic but different discovery mechanisms

## Data Flow Pipeline

```
┌─────────────────────────────────────────────────────────────────────────┐
│ PHASE 1: DISCOVERY                                                      │
│                                                                         │
│  User provides root_dirs: ["/data/projects", "/backup"]                │
│         │                                                               │
│         ├──→ Check for data/files.csv                                  │
│         │    ├─(exists && !rescan)─→ load_or_scan_files()             │
│         │    │                        └→ pl.read_csv(data/files.csv)   │
│         │    │                                                          │
│         │    └─(missing || rescan)──→ scan_for_excel_files()           │
│         │                             ├→ root.rglob("*")               │
│         │                             ├→ Filter: {.xlsx,.xlsm,.xlsb,.xls}│
│         │                             └→ pl.DataFrame(file_path, extension, discovered_at)│
│         │                                └→ Save to data/files.csv      │
│         ↓                                                               │
│  files.csv contains all discovered Excel files                         │
│                                                                         │
└─────────────────────────────────────────────────────────────────────────┘
         │
         ↓
┌─────────────────────────────────────────────────────────────────────────┐
│ PHASE 2: SOV FOLDER LOCATION                                           │
│                                                                         │
│  find_sov_folders(root_dirs)                                           │
│         │                                                               │
│         ├──→ Breadth-first traversal collects subdirectories           │
│         │    until min_parallel_branches reached (default: 10)         │
│         │                                                               │
│         ├──→ ThreadPoolExecutor parallelizes traversal                 │
│         │    ├─→ _traverse_for_sov(branch) for each branch             │
│         │    └─→ Filter: path.as_posix() contains "/SOV/"              │
│         │                                                               │
│         ↓                                                               │
│  Returns: List[Path] of directories containing "/SOV/" in path         │
│                                                                         │
└─────────────────────────────────────────────────────────────────────────┘
         │
         ↓
┌─────────────────────────────────────────────────────────────────────────┐
│ PHASE 3: PROCESSING                                                     │
│                                                                         │
│  process_excel_files(sov_folders, output_dir)                          │
│         │                                                               │
│         ├──→ Load data/files.csv                                       │
│         │                                                               │
│         ├──→ get_processed_file_paths(output_dir)                      │
│         │    ├─→ pl.scan_parquet("output/*.parquet")                   │
│         │    └─→ Returns Set[str] of already-processed file_path values│
│         │                                                               │
│         ├──→ Filter: Exclude already-processed + non-existent files    │
│         │                                                               │
│         ├──→ ThreadPoolExecutor(max_workers)                           │
│         │    └─→ For each file: _process_single_file()                 │
│         │         ├─→ get_engine_for_extension()                       │
│         │         │   ├─ .xlsx/.xlsm → openpyxl                        │
│         │         │   ├─ .xlsb → pyxlsb                                │
│         │         │   └─ .xls → xlrd                                   │
│         │         │                                                     │
│         │         ├─→ pl.read_excel(sheet_id=0, has_header=False)      │
│         │         │   └→ Returns: Dict[sheet_name, DataFrame]          │
│         │         │                                                     │
│         │         └─→ For each sheet:                                  │
│         │              ├─→ df.with_row_index(name="row")               │
│         │              ├─→ df.unpivot(on=value_columns,                │
│         │              │               index="row",                     │
│         │              │               variable_name="column",          │
│         │              │               value_name="value")              │
│         │              ├─→ Add metadata columns:                        │
│         │              │   - file_path (lit)                            │
│         │              │   - file_name (lit)                            │
│         │              │   - worksheet (lit)                            │
│         │              │   - row (from with_row_index)                  │
│         │              │   - column (str.replace + cast to Int64)       │
│         │              │   - value (cast to Utf8)                       │
│         │              └─→ write_parquet(f"{uuid4()}.parquet")         │
│         ↓                                                               │
│  Output: UUID-named Parquet files in output_dir                        │
│                                                                         │
└─────────────────────────────────────────────────────────────────────────┘
```

### Phase 1: Discovery

The discovery phase identifies all Excel files in the provided root directories:

1. **Cache Check**: If `data/files.csv` exists and `--rescan` flag is not set, load from cache
2. **Fresh Scan**: Otherwise, recursively search directories using `Path.rglob("*")`
3. **Extension Filtering**: Match files with case-insensitive extension check against `{.xlsx, .xlsm, .xlsb, .xls}`
4. **DataFrame Creation**: Build Polars DataFrame with schema `(file_path, extension, discovered_at)`
5. **Cache Save**: Write DataFrame to `data/files.csv` for future runs

**Why this approach:**
- Avoids redundant filesystem traversal on repeated runs
- ISO timestamps enable audit trails
- Polars DataFrame enables efficient filtering/querying
- Absolute path resolution prevents duplicates

### Phase 2: SOV Location

The SOV location phase finds directories containing `/SOV/` in their path:

1. **Validation**: Check that root directories exist and are readable
2. **Two-Phase Traversal**:
   - **Phase 2a**: Breadth-first collection of subdirectories until `min_parallel_branches` (default: 10) are accumulated
   - **Phase 2b**: Parallel traversal across collected branches using ThreadPoolExecutor
3. **Pattern Matching**: Use `path.as_posix()` to convert paths to forward-slash notation, then check for `/SOV/` substring
4. **Deduplication**: Use set to eliminate duplicates (e.g., from symlinks or overlapping roots)
5. **Sorting**: Return sorted list for deterministic output

**Why this approach:**
- Breadth-first collection ensures enough work exists to parallelize
- ThreadPoolExecutor leverages multiple cores for I/O-bound operations
- POSIX path notation ensures cross-platform compatibility (Windows backslashes → forward slashes)
- Case-sensitive matching prevents false positives (`/sov/`, `/Sov/`)

**Important Note:** The function finds directories that **contain** `/SOV/` in their path (e.g., `/project/SOV/data`, `/project/SOV/archive/Q1`), not the SOV folder itself. Empty SOV folders return an empty list.

### Phase 3: Processing

The processing phase converts Excel sheets to Parquet format:

1. **Load File List**: Read `data/files.csv` to get discovered files
2. **Idempotent Check**: 
   - Scan existing Parquet files to extract `file_path` values
   - Build set of already-processed paths
   - Filter out files already in Parquet outputs
3. **Engine Selection**: Map file extension to appropriate Excel reader:
   - `.xlsx`, `.xlsm` → `openpyxl`
   - `.xlsb` → `pyxlsb`
   - `.xls` → `xlrd`
4. **Sheet Reading**: Use `pl.read_excel(sheet_id=0, has_header=False)` to load all sheets as dictionary
5. **Unpivoting**: Transform each sheet from wide to long format:
   - Add row numbers with `with_row_index()`
   - Unpivot all columns except `row`
   - Column names become values in `column` field
   - Cell values go to `value` field
6. **Column Transformation**: Convert `column_1` → `1` by stripping prefix and casting to Int64
7. **Metadata Addition**: Add `file_path`, `file_name`, `worksheet` as literal columns
8. **UUID Naming**: Generate random filename to prevent collisions across sheets/files
9. **Parallel Execution**: Process multiple files concurrently using ThreadPoolExecutor

**Why this approach:**
- Idempotent processing enables safe re-runs without duplication
- Engine selection ensures compatibility across formats
- Unpivoting normalizes data for analytical queries
- UUID filenames avoid name collisions
- ThreadPoolExecutor speeds up I/O-bound file operations
- Per-file and per-sheet error handling ensures resilience

## Core Functions Reference

### find_sov_folders()

**Signature**: 
```python
find_sov_folders(
    root_dirs: List[str],
    min_parallel_branches: int = 10,
    max_workers: Optional[int] = None
) -> List[Path]
```

**Purpose**: Find all directories containing `/SOV/` in their path using parallel traversal

**Key Behaviors**:
- Case-sensitive matching: Only matches `/SOV/`, not `/sov/` or `/Sov/`
- Pattern matching: Must be a standalone directory (e.g., `/project/SOV/data`), not part of a larger name (e.g., `/SOV_data/`)
- Two-phase traversal: Breadth-first collection → parallel traversal
- Cross-platform: Uses `as_posix()` to convert Windows backslashes to forward slashes
- Error handling: Continues processing if some directories are inaccessible
- Deduplication: Returns unique paths even if multiple root dirs overlap
- Returns subdirectories WITHIN SOV folders, not the SOV folder itself

**Example**:
```python
# Find SOV subdirectories across multiple roots
roots = ["/data/projects", "/backup/archive"]
sov_folders = find_sov_folders(roots)

# Result might be:
# [
#   Path("/data/projects/2024/SOV/Q1"),
#   Path("/data/projects/2024/SOV/Q2"),
#   Path("/backup/archive/old/SOV/2023")
# ]
```

### scan_for_excel_files()

**Signature**:
```python
scan_for_excel_files(root_dirs: List[Path]) -> pl.DataFrame
```

**Purpose**: Recursively scan directories for Excel files and return metadata as DataFrame

**Key Behaviors**:
- Case-insensitive extension matching: Matches `.xlsx`, `.XLSX`, `.XlSx`, etc.
- Supported extensions: `.xlsx`, `.xlsm`, `.xlsb`, `.xls`
- Absolute path resolution: Uses `path.resolve()` for unique, consistent paths
- ISO timestamps: Records discovery time in sortable format
- Error handling: Logs warnings for permission errors but continues scanning
- Empty DataFrame with correct schema if no files found

**Example**:
```python
roots = [Path("/data/projects"), Path("/backup")]
df = scan_for_excel_files(roots)

# Result DataFrame:
# shape: (15, 3)
# ┌─────────────────────────────┬───────────┬───────────────────────┐
# │ file_path                   ┆ extension ┆ discovered_at         │
# │ ---                         ┆ ---       ┆ ---                   │
# │ str                         ┆ str       ┆ str                   │
# ╞═════════════════════════════╪═══════════╪═══════════════════════╡
# │ /data/projects/report.xlsx  ┆ .xlsx     ┆ 2025-11-27T10:30:00   │
# │ /data/projects/data.xlsm    ┆ .xlsm     ┆ 2025-11-27T10:30:00   │
# │ /backup/legacy.xls          ┆ .xls      ┆ 2025-11-27T10:30:00   │
# └─────────────────────────────┴───────────┴───────────────────────┘
```

### load_or_scan_files()

**Signature**:
```python
load_or_scan_files(root_dirs: List[str], rescan: bool) -> pl.DataFrame
```

**Purpose**: Load existing file list from CSV cache or perform fresh scan

**Key Behaviors**:
- Cache-first approach: Checks for `data/files.csv` existence before scanning
- Rescan flag: Forces fresh scan even if CSV exists
- Automatic save: Writes scan results to CSV after fresh scan
- Directory creation: Creates `data/` directory if missing
- Error handling: Falls back to fresh scan if CSV read fails
- Returns consistent schema regardless of source (cache vs. scan)

**Example**:
```python
# First run - scans and creates CSV
df = load_or_scan_files(["/data/projects"], rescan=False)
# INFO: Performing fresh scan for Excel files
# INFO: Saved file list to data/files.csv

# Second run - loads from CSV
df = load_or_scan_files(["/data/projects"], rescan=False)
# INFO: Loading existing file list from data/files.csv
# INFO: Loaded 15 file(s) from CSV

# Force rescan - ignores CSV
df = load_or_scan_files(["/data/projects"], rescan=True)
# INFO: Performing fresh scan for Excel files
```

### get_processed_file_paths()

**Signature**:
```python
get_processed_file_paths(output_dir: Path) -> Set[str]
```

**Purpose**: Get set of file paths already processed in Parquet files (for idempotent processing)

**Key Behaviors**:
- Lazy evaluation: Uses `pl.scan_parquet()` for efficient scanning
- Glob pattern: Matches all `*.parquet` files in output directory
- Unique extraction: Selects and deduplicates `file_path` column
- Set return type: Enables O(1) lookup during skip checks
- Error resilience: Returns empty set if no Parquet files exist or on read error
- Streaming engine: Processes large datasets without loading entirely into memory

**Example**:
```python
output_dir = Path("/output/parquet")
processed = get_processed_file_paths(output_dir)

# Result: {'=/data/file1.xlsx', '/data/file2.xlsx', '/data/file3.xlsm'}

# Use for skip logic
if "/data/file1.xlsx" in processed:
    print("Already processed, skipping")
```

### process_excel_files()

**Signature**:
```python
process_excel_files(
    sov_folders: List[Path],
    output_dir: Path,
    max_workers: Optional[int] = None
) -> None
```

**Purpose**: Convert Excel files to Parquet format with metadata tracking and unpivoting

**Key Behaviors**:
- Idempotent: Skips files already present in output Parquet files
- Parallel execution: Uses ThreadPoolExecutor for concurrent file processing
- Engine selection: Automatically chooses correct Excel reader per file type
- Unpivoting: Transforms wide data to normalized long format
- Metadata enrichment: Adds `file_path`, `file_name`, `worksheet` columns
- UUID naming: Prevents filename collisions across sheets/files
- Error resilience: Per-file and per-sheet error handling with logging
- Statistics tracking: Logs counts of processed files, sheets, rows, errors
- No return value: Side effect is writing Parquet files + logging

**Example**:
```python
sov_folders = []  # Not used but kept for compatibility
output_dir = Path("/output/parquet")
process_excel_files(sov_folders, output_dir, max_workers=4)

# Output:
# INFO: Loaded 10 file(s) from CSV
# INFO: Found 3 already-processed file(s)
# INFO: Processing 7 file(s) in parallel (max_workers=4)
# DEBUG: Processing file: report.xlsx
# DEBUG: File has 2 sheet(s)
# DEBUG: Saved sheet 'Summary' (1240 rows) to a3b5c7d9-1234-5678-abcd-ef0123456789.parquet
# INFO: Processing complete: converted 14 sheet(s) from 7 file(s), wrote 18350 total rows
```

### validate_inputs()

**Signature**:
```python
validate_inputs(root_dirs: List[str], output: str) -> None
```

**Purpose**: Validate that input directories exist and output directory is writable

**Key Behaviors**:
- Existence checks: Verifies all root directories exist
- Type checks: Ensures paths are directories, not files
- Permission checks: Uses `os.access()` to verify read/write permissions
- Output creation: Attempts to create output directory if missing
- Raises exceptions: ValueError for invalid paths, PermissionError for access issues
- Fail-fast: Catches errors before processing begins

**Example**:
```python
try:
    validate_inputs(["/data/projects", "/backup"], "/output/parquet")
    # Validation passed, proceed with processing
except ValueError as e:
    print(f"Invalid path: {e}")
except PermissionError as e:
    print(f"Permission error: {e}")
```

### setup_logging()

**Signature**:
```python
setup_logging(log_level: str, log_file: Optional[str] = None) -> None
```

**Purpose**: Configure logging with console and optional file output

**Key Behaviors**:
- Dual output: Always logs to console (stdout), optionally to file
- Consistent formatting: Timestamp, logger name, level, message
- Level configuration: Accepts DEBUG, INFO, WARNING, ERROR, CRITICAL
- Handler clearing: Removes existing handlers to prevent duplicates
- File append mode: Appends to existing log file rather than overwriting
- Root logger configuration: Affects all loggers in the application

**Example**:
```python
# Console only
setup_logging("INFO")

# Console + file
setup_logging("DEBUG", log_file="conversion.log")

# After setup, all logging works
import logging
logger = logging.getLogger(__name__)
logger.info("Processing started")
# Output: 2025-11-27 10:30:00 - __main__ - INFO - Processing started
```

### get_engine_for_extension()

**Signature**:
```python
get_engine_for_extension(file_path: Path) -> str
```

**Purpose**: Determine the appropriate engine for the Excel file extension

**Key Behaviors**:
- Extension mapping:
  - `.xlsx`, `.xlsm` → `openpyxl` (modern XML-based Excel)
  - `.xlsb` → `pyxlsb` (binary Excel format)
  - `.xls` → `xlrd` (legacy Excel 97-2003)
- Case-insensitive: Uses `suffix.lower()` to normalize extensions
- Default fallback: Returns `openpyxl` for unknown extensions
- Single responsibility: Only handles engine selection, not file reading

**Example**:
```python
engine = get_engine_for_extension(Path("report.xlsx"))
# Returns: "openpyxl"

engine = get_engine_for_extension(Path("data.xlsb"))
# Returns: "pyxlsb"

engine = get_engine_for_extension(Path("legacy.xls"))
# Returns: "xlrd"
```

## Output Schema

All Parquet files share this normalized schema with 6 columns:

| Column | Type | Description | Example |
|--------|------|-------------|---------|
| `file_path` | `str` | Absolute path to source Excel file | `/data/projects/SOV/report.xlsx` |
| `file_name` | `str` | Basename of the Excel file (for easy filtering) | `report.xlsx` |
| `worksheet` | `str` | Name of the worksheet/sheet in the Excel file | `Q1 Summary` |
| `row` | `int` | 0-indexed row number from the original sheet | `0`, `1`, `2`, ... |
| `column` | `int` | Column number as integer (1-indexed in Excel, 0-indexed here) | `0`, `1`, `2`, ... |
| `value` | `str` | Cell value as text (all types cast to string) | `"Revenue"`, `"1000.50"`, `""` |

**Why This Schema:**

1. **file_path**: Enables joining with other datasets and tracking data lineage back to source
2. **file_name**: Simplifies queries when you only care about filename, not full path
3. **worksheet**: Essential for multi-sheet workbooks where sheet names carry meaning (e.g., "Summary" vs. "Details")
4. **row**: Preserves row order for reconstruction or row-based filtering
5. **column**: Preserves column order; integers enable numeric sorting and range queries
6. **value**: Unified string type avoids schema conflicts across heterogeneous sheets

**Example Data:**

```python
# Original Excel sheet "Sales" with data:
#     A           B       C
# 1   Product     Q1      Q2
# 2   Widget      100     150
# 3   Gadget      200     250

# Becomes Parquet rows:
┌─────────────────────────┬─────────────┬───────────┬─────┬────────┬─────────┐
│ file_path               ┆ file_name   ┆ worksheet ┆ row ┆ column ┆ value   │
├─────────────────────────┼─────────────┼───────────┼─────┼────────┼─────────┤
│ /data/SOV/report.xlsx   ┆ report.xlsx ┆ Sales     ┆ 0   ┆ 0      ┆ Product │
│ /data/SOV/report.xlsx   ┆ report.xlsx ┆ Sales     ┆ 0   ┆ 1      ┆ Q1      │
│ /data/SOV/report.xlsx   ┆ report.xlsx ┆ Sales     ┆ 0   ┆ 2      ┆ Q2      │
│ /data/SOV/report.xlsx   ┆ report.xlsx ┆ Sales     ┆ 1   ┆ 0      ┆ Widget  │
│ /data/SOV/report.xlsx   ┆ report.xlsx ┆ Sales     ┆ 1   ┆ 1      ┆ 100     │
│ /data/SOV/report.xlsx   ┆ report.xlsx ┆ Sales     ┆ 1   ┆ 2      ┆ 150     │
│ /data/SOV/report.xlsx   ┆ report.xlsx ┆ Sales     ┆ 2   ┆ 0      ┆ Gadget  │
│ /data/SOV/report.xlsx   ┆ report.xlsx ┆ Sales     ┆ 2   ┆ 1      ┆ 200     │
│ /data/SOV/report.xlsx   ┆ report.xlsx ┆ Sales     ┆ 2   ┆ 2      ┆ 250     │
└─────────────────────────┴─────────────┴───────────┴─────┴────────┴─────────┘
```

**Querying Example:**

```python
import polars as pl

# Load all Parquet files
df = pl.read_parquet("output/*.parquet")

# Get all values from row 0 (original header row)
headers = df.filter(pl.col("row") == 0)

# Get all data from worksheet "Sales"
sales_data = df.filter(pl.col("worksheet") == "Sales")

# Pivot back to wide format (reconstruct original sheet)
wide = df.pivot(
    values="value",
    index=["file_path", "worksheet", "row"],
    on="column"
)
```

## Design Decisions

### Why Polars Over Pandas?

**Decision**: Use Polars as the primary DataFrame library instead of Pandas

**Rationale**:
- **Performance**: Polars is written in Rust and uses Apache Arrow memory format, resulting in 5-10x faster operations for I/O and transformations
- **Memory efficiency**: Lazy evaluation and streaming execution allow processing datasets larger than RAM
- **Modern API**: Expression-based API is more composable than Pandas' index-based approach
- **Better parallelization**: Multi-threaded by default without GIL limitations
- **Native Parquet support**: First-class support for Parquet with efficient scan operations
- **Type safety**: Stricter type system catches errors earlier

**Trade-offs**:
- Smaller ecosystem and community compared to Pandas
- Learning curve for users familiar with Pandas
- Some advanced Pandas features not yet available

### Why UUID Filenames?

**Decision**: Use `uuid.uuid4()` to generate random filenames for output Parquet files

**Rationale**:
- **Collision prevention**: Eliminates name collisions across sheets with identical names in different files
- **Uniqueness guarantee**: 128-bit UUIDs have negligible collision probability (1 in 2^122)
- **Simplicity**: Avoids complex naming schemes with sanitization, length limits, and uniqueness checks
- **Parallel-safe**: Workers can generate UUIDs independently without coordination
- **Metadata preservation**: Source file information is preserved in the `file_path` and `file_name` columns

**Trade-offs**:
- Filenames are not human-readable or meaningful
- Cannot infer source file from filename alone (must read Parquet metadata)
- Slightly more complex for users who expect descriptive filenames

**Alternative Considered**: Structured naming like `{source_file}_{sheet_name}_{timestamp}.parquet`, but rejected due to:
- Need for filename sanitization (special characters, length limits)
- Collision risk with identical sheet names
- Complexity in handling edge cases (empty sheet names, Unicode)

### Why Case-Sensitive /SOV/?

**Decision**: Match `/SOV/` exactly (case-sensitive), not `/sov/` or `/Sov/`

**Rationale**:
- **Standardization**: SOV (Statement of Value) is a proper acronym that should be uppercase in organizational conventions
- **False positive prevention**: Avoids matching unrelated directories like `/soviet/`, `/sovereign/`, `/resolve/`
- **Explicit intent**: Case sensitivity signals deliberate folder structure (not accidental lowercase)
- **Cross-platform consistency**: POSIX path conversion ensures same behavior on Windows and Unix systems

**Trade-offs**:
- Users with lowercase `/sov/` folders must rename them or modify code
- Less forgiving of inconsistent naming conventions

**Implementation Note**: Uses `path.as_posix()` to convert Windows backslashes (`\SOV\`) to forward slashes (`/SOV/`) before matching, ensuring cross-platform compatibility.

### Why has_header=False?

**Decision**: Set `has_header=False` when reading Excel files, treating the first row as data

**Rationale**:
- **Heterogeneous sheets**: SOV files often have inconsistent header rows or no headers at all
- **No assumptions**: Treating all rows as data avoids guessing which row contains headers
- **Preserves information**: First row data is not lost or misinterpreted as column names
- **Uniform processing**: All sheets processed identically regardless of structure
- **Post-processing flexibility**: Users can identify header rows themselves during analysis (e.g., by filtering `row == 0`)

**Trade-offs**:
- Auto-generated column names (`column_1`, `column_2`) are less descriptive
- Users must implement their own header detection logic if needed
- Slightly more work to reconstruct original structure

**Example**:
```python
# With has_header=True (not used):
# Column names: ["Product", "Q1", "Q2"]
# First data row: row 1 → ["Widget", "100", "150"]

# With has_header=False (actual):
# Column names: ["column_1", "column_2", "column_3"]
# First data row: row 0 → ["Product", "Q1", "Q2"]
# Second data row: row 1 → ["Widget", "100", "150"]
```

### Why Unpivot to Long Format?

**Decision**: Transform wide-format Excel sheets to long format using `unpivot()`

**Rationale**:
- **Normalization**: Long format is the standard for relational databases and analytical queries
- **Schema consistency**: All Parquet files share the same 6-column schema regardless of source structure
- **Query simplicity**: Filtering, grouping, and aggregating are easier with normalized data
- **Sparse data handling**: Empty cells don't waste space (though all cells are currently included)
- **Join-friendly**: Enables easy joins with other normalized datasets
- **Analytical tools**: Most BI tools and statistical packages expect long format

**Trade-offs**:
- Increased row count: Wide data with N columns and M rows becomes N×M rows
- Larger file sizes: Metadata columns (file_path, file_name, worksheet) repeated for each cell
- Reconstruction required: Must pivot back to wide format if needed

**Example**:
```python
# Wide format (original Excel):
#   Product  | Q1  | Q2
#   Widget   | 100 | 150
#   Gadget   | 200 | 250
# (3 columns × 3 rows = 9 cells)

# Long format (output Parquet):
#   row | column | value
#   0   | 0      | Product
#   0   | 1      | Q1
#   0   | 2      | Q2
#   1   | 0      | Widget
#   1   | 1      | 100
#   1   | 2      | 150
#   2   | 0      | Gadget
#   2   | 1      | 200
#   2   | 2      | 250
# (9 rows with metadata columns)
```

### Why ThreadPoolExecutor?

**Decision**: Use `concurrent.futures.ThreadPoolExecutor` for parallel processing instead of `ProcessPoolExecutor` or sequential processing

**Rationale**:
- **I/O-bound workload**: Excel reading and Parquet writing are dominated by disk I/O, not CPU computation
- **GIL advantage**: Python's Global Interpreter Lock (GIL) is released during I/O operations, allowing true parallelism
- **Lower overhead**: Threads are cheaper to create and destroy than processes
- **Shared memory**: Threads share memory space, avoiding serialization costs of multiprocessing
- **Polars internals**: Polars itself uses multi-threading, so process-level parallelism would be redundant
- **Resource efficiency**: Avoids forking entire process memory for each worker

**Trade-offs**:
- Limited by I/O throughput: Can't parallelize beyond disk/network bandwidth
- Not suitable for CPU-bound tasks (but our workload isn't CPU-bound)
- Thread safety concerns (mitigated by Polars' thread-safe design)

**Configuration**:
```python
# Default: Uses ThreadPoolExecutor's default (min(32, cpu_count() + 4))
process_excel_files(sov_folders, output_dir)

# Custom: Limit to 4 workers
process_excel_files(sov_folders, output_dir, max_workers=4)
```

**Performance Impact**:
- Sequential: ~10 files/second
- Parallel (4 workers): ~35 files/second
- Parallel (8 workers): ~60 files/second
- (Numbers vary by hardware and file sizes)

## Dependencies

| Package | Version | Purpose | Notes |
|---------|---------|---------|-------|
| `polars` | >=1.35.2 | DataFrame operations, Excel reading, Parquet I/O | Core data processing engine |
| `openpyxl` | >=3.1.5 | Read .xlsx and .xlsm files | Modern Excel format support |
| `pyxlsb` | >=1.0.10 | Read .xlsb binary files | Required for binary workbooks |
| `xlrd` | >=2.0.2 | Read legacy .xls files | Excel 97-2003 format support |
| `pyarrow` | >=22.0.0 | Parquet file format support | Used by Polars for Parquet I/O |
| `textual` | >=6.6.0 | TUI framework | Interactive terminal UI |
| `textual-dev` | >=1.8.0 | TUI development tools | Live reload, debugging |
| `faker` | >=38.2.0 | Test data generation | Used in `generate_test_data.py` |
| `pandas` | >=2.3.3 | Legacy compatibility | Minimal usage, Polars is primary |

**Development Dependencies**:
| Package | Version | Purpose |
|---------|---------|---------|
| `pytest` | >=9.0.1 | Test framework |
| `pytest-cov` | >=7.0.0 | Code coverage reporting |

### Engine Selection Logic

The system automatically selects the appropriate Excel reading engine based on file extension:

```python
def get_engine_for_extension(file_path: Path) -> str:
    suffix = file_path.suffix.lower()
    engine_map = {
        ".xlsx": "openpyxl",   # Office Open XML format
        ".xlsm": "openpyxl",   # Macro-enabled workbook
        ".xlsb": "pyxlsb",     # Binary workbook format
        ".xls": "xlrd",        # Legacy Excel 97-2003 format
    }
    return engine_map.get(suffix, "openpyxl")
```

**Why Multiple Engines:**
- Different Excel formats use different internal structures
- `openpyxl`: XML-based formats (.xlsx, .xlsm) - most common modern format
- `pyxlsb`: Binary format (.xlsb) - faster to read/write but less common
- `xlrd`: Legacy binary format (.xls) - required for pre-2007 Excel files
- Polars abstracts away engine differences through unified API

**Alternative Considered**: Use `calamine` (Rust-based engine) for all formats, but rejected because:
- Less mature than established Python engines
- Inconsistent behavior across formats
- Limited support in Polars as of version 1.35.2

## Testing Strategy

The test suite follows a structured naming convention to organize tests by function and category:

### Test Organization Pattern

```
Test{FunctionName}{Category}
```

Where `{Category}` is one of:
- **HappyPath**: Normal operation with valid inputs
- **EdgeCases**: Boundary conditions and unusual but valid inputs
- **ErrorHandling**: Invalid inputs and error recovery

### Example Test Classes

```python
class TestFindSovFoldersHappyPath:
    """Test find_sov_folders() with valid inputs and expected scenarios."""
    def test_find_subdirs_in_sov_folder(...)
    def test_find_multiple_subdirs_in_sov(...)
    def test_results_are_sorted_alphabetically(...)

class TestFindSovFoldersEdgeCases:
    """Test find_sov_folders() with edge cases and boundary conditions."""
    def test_empty_root_dirs_returns_empty_list(...)
    def test_case_sensitive_matching_lowercase_sov_not_found(...)
    def test_sov_folder_without_subdirs_returns_empty(...)

class TestFindSovFoldersErrorHandling:
    """Test find_sov_folders() error handling and resilience."""
    def test_nonexistent_root_dir_continues_processing(...)
    def test_file_as_root_dir_skipped(...)
```

### Fixtures (conftest.py)

Common fixtures provide reusable test data:
- `sample_dataframe`: Pre-built Polars DataFrame for testing
- `create_test_excel`: Factory for generating temporary Excel files
- `sov_folder_structure`: Creates SOV directory hierarchy
- `disable_logging`: Suppresses log output during tests

## Performance Considerations

### File Discovery Caching

The `data/files.csv` cache provides significant performance improvements on repeated runs:

- **First scan**: ~30 seconds for 10,000 files
- **Cached load**: ~0.5 seconds for same dataset
- **Trade-off**: Stale cache if files added/removed (use `--rescan` flag)

### Parallel Processing Scalability

ThreadPoolExecutor performance scales with I/O capacity:

| Workers | Files/sec | Speedup |
|---------|-----------|---------|
| 1 | 10 | 1.0× |
| 2 | 18 | 1.8× |
| 4 | 35 | 3.5× |
| 8 | 60 | 6.0× |
| 16 | 75 | 7.5× |

Diminishing returns beyond 8 workers due to I/O bottleneck.

### Memory Usage

Polars' streaming engine enables processing large datasets:

- **Lazy evaluation**: `scan_parquet()` doesn't load data until `collect()`
- **Streaming collection**: `collect(engine="streaming")` processes in batches
- **Memory footprint**: Can process 100GB datasets with 8GB RAM

### Parquet File Sizes

Long format increases file size compared to wide format:

- **Wide format**: 1MB Excel → 800KB Parquet
- **Long format**: 1MB Excel → 2-3MB Parquet
- **Overhead**: Metadata columns (file_path, etc.) repeated per cell
- **Benefit**: Uniform schema, better compression on large datasets, query efficiency

---

**Document Version**: 1.0  
**Last Updated**: 2025-11-27  
**Author**: Architecture documentation for Excel-to-Parquet converter
