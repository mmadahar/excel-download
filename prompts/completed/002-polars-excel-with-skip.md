<objective>
Update the Excel processing to use Polars with the correct engine per file type, and skip files that have already been processed to Parquet.

This makes processing idempotent - running the tool multiple times won't reprocess files unnecessarily.
</objective>

<context>
The codebase now has file scanning that saves Excel files to `data/files.csv`.

We need to update the Excel reading and add skip logic for already-processed files.

Read these files for implementation guidance:
@ai_docs/2025-11-26-091923_polars_excel_unpivot_guide.md
@excel_to_parquet.py
@CLAUDE.md
</context>

<requirements>
1. **Engine Selection by Extension**:
   - `.xlsx` and `.xlsm` -> `openpyxl` engine
   - `.xlsb` -> `pyxlsb` engine
   - `.xls` -> `xlrd` engine

2. **Polars Excel Reading**: Use `pl.read_excel()` with:
   - `sheet_id=0` to read all sheets as dict
   - `has_header=False` to treat first row as data
   - Correct engine per extension

3. **Skip Already-Processed Files**:
   - Before processing a file, check if its `file_path` already exists in any Parquet file in the output directory
   - If found, skip that file and log it
   - Use Polars to scan Parquet files efficiently: `pl.scan_parquet("output/*.parquet")`

4. **Unpivot to Long Format**: Transform each sheet to:
   - `file_path` - absolute path to source Excel
   - `file_name` - basename of Excel file
   - `worksheet` - sheet name
   - `row` - 0-indexed row number
   - `column` - column name (column_1, column_2, etc.)
   - `value` - cell value as string

5. **Dependencies**: Add required packages:
   - `polars`
   - `openpyxl` (for xlsx/xlsm)
   - `pyxlsb` (for xlsb)
   - `xlrd` (for xls)
</requirements>

<implementation>
Follow the patterns from the Polars guide:

```python
def get_engine_for_extension(file_path: Path) -> str:
    """Determine the appropriate engine for the Excel file extension."""
    suffix = file_path.suffix.lower()
    engine_map = {
        '.xlsx': 'openpyxl',
        '.xlsm': 'openpyxl',
        '.xlsb': 'pyxlsb',
        '.xls': 'xlrd',
    }
    return engine_map.get(suffix, 'openpyxl')
```

For skip logic:
```python
def get_processed_file_paths(output_dir: Path) -> set[str]:
    """Get set of file paths already in Parquet files."""
    parquet_pattern = str(output_dir / "*.parquet")
    try:
        df = pl.scan_parquet(parquet_pattern).select("file_path").unique().collect()
        return set(df["file_path"].to_list())
    except Exception:
        return set()  # No parquet files yet
```

Key points:
- Replace pandas with polars throughout
- Use `with_row_index()` for row numbers
- Use `unpivot()` for wide-to-long transformation
- Cast all values to string with `.cast(pl.Utf8)`
</implementation>

<output>
Modify:
- `./excel_to_parquet.py` - Update to use Polars with correct engines
- `./pyproject.toml` - Add dependencies if not present

Run after changes:
!uv add polars openpyxl pyxlsb xlrd
</output>

<verification>
Test the implementation:
1. Process a mix of .xlsx, .xlsm, .xlsb, .xls files
2. Verify Parquet output has correct schema (6 columns)
3. Run again - files should be skipped (check logs)
4. Add new Excel file - only new file should be processed
5. Verify row numbers are 0-indexed
6. Verify values are all strings
</verification>

<success_criteria>
- [ ] Correct engine used for each extension type
- [ ] Polars used instead of pandas for Excel reading
- [ ] Output schema matches: file_path, file_name, worksheet, row, column, value
- [ ] Files already in Parquet are skipped on subsequent runs
- [ ] All required dependencies added to pyproject.toml
- [ ] Logging indicates which files are skipped vs processed
</success_criteria>
