<objective>
Update the TUI (src/excel_converter/tui.py) to enhance directory input and progress tracking:

1. Keep current single-directory input functionality
2. Add ability to load directories from an Excel spreadsheet (single column, column A)
3. Display directories in a manageable list before scanning
4. Add detailed progress bars showing actual file counts to both ScanScreen and ConversionScreen
</objective>

<context>
This is a Textual-based TUI for an Excel-to-Parquet converter. Review the existing code:
@src/excel_converter/tui.py
@src/excel_converter/cli.py

The TUI currently has:
- ScanScreen with single directory Input and basic ProgressBar
- ConversionScreen with basic ProgressBar
- Background workers using @work(thread=True) decorator

Tech stack: Python, Textual, Polars
</context>

<requirements>

## 1. Directory List Management (ScanScreen)

Replace single directory input with a multi-directory interface:

- Keep the existing Input field for manually adding directories
- Add "Add Directory" button next to input
- Add "Load from Excel" button that opens a file picker or input for Excel path
- Display added directories in a selectable list with checkboxes
- Each directory entry has a checkbox - checked means it will be scanned
- **Auto-select all**: When directories are added (manually or from Excel), they are selected by default
- Add "Select All" button to check all directories
- Add "Deselect All" button to uncheck all directories
- Add "Remove Selected" button to remove checked directories from list
- Add "Clear All" button to remove all directories

When loading from Excel:
- Read column A (first column) as directory paths
- Skip empty rows
- Skip header row if first cell looks like a header (e.g., contains "path", "folder", "directory")
- Validate each path exists before adding to list
- Show count of valid/invalid paths after loading
- All loaded directories are auto-selected (checked)

## 2. Detailed Progress Bars

### ScanScreen Progress
- Show progress as "Scanning directory X of Y" in status
- Update progress bar based on directories completed
- After scanning each directory, show running total of files found
- Final summary shows total files by extension

### ConversionScreen Progress  
- Show "Converting file X of Y: filename.xlsx" in status
- Update progress bar based on files completed (not arbitrary percentages)
- Show "Processing sheet Z of N" for files with multiple sheets
- Log each file completion with sheet count
- Final summary shows total Parquet files generated

## 3. Implementation Details

Use Polars to read the Excel file for directory list:
```python
df = pl.read_excel(excel_path, has_header=False)
directories = df.get_column("column_1").to_list()
```

For progress tracking, modify the @work methods to:
- Calculate total items upfront
- Call progress update after each item
- Pass actual counts, not estimated percentages

The ProgressBar widget accepts `total` and `progress` parameters:
```python
progress_bar.update(total=total_files, progress=completed_files)
```

</requirements>

<implementation>

### ScanScreen Layout Changes

```
Static("Scan for Excel Files")
Label("Add Directory:")
Horizontal(
    Input(id="dir-input"),
    Button("Add", id="btn-add-dir"),
    Button("Load from Excel", id="btn-load-excel"),
)
Label("Directories to scan:")
VerticalScroll(id="dir-list-container")  # Contains checkboxes for each directory
    # Each directory is a Checkbox widget: Checkbox("path/to/dir", id="dir-check-0", value=True)
Horizontal(
    Button("Select All", id="btn-select-all"),
    Button("Deselect All", id="btn-deselect-all"),
    Button("Remove Selected", id="btn-remove"),
    Button("Clear All", id="btn-clear"),
)
Checkbox("Force Rescan", id="rescan-checkbox")
Horizontal(
    Button("Start Scan", variant="primary"),
    Button("Back"),
)
ProgressBar(id="scan-progress")
Static(id="status-label")  # "Scanning directory 2 of 5..."
Static(id="results-summary")
```

### Directory List Implementation

Use Checkbox widgets inside a VerticalScroll container for the directory list:
```python
# Adding a directory
checkbox = Checkbox(directory_path, id=f"dir-check-{index}", value=True)  # Auto-selected
dir_container.mount(checkbox)

# Select All
for checkbox in self.query("Checkbox").results():
    if checkbox.id and checkbox.id.startswith("dir-check-"):
        checkbox.value = True

# Deselect All
for checkbox in self.query("Checkbox").results():
    if checkbox.id and checkbox.id.startswith("dir-check-"):
        checkbox.value = False

# Get selected directories for scanning
selected_dirs = [
    cb.label.plain for cb in self.query("Checkbox").results()
    if cb.id and cb.id.startswith("dir-check-") and cb.value
]
```

### Key Methods to Add/Modify

ScanScreen:
- `add_directory()` - Add directory from input as checked Checkbox
- `load_from_excel()` - Parse Excel, add valid paths as checked Checkboxes
- `select_all()` - Check all directory checkboxes
- `deselect_all()` - Uncheck all directory checkboxes
- `remove_selected()` - Remove checked directories from list
- `clear_directories()` - Clear all directories from list
- `get_selected_directories()` - Return list of checked directory paths
- `run_scan()` - Scan only selected (checked) directories with progress updates

ConversionScreen:
- `run_conversion()` - Modify to track file-by-file progress with actual counts

### State Management

Store directory list in app state so it persists across screen switches:
```python
self.app.scan_directories = []  # List of directory paths to scan
```

</implementation>

<output>
Modify these files:
- `./src/excel_converter/tui.py` - All changes described above

Do NOT create new files. All changes go in the existing tui.py.
</output>

<verification>
After implementation, verify:

1. Manual directory entry still works:
   - Type path in input, click Add, see it in list
   
2. Excel loading works:
   - Create test Excel with paths in column A
   - Load it, verify paths appear in list
   - Invalid paths should be reported but not added

3. Selection controls work:
   - Add directories, verify all are checked by default
   - Click "Deselect All", verify all unchecked
   - Click "Select All", verify all checked
   - Manually toggle individual checkboxes
   - Only checked directories are scanned

4. Progress bars show real counts:
   - Scan multiple directories, see "Directory 1 of 3" progress
   - Convert files, see "File 5 of 20: example.xlsx" progress

5. Run existing tests pass:
   ```bash
   uv run pytest tests/test_tui.py -v
   ```
</verification>

<success_criteria>
- Directory list UI allows add/remove/clear operations
- Excel file with folder paths in column A can be loaded
- Invalid paths are reported, not silently added
- **Directories are auto-selected (checked) when added**
- Select All / Deselect All buttons work correctly
- Individual directory checkboxes can be toggled
- Only checked directories are included in scan
- ScanScreen progress shows directory count progress
- ConversionScreen progress shows file count progress
- Status messages show current item being processed
- All existing TUI functionality preserved
</success_criteria>
