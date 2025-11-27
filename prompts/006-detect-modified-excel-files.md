<objective>
Update the Excel-to-Parquet conversion tool to detect and re-process modified Excel files during rescan.

Currently, rescan only adds new files. After this change:
1. New Excel files → converted to Parquet (existing behavior)
2. Modified Excel files → new Parquet created (keeping history)
3. Unchanged Excel files → skipped (existing behavior)
</objective>

<context>
Read CLAUDE.md for project conventions.

Key files to examine:
- `excel_to_parquet.py` - Main CLI with `scan_for_excel_files()`, `load_or_scan_files()`, `get_processed_file_paths()`, `process_excel_files()`
- `data/files.csv` - Cached file registry (file_path, extension, discovered_at)

Current flow:
1. `scan_for_excel_files()` discovers Excel files, saves to `files.csv`
2. `get_processed_file_paths()` reads existing Parquet files and extracts unique `file_path` values
3. `process_excel_files()` skips files where `file_path in processed_paths`

Problem: The skip logic only checks if `file_path` exists in any Parquet - it doesn't detect if the source Excel was modified since last conversion.
</context>

<requirements>
1. **Detection method**: Use both timestamp AND hash for reliable change detection
   - Quick check: Compare file's OS modification time against stored `modified_at`
   - Confirmation: If timestamp differs, compute file hash and compare against stored `file_hash`
   - WHY both: Timestamps can change without content changes (copy/backup restore); hash confirms actual changes

2. **Tracking in files.csv**: Add columns to track file state
   - `modified_at` (str): ISO 8601 timestamp of file's last modification time from OS
   - `file_hash` (str): MD5 or SHA256 hash of file contents
   - Update `scan_for_excel_files()` to capture these values
   - On rescan, compare current values against stored values

3. **Tracking in Parquet**: Add column for audit trail
   - `source_modified_at` (str): ISO 8601 timestamp of when source Excel was last modified
   - This enables queries like "SELECT * FROM parquet WHERE source_modified_at = (SELECT MAX(source_modified_at) FROM parquet WHERE file_path = X)"

4. **History preservation**: When re-processing a modified file
   - Do NOT delete existing Parquet files
   - Create new Parquet file(s) with new UUID(s)
   - The `source_modified_at` column differentiates versions

5. **Skip logic update**: Modify `process_excel_files()` to:
   - Skip files where file_path exists in Parquet AND file_hash matches files.csv AND modified_at matches
   - Re-process files where file_path exists but hash/timestamp indicates changes
   - Process new files as before
</requirements>

<implementation>
1. Add helper function for file hashing:
   ```python
   def get_file_hash(file_path: Path) -> str:
       """Compute hash of file contents for change detection."""
       # Use hashlib, read in chunks for large files
   ```

2. Update `scan_for_excel_files()`:
   - Add `modified_at` from `os.path.getmtime()` converted to ISO format
   - Add `file_hash` from new helper function
   - Return DataFrame with new columns

3. Update `_process_single_file()`:
   - Accept `source_modified_at` parameter
   - Include in the result DataFrame select statement

4. Update `process_excel_files()`:
   - Load files.csv with new columns
   - Compare against Parquet metadata to determine which files need processing
   - Pass `source_modified_at` to `_process_single_file()`

5. Update `get_processed_file_paths()` to return more than just paths:
   - Return dict mapping file_path → latest source_modified_at from Parquet
   - Or return set of (file_path, source_modified_at) tuples
</implementation>

<constraints>
- Maintain backward compatibility: Existing Parquet files without `source_modified_at` should still work
- Existing files.csv without new columns should trigger a rescan (or handle gracefully)
- Hash computation should use chunked reading for memory efficiency with large Excel files
- Keep the parallel processing architecture intact
</constraints>

<output>
Modify these files:
- `./excel_to_parquet.py` - Add hash function, update scan/process functions, add new columns
- `./data/files.csv` - Will be regenerated with new schema on next scan

No new files needed.
</output>

<verification>
Before declaring complete:
1. Run `uv run python excel_to_parquet.py /path/to/test --rescan -o /tmp/output` on a folder with Excel files
2. Verify files.csv contains `modified_at` and `file_hash` columns
3. Verify Parquet files contain `source_modified_at` column
4. Modify an Excel file's content (change a cell value)
5. Run rescan again
6. Verify:
   - New Parquet file(s) created for modified Excel
   - Old Parquet file(s) still exist
   - `source_modified_at` differs between old and new Parquet files
7. Run rescan a third time without changes - verify no new Parquet files created
</verification>

<success_criteria>
- New Excel files are converted (existing behavior preserved)
- Modified Excel files create new Parquet files (history preserved)
- Unchanged Excel files are skipped (no duplicate work)
- files.csv tracks modification state with timestamp + hash
- Parquet files include source_modified_at for version querying
- All existing tests still pass
</success_criteria>
