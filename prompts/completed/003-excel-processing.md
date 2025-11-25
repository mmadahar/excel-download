<objective>
Implement `process_excel_files()` - Step 2 of 4 in the Excel-to-Parquet pipeline.

This function reads Excel files from SOV folders, adds metadata columns, and saves each sheet as a UUID-named Parquet file. It consumes Step 1 output and prepares data for storage.
</objective>

<context>
@prompts/001-shared-context.md - Read this first for project architecture and standards.
@excel_to_parquet.py - Contains find_sov_folders() from Step 1.

This step DEPENDS on Step 1 output:
```python
sov_folders = find_sov_folders(['/data'])  # Returns List[Path]
process_excel_files(sov_folders, output_dir)  # This function
```
</context>

<function_signature>
```python
def process_excel_files(sov_folders: List[Path], output_dir: Path) -> None:
```
</function_signature>

<requirements>
1. **Output Directory**
   - Create output_dir if it doesn't exist (including parents)
   - Validate directory is writable before processing begins

2. **Excel File Discovery**
   - Find ALL .xlsx and .xls files in each SOV folder recursively
   - Use Path.rglob() for recursive search
   - Case-insensitive extension matching

3. **Excel Reading - CRITICAL**
   - Use `pd.read_excel()` with `engine='openpyxl'`
   - Read with `header=None` - do NOT assume header rows exist
   - Process ALL sheets in each Excel file
   - Use pd.ExcelFile context manager for efficiency

4. **Metadata Columns - CRITICAL**
   - Add `file_path` column: full path to source Excel file (as string)
   - Add `row_number` column: sequential starting from 0
   - Insert these as the FIRST two columns (index 0, 1)
   - Order: [file_path, row_number, ...original columns...]

5. **Parquet Output**
   - One Parquet file per Excel sheet
   - Filename: `{uuid.uuid4()}.parquet`
   - Save with `index=False`

6. **Error Handling**
   - Per-file try-except (don't stop pipeline on individual failures)
   - Per-sheet try-except (one bad sheet shouldn't skip whole file)
   - Log errors with full context (file path, sheet name, exception)
   - Track and log statistics: files processed, sheets converted, errors
</requirements>

<implementation_pattern>
```python
import logging
import uuid
from pathlib import Path
from typing import List
import pandas as pd

logger = logging.getLogger(__name__)

def process_excel_files(sov_folders: List[Path], output_dir: Path) -> None:
    """
    Process Excel files in SOV folders and convert to Parquet format.

    Each Excel sheet becomes a separate Parquet file with UUID naming.
    Metadata columns (file_path, row_number) are added for data lineage.

    Why this approach:
    - UUID filenames prevent conflicts and enable parallel processing
    - header=None ensures all data captured without structure assumptions
    - Metadata columns enable tracing data back to source files
    - Per-file error handling prevents one bad file from stopping pipeline

    Args:
        sov_folders: List of Path objects from find_sov_folders().
        output_dir: Destination directory for Parquet files.

    Returns:
        None. Creates Parquet files as side effect.
    """
    # Create output directory
    output_dir.mkdir(parents=True, exist_ok=True)
    logger.info(f"Output directory: {output_dir}")

    # Statistics tracking
    files_processed = 0
    sheets_converted = 0
    errors_encountered = 0

    # Find all Excel files
    excel_files = []
    for sov_folder in sov_folders:
        excel_files.extend(sov_folder.rglob('*.xlsx'))
        excel_files.extend(sov_folder.rglob('*.xls'))
        excel_files.extend(sov_folder.rglob('*.XLSX'))
        excel_files.extend(sov_folder.rglob('*.XLS'))

    # Remove duplicates (case-insensitive matching may find same file twice)
    excel_files = list(set(excel_files))
    logger.info(f"Found {len(excel_files)} Excel file(s) to process")

    for excel_file in excel_files:
        try:
            with pd.ExcelFile(excel_file, engine='openpyxl') as xls:
                for sheet_name in xls.sheet_names:
                    try:
                        # Read WITHOUT header assumption
                        df = pd.read_excel(
                            xls,
                            sheet_name=sheet_name,
                            header=None
                        )

                        # Skip empty sheets
                        if df.empty:
                            logger.warning(
                                f"Empty sheet '{sheet_name}' in {excel_file}"
                            )
                            continue

                        # Add metadata columns at the BEGINNING
                        df.insert(0, 'file_path', str(excel_file))
                        df.insert(1, 'row_number', range(len(df)))

                        # Generate UUID filename and save
                        output_file = output_dir / f"{uuid.uuid4()}.parquet"
                        df.to_parquet(output_file, index=False)

                        sheets_converted += 1
                        logger.debug(
                            f"Converted {sheet_name}: {len(df)} rows "
                            f"-> {output_file.name}"
                        )

                    except Exception as sheet_error:
                        errors_encountered += 1
                        logger.error(
                            f"Error processing sheet '{sheet_name}' "
                            f"in {excel_file}: {sheet_error}"
                        )
                        continue

            files_processed += 1

        except Exception as file_error:
            errors_encountered += 1
            logger.error(f"Error processing {excel_file}: {file_error}")
            continue

    # Log summary
    logger.info(
        f"Processing complete: {files_processed} files, "
        f"{sheets_converted} sheets converted, "
        f"{errors_encountered} errors"
    )
```
</implementation_pattern>

<edge_cases>
```python
# Handle these scenarios:

# 1. Empty Excel file (no sheets)
#    -> Log warning, continue to next file

# 2. Empty sheet (0 rows)
#    -> Log warning, skip sheet, process other sheets

# 3. Single column Excel
#    -> Works fine, adds 2 metadata columns

# 4. Large Excel (10k+ rows)
#    -> Process normally, pandas handles memory

# 5. Corrupted Excel file
#    -> Catch exception, log error, continue

# 6. Sheet with special characters: "Data/Sheet!", "Sheet#1"
#    -> Handled by pandas automatically

# 7. Mixed .xlsx and .xls
#    -> Both processed with openpyxl engine
```
</edge_cases>

<common_pitfalls>
- Forgetting `header=None` - causes first row to become column names
- Not creating output_dir - leads to write failures
- Stopping on first error - must use per-file try-except
- Using fixed filenames - MUST use UUID4
- Forgetting metadata columns - file_path and row_number are REQUIRED
- Not using context manager for ExcelFile - can leak file handles
- Not handling empty sheets - check df.empty before processing
</common_pitfalls>

<output>
Edit file: `./excel_to_parquet.py`

Add to existing file (after find_sov_folders):
1. Additional imports (uuid, pandas)
2. Complete process_excel_files() function with docstring
3. Inline comments for complex logic

Preserve the find_sov_folders() function from Step 1.
</output>

<verification>
Before completing, verify:
- [ ] Creates output_dir before processing
- [ ] Finds both .xlsx and .xls files (case-insensitive)
- [ ] Reads Excel with header=None
- [ ] Adds file_path as column 0
- [ ] Adds row_number as column 1
- [ ] row_number starts at 0 and is sequential
- [ ] Uses uuid.uuid4() for all output filenames
- [ ] Handles empty sheets (skip with warning)
- [ ] Per-file error handling (continues on failures)
- [ ] Uses context manager for pd.ExcelFile
- [ ] Logs statistics at completion
- [ ] Has complete type hints and docstring
- [ ] PEP 8 compliant
</verification>

<next_step>
After validation, Step 3 will wire up CLI and main():
```python
# main() will call:
sov_folders = find_sov_folders(args.root_dirs)
process_excel_files(sov_folders, Path(args.output))
```
</next_step>
