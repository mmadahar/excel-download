<objective>
Transform the Excel-to-Parquet tool into an interactive TUI (Text User Interface) that allows users to run operations interactively, monitor progress, and inspect results.

This makes the tool more approachable for users who want to understand what's happening at each stage of the conversion process.
</objective>

<context>
The current `excel_to_parquet.py` is a CLI tool with argparse. The TUI should wrap the existing functionality without breaking the current CLI interface.

Read CLAUDE.md for project conventions and existing architecture.

Key existing functions to integrate:
- `scan_for_excel_files()` - Discovers Excel files
- `find_sov_folders()` - Finds SOV directories  
- `process_excel_files()` - Converts Excel to Parquet
- `load_or_scan_files()` - Caching layer for file discovery
</context>

<requirements>
1. Create a new `tui.py` module using the Textual framework
2. Implement an interactive dashboard with these features:

**Main Menu:**
- Scan directories for Excel files
- View discovered files
- Convert files to Parquet
- View conversion results
- Settings/Configuration
- Exit

**Scan Screen:**
- Input field for root directory path(s)
- Checkbox for "Force rescan" option
- Progress bar during scanning
- Results summary showing files found by extension

**File Browser:**
- DataTable showing discovered Excel files
- Columns: filename, path, extension, discovered date
- Sorting and filtering capabilities
- Selection for targeted conversion

**Conversion Screen:**
- Input for output directory
- Real-time progress indicator
- Per-file status updates (processing, completed, error)
- Summary statistics on completion

**Results Viewer:**
- List of generated Parquet files
- Preview of sample data (first 10 rows)
- Metadata display (row count, columns, file size)

3. Preserve existing CLI interface - TUI is an additional entry point
4. Add keyboard shortcuts for power users
</requirements>

<implementation>
Structure the TUI with these components:

```
tui.py
├── ExcelConverterApp(App)          # Main Textual application
├── MainMenu(Screen)                # Navigation screen
├── ScanScreen(Screen)              # Directory scanning UI
├── FileBrowserScreen(Screen)       # View/select discovered files
├── ConversionScreen(Screen)        # Run conversions with progress
├── ResultsScreen(Screen)           # View output Parquet files
└── SettingsScreen(Screen)          # Configuration options
```

WHY Textual: Modern Python TUI framework with:
- Reactive updates for progress tracking
- Built-in widgets (DataTable, Input, Button, ProgressBar)
- CSS-like styling for professional appearance
- Async support for non-blocking operations

Key implementation notes:
- Use worker threads for long operations (scan, convert) to keep UI responsive
- Store state in app-level reactive variables
- Reuse existing functions from excel_to_parquet.py - don't duplicate logic
</implementation>

<dependencies>
Add to project:
- textual>=0.40.0
- textual-dev (for development/debugging)

Run: `uv add textual textual-dev`
</dependencies>

<output>
Create/modify files:
- `./tui.py` - Main TUI application
- Update `./pyproject.toml` - Add textual dependencies
- Optional: `./tui.tcss` - Custom Textual CSS styling

Entry point: `uv run python tui.py`
</output>

<verification>
Before declaring complete, verify:
1. `uv add textual textual-dev` completes successfully
2. `uv run python tui.py` launches the TUI without errors
3. Navigate through all screens using keyboard
4. Perform a full workflow:
   - Scan `data/test_excel/` directory
   - View discovered files in browser
   - Convert files to `data/tui_output/`
   - View results and preview data
5. Original CLI still works: `uv run python excel_to_parquet.py --help`
</verification>

<success_criteria>
- TUI launches and displays main menu
- All screens are navigable and functional
- Scanning shows real-time progress
- File browser displays discovered files correctly
- Conversion runs with progress updates
- Results viewer shows Parquet file metadata
- Original CLI interface unchanged
- Keyboard shortcuts work (q=quit, etc.)
</success_criteria>
