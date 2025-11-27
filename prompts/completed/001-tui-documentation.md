# TUI Documentation

## Overview

The Excel-to-Parquet Converter TUI (Text User Interface) is an interactive terminal-based application built with [Textual](https://textual.textualize.io/). It provides a user-friendly interface for discovering Excel files, browsing them, converting to Parquet format, and inspecting results.

**Key Features:**
- Interactive directory scanning with progress feedback
- File browser with DataTable display
- Background conversion with live logging
- Parquet file inspection with row-level preview
- Keyboard-driven navigation
- Visual progress indicators

**Entry Point:**
```bash
uv run python tui.py
```

## Screen Flow Diagram

```
┌─────────────────────────────────────────────────────────────────┐
│                          MainMenu                               │
│                     (Navigation Hub)                            │
│                                                                 │
│  [1] Scan Directories ────────┐                                │
│  [2] View Discovered Files ───┼────┐                           │
│  [3] Convert to Parquet ──────┼────┼────┐                      │
│  [4] View Results ────────────┼────┼────┼────┐                 │
│  [Q] Exit                     │    │    │    │                 │
└───────────────────────────────┼────┼────┼────┼─────────────────┘
                                │    │    │    │
                                ▼    │    │    │
                    ┌───────────────────┐ │    │
                    │   ScanScreen      │ │    │
                    │ (File Discovery)  │ │    │
                    │                   │ │    │
                    │ • Enter directory │ │    │
                    │ • Force rescan?   │ │    │
                    │ • Run scan        │ │    │
                    │ • View summary    │ │    │
                    └───────────────────┘ │    │
                         │ saves to       │    │
                         ▼                │    │
                    files.csv ────────────┼────┼───┐
                                          │    │   │
                                          ▼    │   │
                           ┌────────────────────┐  │
                           │ FileBrowserScreen  │  │
                           │  (View Files)      │  │
                           │                    │  │
                           │ • Table of files   │  │
                           │ • Refresh data     │  │
                           └────────────────────┘  │
                                                   │
                                          ▼        │
                           ┌────────────────────┐  │
                           │ ConversionScreen   │  │
                           │  (Convert)         │  │
                           │                    │  │
                           │ • Set output dir   │  │
                           │ • Run conversion   │  │
                           │ • View logs        │  │
                           └────────────────────┘  │
                                │ creates          │
                                ▼                  │
                           *.parquet ──────────────┘
                                                   │
                                                   ▼
                                    ┌───────────────────────┐
                                    │  ResultsScreen        │
                                    │  (Inspect Results)    │
                                    │                       │
                                    │ • List Parquet files  │
                                    │ • View metadata       │
                                    │ • Preview data        │
                                    └───────────────────────┘
```

## Screens

### MainMenu

**Purpose:** Central navigation hub providing access to all TUI functionality.

**Components:**
- Title: "Excel-to-Parquet Converter"
- Four primary navigation buttons
- Exit button
- Header and Footer (with keybindings)

**ASCII Mockup:**
```
┌─────────────────────────────────────────────────────────────────┐
│ Excel-to-Parquet Converter                               Q Quit │
├─────────────────────────────────────────────────────────────────┤
│                                                                 │
│                                                                 │
│                   Excel-to-Parquet Converter                    │
│                                                                 │
│                                                                 │
│                   ┌───────────────────────────────┐             │
│                   │  [1] Scan Directories         │             │
│                   └───────────────────────────────┘             │
│                   ┌───────────────────────────────┐             │
│                   │  [2] View Discovered Files    │             │
│                   └───────────────────────────────┘             │
│                   ┌───────────────────────────────┐             │
│                   │  [3] Convert to Parquet       │             │
│                   └───────────────────────────────┘             │
│                   ┌───────────────────────────────┐             │
│                   │  [4] View Results             │             │
│                   └───────────────────────────────┘             │
│                                                                 │
│                                                                 │
│                   ┌───────────────────────────────┐             │
│                   │  [Q] Exit                     │             │
│                   └───────────────────────────────┘             │
│                                                                 │
│                                                                 │
├─────────────────────────────────────────────────────────────────┤
│ 1 Scan │ 2 Browse │ 3 Convert │ 4 Results │ Q Quit             │
└─────────────────────────────────────────────────────────────────┘
```

**User Workflow:**
1. Launch TUI with `uv run python tui.py`
2. MainMenu appears
3. Select option via mouse click or keyboard shortcut (1-4, Q)
4. Navigate to corresponding screen
5. Return to MainMenu via ESC or Back button

**Key Bindings:**
| Key | Action | Description |
|-----|--------|-------------|
| `1` | Scan | Go to ScanScreen |
| `2` | Browse | Go to FileBrowserScreen |
| `3` | Convert | Go to ConversionScreen |
| `4` | Results | Go to ResultsScreen |
| `q` | Quit | Exit application |

**Data Flow:**
- **Input:** User selection
- **Output:** Screen navigation (push new screen onto stack)
- **State:** No persistent state stored

**Error Handling:**
- No errors expected (simple navigation)

---

### ScanScreen

**Purpose:** Discover Excel files in directory trees and cache results to `data/files.csv`.

**Components:**
- Title: "Scan for Excel Files"
- Input field: Root directory path
- Checkbox: Force Rescan (ignore cache)
- Buttons: "Start Scan", "Back"
- ProgressBar: Visual scan progress (0-100)
- Status label: Real-time status messages
- Results summary: File count breakdown by extension

**ASCII Mockup:**
```
┌─────────────────────────────────────────────────────────────────┐
│ Excel-to-Parquet Converter                         ESC Back     │
├─────────────────────────────────────────────────────────────────┤
│                                                                 │
│                     Scan for Excel Files                        │
│                                                                 │
│  Root Directory:                                                │
│  ┌────────────────────────────────────────────────────────────┐ │
│  │ ./data/test_excel                                          │ │
│  └────────────────────────────────────────────────────────────┘ │
│                                                                 │
│  ☑ Force Rescan                                                 │
│                                                                 │
│  ┌──────────────┐  ┌──────────────┐                            │
│  │ Start Scan   │  │ Back         │                            │
│  └──────────────┘  └──────────────┘                            │
│                                                                 │
│  Progress:                                                      │
│  ████████████████████████████░░░░░░░░░░░░ 80%                  │
│                                                                 │
│  Status: Scanning...                                            │
│                                                                 │
│  Found 47 Excel file(s):                                        │
│    .xlsx: 35                                                    │
│    .xlsm: 8                                                     │
│    .xlsb: 3                                                     │
│    .xls: 1                                                      │
│                                                                 │
├─────────────────────────────────────────────────────────────────┤
│ ESC Back │ ENTER Start Scan                                    │
└─────────────────────────────────────────────────────────────────┘
```

**User Workflow:**
1. Enter directory path (e.g., `./data/test_excel`)
2. Optionally check "Force Rescan" to ignore cached results
3. Click "Start Scan" or press ENTER
4. Watch progress bar advance
5. Review summary showing file counts by extension
6. Press ESC or "Back" to return to MainMenu

**Key Bindings:**
| Key | Action | Description |
|-----|--------|-------------|
| `ESC` | Go Back | Return to MainMenu |
| `ENTER` | Start Scan | Begin directory scan |

**Data Flow:**
- **Input:** 
  - Directory path (string)
  - Rescan flag (boolean)
- **Processing:** 
  - Calls `load_or_scan_files([directory], rescan)`
  - Runs in background thread via `@work(thread=True)`
  - Updates UI via `call_from_thread()`
- **Output:**
  - Saves DataFrame to `data/files.csv`
  - Stores in `app.discovered_files` state
  - Displays summary statistics

**Error Handling:**
| Error Condition | User Feedback |
|----------------|---------------|
| Empty directory input | "Error: Please enter a directory path" |
| Directory doesn't exist | "Error: Directory does not exist: {path}" |
| Scan exception | "Error: {exception_message}" (progress bar resets to 0) |

**Background Processing:**
The scan runs asynchronously to keep the UI responsive:
1. Status: "Scanning..." (progress: 10%)
2. Calls `load_or_scan_files()` function
3. Progress advances to 80%
4. Groups files by extension for summary
5. Progress reaches 100%
6. Status: "Scan complete!"

---

### FileBrowserScreen

**Purpose:** Display discovered Excel files in a sortable table with metadata.

**Components:**
- Title: "Discovered Excel Files"
- File count label
- DataTable with columns: Filename, Extension, Path, Discovered
- Buttons: "Refresh", "Back"

**ASCII Mockup:**
```
┌─────────────────────────────────────────────────────────────────┐
│ Excel-to-Parquet Converter                ESC Back │ R Refresh  │
├─────────────────────────────────────────────────────────────────┤
│                                                                 │
│                   Discovered Excel Files                        │
│                                                                 │
│  Total: 47 file(s)                                              │
│                                                                 │
│  ┌──────────────────────────────────────────────────────────┐   │
│  │ Filename        │ Ext   │ Path          │ Discovered     │   │
│  ├─────────────────┼───────┼───────────────┼────────────────┤   │
│  │ sales_2024.xlsx │ .xlsx │ /data/excel   │ 2025-11-27 ... │   │
│  │ report.xlsm     │ .xlsm │ /data/reports │ 2025-11-27 ... │   │
│  │ summary.xlsb    │ .xlsb │ /data/archive │ 2025-11-27 ... │   │
│  │ legacy.xls      │ .xls  │ /data/old     │ 2025-11-27 ... │   │
│  │ ...             │ ...   │ ...           │ ...            │   │
│  └──────────────────────────────────────────────────────────┘   │
│                                                                 │
│                                                                 │
│  ┌──────────────┐  ┌──────────────┐                            │
│  │ Refresh      │  │ Back         │                            │
│  └──────────────┘  └──────────────┘                            │
│                                                                 │
├─────────────────────────────────────────────────────────────────┤
│ ESC Back │ R Refresh                                           │
└─────────────────────────────────────────────────────────────────┘
```

**User Workflow:**
1. Screen auto-loads on mount
2. Browse files using arrow keys or mouse scroll
3. Click "Refresh" or press `R` to reload from cache
4. Press ESC or "Back" to return to MainMenu

**Key Bindings:**
| Key | Action | Description |
|-----|--------|-------------|
| `ESC` | Go Back | Return to MainMenu |
| `r` | Refresh | Reload file list |
| `↑`/`↓` | Navigate | Move through table rows |

**Data Flow:**
- **Input:** 
  - Reads from `app.discovered_files` (in-memory)
  - Falls back to `data/files.csv` if not in memory
- **Processing:**
  - Loads Polars DataFrame
  - Iterates rows to populate DataTable
  - Truncates timestamps to 19 chars (YYYY-MM-DD HH:MM:SS)
- **Output:**
  - Visual table display
  - File count summary

**Error Handling:**
| Condition | User Feedback |
|-----------|---------------|
| No files found | "No files discovered. Run a scan first." |
| CSV read error | Silent fallback to empty state |

**State Dependencies:**
- Requires `ScanScreen` to have run successfully
- Depends on `data/files.csv` existing OR `app.discovered_files` being set

---

### ConversionScreen

**Purpose:** Convert discovered Excel files to Parquet format with live progress logging.

**Components:**
- Title: "Convert to Parquet"
- Input field: Output directory (default: `./data/output`)
- Buttons: "Start Conversion", "Back"
- ProgressBar: Conversion progress (0-100)
- Status label: Current operation
- Scrollable log output: Timestamped conversion events

**ASCII Mockup:**
```
┌─────────────────────────────────────────────────────────────────┐
│ Excel-to-Parquet Converter             ESC Back │ ENTER Convert │
├─────────────────────────────────────────────────────────────────┤
│                                                                 │
│                      Convert to Parquet                         │
│                                                                 │
│  Output Directory:                                              │
│  ┌────────────────────────────────────────────────────────────┐ │
│  │ ./data/output                                              │ │
│  └────────────────────────────────────────────────────────────┘ │
│                                                                 │
│  ┌──────────────────┐  ┌──────────────┐                        │
│  │ Start Conversion │  │ Back         │                        │
│  └──────────────────┘  └──────────────┘                        │
│                                                                 │
│  Progress:                                                      │
│  ████████████████░░░░░░░░░░░░░░░░░░░░░ 20%                     │
│                                                                 │
│  Status: Starting conversion...                                 │
│                                                                 │
│  ┌────────────────────────────────────────────────────────────┐ │
│  │ [11:23:45] Output directory: ./data/output                 │ │
│  │ [11:23:46] Processing 47 file(s)...                        │ │
│  │ [11:23:46] Already processed: 12 file(s)                   │ │
│  │ [11:23:50] Processing: sales_2024.xlsx                     │ │
│  │ [11:23:52] Created: abc123.parquet (Sheet1, 450 rows)      │ │
│  │ ...                                                         │ │
│  └────────────────────────────────────────────────────────────┘ │
│                                                                 │
├─────────────────────────────────────────────────────────────────┤
│ ESC Back │ ENTER Start Convert                                 │
└─────────────────────────────────────────────────────────────────┘
```

**User Workflow:**
1. Verify/modify output directory path
2. Click "Start Conversion" or press ENTER
3. Watch progress bar and live log output
4. Wait for "Conversion complete!" status
5. Note final Parquet file count in log
6. Press ESC or "Back" to return

**Key Bindings:**
| Key | Action | Description |
|-----|--------|-------------|
| `ESC` | Go Back | Return to MainMenu |
| `ENTER` | Start Convert | Begin conversion process |

**Data Flow:**
- **Input:**
  - Output directory path
  - Reads `data/files.csv` for file list
- **Processing:**
  - Runs `process_excel_files([], output_path)` in background thread
  - Calls `get_processed_file_paths()` to detect already-converted files (idempotency)
  - Appends timestamped log entries during conversion
- **Output:**
  - Creates `*.parquet` files in output directory
  - Stores `output_path` in `app.output_dir` state
  - Returns count of generated Parquet files

**Error Handling:**
| Condition | User Feedback |
|-----------|---------------|
| Empty output directory | "Error: Please enter an output directory" |
| files.csv missing | "Error: No files discovered. Run a scan first." |
| Conversion exception | "Error: {exception}" (in both status and log) |

**Background Processing:**
Conversion runs asynchronously with live updates:
1. Status: "Starting conversion..." (5%)
2. Creates output directory
3. Loads file list, counts total files
4. Status: "Processing {N} file(s)..." (20%)
5. Checks for already-processed files
6. Calls main conversion function
7. Status: "Conversion complete!" (100%)
8. Logs final Parquet file count

**Log Format:**
```
[HH:MM:SS] {message}
```

Examples:
- `[11:23:45] Output directory: ./data/output`
- `[11:23:46] Processing 47 file(s)...`
- `[11:23:46] Already processed: 12 file(s)`
- `[11:24:30] Generated 142 Parquet file(s)`

---

### ResultsScreen

**Purpose:** Inspect generated Parquet files, view metadata, and preview data contents.

**Components:**
- Title: "Conversion Results"
- Input field: Output directory (default: `./data/output`)
- Buttons: "Load Results", "Back"
- Summary label: File count
- Results table: Filename, Size (KB), Rows, Source File
- Preview title: "Preview (first 10 rows of selected file)"
- Preview table: file_path, worksheet, row, column, value

**ASCII Mockup:**
```
┌─────────────────────────────────────────────────────────────────┐
│ Excel-to-Parquet Converter                ESC Back │ R Refresh  │
├─────────────────────────────────────────────────────────────────┤
│                                                                 │
│                     Conversion Results                          │
│                                                                 │
│  Output Directory:                                              │
│  ┌────────────────────────────────────────────────────────────┐ │
│  │ ./data/output                                              │ │
│  └────────────────────────────────────────────────────────────┘ │
│  ┌──────────────┐  ┌──────────────┐                            │
│  │ Load Results │  │ Back         │                            │
│  └──────────────┘  └──────────────┘                            │
│                                                                 │
│  Found 142 Parquet file(s)                                      │
│                                                                 │
│  ┌──────────────────────────────────────────────────────────┐   │
│  │ Filename       │ Size (KB) │ Rows │ Source File         │   │
│  ├────────────────┼───────────┼──────┼─────────────────────┤   │
│  │ abc123.parquet │ 45.2      │ 450  │ sales_2024.xlsx     │   │
│  │ def456.parquet │ 12.8      │ 120  │ report.xlsm         │   │
│  │ ghi789.parquet │ 98.7      │ 2340 │ summary.xlsb        │   │
│  │ ...            │ ...       │ ...  │ ...                 │   │
│  └──────────────────────────────────────────────────────────┘   │
│                                                                 │
│  Preview (first 10 rows of selected file):                      │
│  ┌──────────────────────────────────────────────────────────┐   │
│  │ file_path   │ worksheet │ row │ column │ value           │   │
│  ├─────────────┼───────────┼─────┼────────┼─────────────────┤   │
│  │ /data/ex... │ Sheet1    │ 0   │ 0      │ Product         │   │
│  │ /data/ex... │ Sheet1    │ 0   │ 1      │ Revenue         │   │
│  │ /data/ex... │ Sheet1    │ 1   │ 0      │ Widget A        │   │
│  │ /data/ex... │ Sheet1    │ 1   │ 1      │ 45000           │   │
│  │ ...         │ ...       │ ... │ ...    │ ...             │   │
│  └──────────────────────────────────────────────────────────┘   │
│                                                                 │
├─────────────────────────────────────────────────────────────────┤
│ ESC Back │ R Refresh                                           │
└─────────────────────────────────────────────────────────────────┘
```

**User Workflow:**
1. Screen auto-loads if `app.output_dir` is set (from ConversionScreen)
2. Alternatively, enter output directory manually and click "Load Results"
3. Browse Parquet files in results table
4. Click on a row to see preview of first 10 data rows
5. Press `R` to refresh file list
6. Press ESC or "Back" to return to MainMenu

**Key Bindings:**
| Key | Action | Description |
|-----|--------|-------------|
| `ESC` | Go Back | Return to MainMenu |
| `r` | Refresh | Reload results from directory |
| `↑`/`↓` | Navigate | Move through results table |
| `Click` | Select | Show preview of selected file |

**Data Flow:**
- **Input:**
  - Output directory path
  - User row selection in results table
- **Processing:**
  - Scans directory for `*.parquet` files
  - Reads each file to get row count and metadata
  - On row selection, loads first 10 rows of selected file
- **Output:**
  - Results table populated with file metadata
  - Preview table shows normalized data structure

**Error Handling:**
| Condition | User Feedback |
|-----------|---------------|
| Directory not found | "Directory not found: {path}" |
| No Parquet files | "No Parquet files found." |
| File read error | Row shows "Error" in Rows column, truncated error in Source File |
| Preview error | "Preview error: {exception}" |

**Results Table Columns:**
| Column | Description | Example |
|--------|-------------|---------|
| Filename | Parquet file name (UUID-based) | `abc123.parquet` |
| Size (KB) | File size in kilobytes | `45.2` |
| Rows | Number of data rows | `450` |
| Source File | Original Excel filename | `sales_2024.xlsx` |

**Preview Table Columns:**
| Column | Description | Example |
|--------|-------------|---------|
| file_path | Full path to source Excel file | `/data/excel/sales_2024.xlsx` (truncated to 40 chars) |
| worksheet | Sheet name | `Sheet1`, `Summary`, etc. |
| row | Row number (0-indexed) | `0`, `1`, `2`... |
| column | Column number (0-indexed) | `0`, `1`, `2`... |
| value | Cell value as string | `Product`, `45000`, etc. (truncated to 30 chars) |

**Display Limits:**
- Results table: First 50 files only (sorted alphabetically)
- Preview table: First 10 rows only

---

## State Management

The TUI uses the main `ExcelConverterApp` class to manage shared state across screens:

### App-Level State

```python
class ExcelConverterApp(App):
    def __init__(self):
        super().__init__()
        self.discovered_files = None  # Polars DataFrame
        self.output_dir = None        # Path object
```

### State Flow

```
┌─────────────────────────────────────────────────────────────┐
│                     ExcelConverterApp                       │
│                                                             │
│  State:                                                     │
│  • discovered_files: Polars DataFrame                       │
│  • output_dir: Path                                         │
└─────────────────────────────────────────────────────────────┘
         ▲                           │                  ▲
         │                           │                  │
         │ writes                    │ reads            │ writes
         │                           ▼                  │
    ┌─────────┐              ┌──────────────┐    ┌──────────────┐
    │  Scan   │              │ FileBrowser  │    │ Conversion   │
    │ Screen  │              │   Screen     │    │   Screen     │
    └─────────┘              └──────────────┘    └──────────────┘
         │                                              │
         │ also saves                                   │ creates
         ▼                                              ▼
    data/files.csv ◄──────── reads ────────    *.parquet files
         │                                              │
         │                                              │
         └────────── both read by ──────────────────────┘
                           │
                           ▼
                   ┌──────────────┐
                   │   Results    │
                   │   Screen     │
                   └──────────────┘
```

### State Details

| State Variable | Type | Set By | Read By | Persistence |
|----------------|------|--------|---------|-------------|
| `app.discovered_files` | `pl.DataFrame` | ScanScreen | FileBrowserScreen | In-memory only |
| `app.output_dir` | `Path` | ConversionScreen | ResultsScreen | In-memory only |
| `data/files.csv` | CSV file | ScanScreen | FileBrowserScreen, ConversionScreen | Disk-persisted |
| `{output}/*.parquet` | Parquet files | ConversionScreen | ResultsScreen | Disk-persisted |

### Cache Behavior

**files.csv caching:**
- ScanScreen respects "Force Rescan" checkbox
- If unchecked: `load_or_scan_files()` returns cached data if CSV exists
- If checked: Forces new scan regardless of cache

**Parquet idempotency:**
- ConversionScreen calls `get_processed_file_paths()` before converting
- Skips Excel files already represented in output directory
- Based on `file_path` metadata column in existing Parquet files

---

## Keyboard Shortcuts Reference

### Global Shortcuts
| Key | Action | Available On |
|-----|--------|--------------|
| `q` | Quit Application | All screens (via Footer) |
| `ESC` | Go Back | All screens except MainMenu |

### MainMenu Shortcuts
| Key | Action | Description |
|-----|--------|-------------|
| `1` | Scan | Navigate to ScanScreen |
| `2` | Browse | Navigate to FileBrowserScreen |
| `3` | Convert | Navigate to ConversionScreen |
| `4` | Results | Navigate to ResultsScreen |
| `q` | Quit | Exit application |

### ScanScreen Shortcuts
| Key | Action | Description |
|-----|--------|-------------|
| `ESC` | Back | Return to MainMenu |
| `ENTER` | Start Scan | Begin directory scan |

### FileBrowserScreen Shortcuts
| Key | Action | Description |
|-----|--------|-------------|
| `ESC` | Back | Return to MainMenu |
| `r` | Refresh | Reload file list from cache |
| `↑` | Up | Move selection up in table |
| `↓` | Down | Move selection down in table |
| `PgUp` | Page Up | Scroll up one page |
| `PgDn` | Page Down | Scroll down one page |

### ConversionScreen Shortcuts
| Key | Action | Description |
|-----|--------|-------------|
| `ESC` | Back | Return to MainMenu |
| `ENTER` | Start Convert | Begin conversion process |

### ResultsScreen Shortcuts
| Key | Action | Description |
|-----|--------|-------------|
| `ESC` | Back | Return to MainMenu |
| `r` | Refresh | Reload results from directory |
| `↑` | Up | Move selection up in results table |
| `↓` | Down | Move selection down in results table |
| `Click` | Select Row | Show preview of selected Parquet file |
| `PgUp` | Page Up | Scroll up one page |
| `PgDn` | Page Down | Scroll down one page |

### Mouse Interactions
| Action | Result |
|--------|--------|
| Click Button | Execute button action |
| Click Table Row | Select row (triggers preview in ResultsScreen) |
| Scroll Wheel | Scroll through tables/logs |
| Click Input Field | Focus field for text entry |

---

## UI Components Reference

### Widgets Used

| Widget | Purpose | Used In |
|--------|---------|---------|
| `Header` | Shows app title and global shortcuts | All screens |
| `Footer` | Shows active keybindings | All screens |
| `Button` | Clickable action triggers | All screens |
| `Input` | Text entry fields | ScanScreen, ConversionScreen, ResultsScreen |
| `Checkbox` | Boolean toggle (Force Rescan) | ScanScreen |
| `DataTable` | Tabular data display | FileBrowserScreen, ResultsScreen |
| `ProgressBar` | Visual progress indicator | ScanScreen, ConversionScreen |
| `Static` | Read-only text labels | All screens |
| `Label` | Field labels | ScanScreen, ConversionScreen, ResultsScreen |
| `VerticalScroll` | Scrollable log container | ConversionScreen |
| `Container` | Layout grouping | All screens |
| `Horizontal` | Horizontal layout | All screens (button rows) |

### Button Variants

| Variant | Color | Used For |
|---------|-------|----------|
| `primary` | Blue | Main actions (Scan, Load Results) |
| `success` | Green | Convert action |
| `default` | Gray | Secondary actions (Back, Refresh) |
| `error` | Red | Exit button |

---

## Design Patterns

### Background Processing with `@work`

Long-running operations use Textual's `@work(thread=True)` decorator to prevent UI blocking:

```python
@work(thread=True)
def run_scan(self, directory: str, rescan: bool) -> None:
    """Run the scan in a background thread."""
    self.call_from_thread(self._update_status, "Scanning...")
    # ... perform work ...
    self.call_from_thread(self._update_progress, 100)
```

**Key points:**
- Work runs in separate thread
- UI updates via `call_from_thread()` helper
- User can still navigate/interact with UI
- Used in: ScanScreen, ConversionScreen

### Progressive Disclosure

Information is revealed progressively:
1. MainMenu: High-level options only
2. ScanScreen: Results appear after scan completes
3. FileBrowserScreen: Table populates on mount
4. ConversionScreen: Log grows during conversion
5. ResultsScreen: Preview loads on row selection

### Idempotency

ConversionScreen checks for already-processed files:
- Reads metadata from existing Parquet files
- Builds set of processed `file_path` values
- Skips Excel files already in output directory
- Prevents duplicate conversions on repeated runs

### Error Resilience

Each screen handles errors gracefully:
- User input validation before processing
- Try/except blocks around file operations
- Clear error messages in UI
- Progress bars reset on error
- Log output includes error details

---

## CSS Styling (tui.tcss)

The TUI uses Textual CSS for visual styling. Key style patterns:

### Layout
- Screen containers: Full width/height, centered alignment
- Padding: `1 2` (vertical horizontal) for screen containers
- Margins: `1 0` for spacing between elements

### Colors
- `$primary`: Primary accent color (borders, highlights)
- `$accent`: Title text color
- `$surface`: Background for containers
- `$text`: Standard text color

### Focus States
- Inputs get `$accent` border on focus
- Buttons show `$primary` background on hover
- DataTables get `$accent` border on focus

### DataTable Styling
- Bordered with `$primary`
- Max height constraints (15 rows for main tables, 12 for preview)
- Auto-height calculation for content

### Responsive Behavior
- Containers use `1fr` (fractional units) for flexible sizing
- Tables scroll vertically when content exceeds max-height
- VerticalScroll containers provide automatic scrolling

---

## File Dependencies

### Imports from excel_to_parquet.py

The TUI reuses core functions:

```python
from excel_to_parquet import (
    FILES_CSV,                    # Path constant: 'data/files.csv'
    find_sov_folders,             # Finds directories with /SOV/ in path
    get_processed_file_paths,     # Returns set of already-converted files
    load_or_scan_files,           # Main scan function (respects cache)
    process_excel_files,          # Main conversion function
    scan_for_excel_files,         # Direct scan (no cache)
)
```

### External Dependencies

| Package | Purpose |
|---------|---------|
| `textual` | TUI framework (screens, widgets, layout) |
| `polars` | DataFrame operations, Parquet I/O |
| `pathlib` | File path handling |
| `datetime` | Timestamps for log entries |

---

## Testing Recommendations

### Manual Testing Checklist

**MainMenu:**
- [ ] All 5 buttons are clickable
- [ ] Keyboard shortcuts (1-4, Q) work
- [ ] Screen transitions occur correctly
- [ ] Footer shows bindings

**ScanScreen:**
- [ ] Input field accepts directory paths
- [ ] Force Rescan checkbox toggles
- [ ] Invalid paths show error messages
- [ ] Progress bar advances during scan
- [ ] Summary shows correct file counts
- [ ] data/files.csv is created/updated
- [ ] ESC returns to MainMenu

**FileBrowserScreen:**
- [ ] Table populates from files.csv
- [ ] File count is accurate
- [ ] Refresh button reloads data
- [ ] Table is scrollable
- [ ] Arrow keys navigate rows
- [ ] Shows friendly message when no files exist

**ConversionScreen:**
- [ ] Output directory has default value
- [ ] Start button is disabled without files.csv
- [ ] Progress bar advances during conversion
- [ ] Log shows timestamped entries
- [ ] Log is scrollable during conversion
- [ ] Final file count is accurate
- [ ] Parquet files are created in output directory

**ResultsScreen:**
- [ ] Table populates from output directory
- [ ] File sizes are calculated correctly
- [ ] Row counts match Parquet file contents
- [ ] Source file names are extracted from metadata
- [ ] Clicking a row loads preview
- [ ] Preview shows first 10 rows
- [ ] Preview columns match schema
- [ ] Refresh button reloads results

### Edge Cases

| Scenario | Expected Behavior |
|----------|-------------------|
| Empty scan directory | "No Excel files found" message |
| Output directory doesn't exist | Directory is created automatically |
| Very large file count (1000+) | Results table shows first 50 only |
| Corrupted Excel file | Error logged, conversion continues |
| Permission denied on directory | Error message displayed |
| Parquet file read failure | "Error" shown in table row |
| Concurrent TUI instances | Each operates independently (no file locks) |

---

## Future Enhancements

Potential improvements for the TUI:

1. **Real-time conversion progress:**
   - Show current file being processed
   - Display per-file progress percentage
   - Estimated time remaining

2. **File filtering:**
   - Filter FileBrowserScreen by extension
   - Search by filename
   - Filter by date range

3. **Export options:**
   - Export file list to CSV
   - Export conversion log to file
   - Copy preview data to clipboard

4. **Validation:**
   - Preview Excel files before conversion
   - Show warnings for files that may fail
   - Validate output schema

5. **Batch operations:**
   - Select multiple files for conversion
   - Queue conversions
   - Pause/resume conversion

6. **Configuration:**
   - Save default directories
   - Customize column mappings
   - Configure worker threads

7. **Error recovery:**
   - Retry failed conversions
   - Skip problematic sheets
   - Export error report

8. **Advanced preview:**
   - Show more than 10 rows
   - Column filtering
   - Data type inference
   - Basic statistics (row count, column count, null values)

---

## Troubleshooting

### Common Issues

**Issue:** "No files discovered. Run a scan first."
- **Cause:** files.csv doesn't exist or is empty
- **Solution:** Navigate to ScanScreen and run a scan

**Issue:** Progress bar stuck at 5%
- **Cause:** Background thread hung or crashed
- **Solution:** Press ESC to exit screen, check terminal for stack trace

**Issue:** Preview table is empty
- **Cause:** Selected Parquet file has 0 rows or read error
- **Solution:** Check file with external tool (e.g., `polars`)

**Issue:** Log output doesn't scroll
- **Cause:** Focus is not on log container
- **Solution:** Click inside log area before scrolling

**Issue:** Keyboard shortcuts don't work
- **Cause:** Focus is on input field
- **Solution:** Press ESC or Tab to change focus

### Debug Mode

Run with Textual's dev console for debugging:

```bash
textual console
# In another terminal:
uv run python tui.py
```

This shows:
- Log messages
- Widget tree
- CSS calculations
- Event stream

---

## Conclusion

The Excel-to-Parquet TUI provides a comprehensive, user-friendly interface for:
1. **Discovery:** Scanning directories for Excel files
2. **Inspection:** Browsing discovered files
3. **Conversion:** Converting to Parquet with progress feedback
4. **Validation:** Previewing results and metadata

**Key Strengths:**
- Asynchronous processing keeps UI responsive
- Clear visual feedback with progress bars and logs
- Keyboard-driven navigation for power users
- Idempotent conversions prevent duplicates
- Reuses core CLI functions for consistency

**Design Philosophy:**
- Progressive disclosure of information
- Graceful error handling
- Minimal user input required
- Visual consistency across screens
- Predictable navigation patterns

The TUI complements the CLI (`excel_to_parquet.py`) by providing:
- Interactive exploration vs. batch processing
- Visual feedback vs. text logs
- Guided workflow vs. command-line flags
- Point-and-click vs. scripting

Both interfaces share the same core conversion logic, ensuring consistent results regardless of entry point.
