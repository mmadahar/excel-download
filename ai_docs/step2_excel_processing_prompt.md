# Step 2: Implement Excel Processing Function (`process_excel_files`)

## Context
You are implementing part of an Excel-to-Parquet conversion pipeline. This is **Step 2 of 4** - implementing the core processing logic that reads Excel files and converts them to Parquet format.

## Full System Context
The complete system:
1. **[Completed]** Find folders with "/SOV/" in path → produces `List[Path]`
2. **[THIS STEP]** Process Excel files in those folders
3. **[Future Step]** Wire up CLI and main function
4. **[Future Step]** Add comprehensive test coverage

## Specific Requirements

### Function Signature
```python
def process_excel_files(sov_folders: List[Path], output_dir: Path) -> None:
```

### Detailed Implementation Requirements

1. **Input Processing**:
   - Accept list of `Path` objects for SOV folders (from Step 1)
   - Accept `Path` object for output directory
   - **Create output directory if it doesn't exist** (including parent dirs)
   - Validate output_dir is writable before processing

2. **File Discovery Within SOV Folders**:
   - Find ALL Excel files (`.xlsx`, `.xls`) in each SOV folder
   - Use case-insensitive extension matching
   - Use `Path.glob('**/*.xlsx')` and `Path.glob('**/*.xls')` for recursive search
   - Log how many Excel files found in each SOV folder

3. **Excel Reading Requirements**:
   - Use `pd.read_excel()` with `engine='openpyxl'`
   - **Critical**: Read with `header=None` (no header row assumed)
   - Read ALL sheets from each Excel file
   - Use `pd.ExcelFile()` context manager to handle multiple sheets efficiently

4. **Data Transformation - CRITICAL**:
   - Add `file_path` column: full path to source Excel file (as string)
   - Add `row_number` column: sequential row number starting from 0
   - These columns should be added BEFORE saving to Parquet
   - Order: [file_path, row_number, ...original columns...]

5. **Parquet File Naming**:
   - Use UUID4 for each output file: `{uuid4()}.parquet`
   - One Parquet file per Excel sheet
   - Format: `str(uuid.uuid4()) + '.parquet'`
   - No relationship preserved between filename and source (intentional anonymization)

6. **Error Handling Strategy**:
   - Wrap each file processing in try-except
   - Log errors with file path, sheet name, and exception details
   - **Continue processing remaining files** if one fails
   - Track statistics: files processed, sheets converted, errors encountered
   - Return summary statistics via logging at INFO level

7. **Logging Requirements**:
   - `logger.info()`: Start processing folder, file counts, completion summary
   - `logger.warning()`: Empty sheets, zero-row DataFrames
   - `logger.error()`: File read failures, write failures, unexpected errors
   - Include context: file path, sheet name, row count

### Critical Success Criteria

Your implementation must:
- ✅ Create output_dir before any processing
- ✅ Read Excel with `header=None` (no automatic header detection)
- ✅ Add `file_path` and `row_number` columns to EVERY DataFrame
- ✅ Use UUID4 for all output filenames
- ✅ Handle multi-sheet Excel files correctly
- ✅ Continue on errors (don't crash entire pipeline)
- ✅ Log meaningful error messages with context
- ✅ Handle empty sheets gracefully
- ✅ Use context managers for file handles

### Common Pitfalls to Avoid

❌ **DON'T** assume Excel files have headers - use `header=None`
❌ **DON'T** forget to create output_dir - this will cause write failures
❌ **DON'T** stop processing if one file fails - use try-except per file
❌ **DON'T** use fixed filenames - must use UUID4
❌ **DON'T** forget to add metadata columns (file_path, row_number)
❌ **DON'T** assume all sheets have data - handle empty DataFrames
❌ **DON'T** leak file handles - use context managers
❌ **DON'T** assume write permissions - catch IOError
❌ **DON'T** forget to handle both .xlsx and .xls extensions

### Edge Cases to Handle

```python
# Empty Excel file (no sheets) - log warning, continue
# Empty sheet (0 rows) - log warning, skip sheet
# Single column Excel - should work fine
# Very large Excel (10k+ rows) - should handle memory efficiently
# Corrupted Excel file - catch exception, log, continue
# Read-only output directory - catch exception, log, fail gracefully
# Sheet with special characters in name - handle encoding
```

### Code Structure Template

```python
import logging
import uuid
from pathlib import Path
from typing import List
import pandas as pd

logger = logging.getLogger(__name__)

def process_excel_files(sov_folders: List[Path], output_dir: Path) -> None:
    """
    Process all Excel files in SOV folders and convert to Parquet format.
    
    This function recursively searches for Excel files (.xlsx, .xls) within
    the provided SOV folders, reads each sheet with pandas, adds metadata
    columns (file_path, row_number), and saves each sheet as a separate
    Parquet file with a UUID filename.
    
    Why this approach:
    - UUID filenames prevent conflicts and enable parallel processing
    - header=None ensures we capture all data without assuming structure
    - Metadata columns enable tracing data back to source files
    - Per-file error handling prevents one bad file from stopping entire pipeline
    - Parquet format provides compression and fast columnar access
    
    Args:
        sov_folders: List of Path objects representing folders to search
                    for Excel files. Typically output from find_sov_folders().
        output_dir: Path object for directory where Parquet files will be saved.
                   Will be created if it doesn't exist.
    
    Returns:
        None. Side effects: Creates Parquet files in output_dir.
    
    Raises:
        OSError: If output_dir cannot be created or written to.
    
    Example:
        >>> sov_folders = [Path('/data/SOV/project1')]
        >>> output_dir = Path('/output/parquet')
        >>> process_excel_files(sov_folders, output_dir)
        # Creates /output/parquet/abc-123-def.parquet, etc.
    """
    
    # TODO: Create output directory
    # TODO: Initialize counters
    # TODO: Iterate through each SOV folder
    # TODO: Find all Excel files (.xlsx and .xls)
    # TODO: For each Excel file:
    #       - Open with pd.ExcelFile context manager
    #       - Iterate through sheets
    #       - Read with header=None
    #       - Add file_path column
    #       - Add row_number column
    #       - Generate UUID filename
    #       - Save as Parquet
    #       - Handle all exceptions per file
    # TODO: Log summary statistics
    
    pass
```

### Detailed Implementation Guidance

#### 1. Output Directory Creation
```python
# Create output directory with parents, exist_ok to avoid errors
output_dir.mkdir(parents=True, exist_ok=True)
logger.info(f"Output directory ready: {output_dir}")
```

#### 2. Excel File Discovery
```python
# Search for both extensions recursively
excel_files = []
for sov_folder in sov_folders:
    excel_files.extend(sov_folder.rglob('*.xlsx'))
    excel_files.extend(sov_folder.rglob('*.xls'))
    # Consider case-insensitive matching on case-sensitive filesystems
```

#### 3. Multi-Sheet Processing Pattern
```python
try:
    with pd.ExcelFile(excel_file, engine='openpyxl') as xls:
        sheet_names = xls.sheet_names
        for sheet_name in sheet_names:
            try:
                # Read sheet with no header assumption
                df = pd.read_excel(xls, sheet_name=sheet_name, header=None)
                
                # Handle empty sheets
                if df.empty:
                    logger.warning(f"Empty sheet '{sheet_name}' in {excel_file}")
                    continue
                
                # Add metadata columns AT THE BEGINNING
                df.insert(0, 'file_path', str(excel_file))
                df.insert(1, 'row_number', range(len(df)))
                
                # Generate UUID filename
                output_file = output_dir / f"{uuid.uuid4()}.parquet"
                
                # Save as Parquet
                df.to_parquet(output_file, index=False)
                
                logger.debug(f"Converted {sheet_name}: {len(df)} rows -> {output_file.name}")
                
            except Exception as sheet_error:
                logger.error(f"Error processing sheet '{sheet_name}' in {excel_file}: {sheet_error}")
                continue  # Continue with next sheet
                
except Exception as file_error:
    logger.error(f"Error processing file {excel_file}: {file_error}")
    continue  # Continue with next file
```

#### 4. Statistics Tracking
```python
# Initialize at function start
files_processed = 0
sheets_converted = 0
errors_encountered = 0

# Update throughout processing
# Log summary at end:
logger.info(f"Processing complete: {files_processed} files, {sheets_converted} sheets converted, {errors_encountered} errors")
```

### Exception Types to Handle Specifically

```python
# File not found (unlikely but possible with race conditions)
except FileNotFoundError as e:
    logger.error(f"File not found: {excel_file} - {e}")

# Corrupted Excel file
except pd.errors.ExcelFileError as e:
    logger.error(f"Invalid Excel file: {excel_file} - {e}")

# Permission errors
except PermissionError as e:
    logger.error(f"Permission denied: {excel_file} - {e}")

# Write errors
except IOError as e:
    logger.error(f"Failed to write Parquet: {output_file} - {e}")

# Catch-all for unexpected errors
except Exception as e:
    logger.error(f"Unexpected error processing {excel_file}: {type(e).__name__} - {e}")
```

### Memory Efficiency Considerations

For large Excel files:
```python
# Option 1: Process in chunks (if needed)
# Option 2: Use read_excel with chunksize parameter (not applicable here)
# Option 3: Monitor memory usage and log warnings

# Current approach is fine for typical Excel files (<100MB)
# If memory becomes an issue, consider processing sheets one at a time
# and explicitly calling df = None, gc.collect() between sheets
```

### Testing Considerations for Step 4

When writing tests later, consider:
- Mock Excel file with 2 sheets, verify 2 Parquet files created
- Verify metadata columns present and correct
- Verify UUID filenames are unique
- Test with empty sheet (should skip)
- Test with corrupted Excel (should log error, continue)
- Test with non-existent output_dir (should create)
- Verify header=None works correctly

## Validation Checklist

Before considering this step complete:

- [ ] Function has complete type hints and docstring
- [ ] Creates output_dir before processing
- [ ] Handles both .xlsx and .xls files
- [ ] Reads Excel with header=None
- [ ] Adds file_path column (as first column)
- [ ] Adds row_number column (as second column)
- [ ] Uses uuid.uuid4() for filenames
- [ ] Handles empty sheets gracefully
- [ ] Per-file error handling (doesn't crash pipeline)
- [ ] Comprehensive logging at all levels
- [ ] Uses context manager for pd.ExcelFile
- [ ] Logs summary statistics at completion
- [ ] PEP 8 compliant

## Output Format

Provide:
1. Complete function implementation with docstring
2. All necessary imports
3. Logger initialization
4. Inline comments for complex logic
5. Example usage snippet
6. Brief explanation of design decisions (why UUID, why metadata columns, etc.)

## Integration Note

This function will be called from `main()` in Step 3:
```python
sov_folders = find_sov_folders(args.root_dirs)
process_excel_files(sov_folders, args.output_dir)
```

Ensure the function signature and behavior align with this integration plan.
