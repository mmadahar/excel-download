<objective>
Modify `process_excel_files()` in `excel_to_parquet.py` to:
1. Transform the `column` column by removing the "column_" prefix and converting to an integer
2. Parallelize file processing using ThreadPoolExecutor for improved performance
</objective>

<context>
Read @excel_to_parquet.py to understand the current implementation.

The `process_excel_files()` function currently:
- Iterates through Excel files from `data/files.csv` sequentially
- For each file, reads all sheets and unpivots them to long format
- The `column` column contains values like `column_1`, `column_2`, etc. (from Polars auto-generated column names)
- Saves each sheet as a separate Parquet file with UUID naming

The output schema should change from:
```
file_path (str), file_name (str), worksheet (str), row (int), column (str), value (str)
```
To:
```
file_path (str), file_name (str), worksheet (str), row (int), column (int), value (str)
```

Where `column` is now an integer representing the column number (1, 2, 3, etc.).
</context>

<requirements>
1. **Column transformation**: In the `result` select block, transform the `column` column:
   - Use `pl.col("column").str.replace("column_", "").cast(pl.Int64)` to strip the prefix and convert to integer
   - Column numbering should be 1-based (column_1 → 1, column_2 → 2)

2. **Parallel processing**: Refactor to process files in parallel:
   - Extract the per-file processing logic into a helper function (e.g., `_process_single_file()`)
   - Use `ThreadPoolExecutor` with `as_completed()` pattern (already imported)
   - Allow configurable `max_workers` parameter (default: None, which uses system default)
   - Maintain thread-safe statistics tracking using atomic operations or locks
   - Preserve all existing error handling and logging
   - Keep the skip logic for already-processed files
</requirements>

<implementation>
1. Create a helper function `_process_single_file(file_path: Path, output_dir: Path) -> dict`:
   - Move the try/except block for file processing into this function
   - Return a dict with statistics: `{"sheets": int, "rows": int, "errors": int}`
   - Handle all exceptions within the function and log them

2. Modify `process_excel_files()`:
   - Filter files to process (exclude already-processed) before parallelization
   - Submit all file processing tasks to ThreadPoolExecutor
   - Collect results using `as_completed()` and aggregate statistics
   - Keep the final summary logging

3. Update the Polars select to transform the column:
   ```python
   pl.col("column").str.replace("column_", "").cast(pl.Int64).alias("column"),
   ```

4. Update CLAUDE.md Output Schema section to reflect the new column type (int instead of str)
</implementation>

<verification>
After implementing, verify:
1. Run `uv run python excel_to_parquet.py /path/to/test -o /tmp/output` with test data
2. Check a resulting Parquet file to confirm `column` is now Int64 type with numeric values
3. Verify parallel processing works by checking logs show concurrent file processing
4. Ensure error handling still works by testing with a corrupted/unreadable file
</verification>

<success_criteria>
- The `column` column in output Parquet files contains integers (1, 2, 3, ...) not strings ("column_1", ...)
- File processing runs in parallel using ThreadPoolExecutor
- All existing functionality preserved: skip logic, error handling, logging, statistics
- CLAUDE.md updated to reflect new schema
</success_criteria>
