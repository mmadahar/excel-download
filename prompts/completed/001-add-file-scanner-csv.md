<objective>
Add a file scanner that discovers Excel files and saves them to a CSV file, with a CLI flag to force rescanning.

This creates the foundation for tracking which files have been processed and enables idempotent processing in subsequent updates.
</objective>

<context>
This is an Excel-to-Parquet conversion tool. Currently it processes Excel files directly from SOV folders.

We need to add a scanning phase that:
1. Discovers all Excel files first
2. Saves the file list to CSV for tracking
3. Allows rescanning via CLI flag

Read the existing codebase:
@excel_to_parquet.py
@CLAUDE.md
</context>

<requirements>
1. **File Discovery**: Scan directories for Excel files with extensions: `.xlsx`, `.xlsm`, `.xlsb`, `.xls` (case-insensitive)

2. **CSV Output**: Save discovered files to `data/files.csv` with columns:
   - `file_path` - absolute path to Excel file
   - `extension` - file extension (lowercase, with dot)
   - `discovered_at` - ISO timestamp when discovered

3. **CLI Arguments**: Add to existing argparse:
   - `--rescan` or `-r` flag: Force rescan even if CSV exists
   - Default behavior: Use existing CSV if present, otherwise scan

4. **Directory Handling**: Create `data/` directory if it doesn't exist

5. **Integration**: The scan should happen before processing, populating the file list that will be processed
</requirements>

<implementation>
Use pathlib for file operations. Use Polars for CSV read/write.

```python
# Extension filter pattern
EXCEL_EXTENSIONS = {'.xlsx', '.xlsm', '.xlsb', '.xls'}

# CSV path
FILES_CSV = Path('data/files.csv')
```

Steps:
1. Add `--rescan` argument to argparse
2. Create `scan_for_excel_files(root_dirs: list[Path]) -> pl.DataFrame` function
3. Create `load_or_scan_files(root_dirs, rescan: bool) -> pl.DataFrame` function
4. Update main() to use the file list from CSV/scan
</implementation>

<output>
Modify:
- `./excel_to_parquet.py` - Add scanning functionality and CLI args

Create if needed:
- `./data/` directory (via code, not manually)
</output>

<verification>
After implementation, verify:
1. Running without `--rescan` creates CSV on first run
2. Running again without `--rescan` reuses existing CSV (check timestamps)
3. Running with `--rescan` overwrites CSV with fresh scan
4. CSV contains only Excel files with correct extensions
5. Extensions are properly normalized (lowercase, with dot)
</verification>

<success_criteria>
- [ ] `--rescan` / `-r` flag added to CLI
- [ ] `data/files.csv` created with correct schema
- [ ] Only Excel files (.xlsx, .xlsm, .xlsb, .xls) are included
- [ ] Existing CSV is reused unless `--rescan` is specified
- [ ] Code integrates cleanly with existing SOV folder logic
</success_criteria>
