# Polars Excel Multi-Sheet Download and Unpivot Guide

This guide explains how to download all sheets from an Excel workbook using Polars, with proper engine selection for different Excel formats, and unpivot the data to a normalized long format.

## Table of Contents

1. [Overview](#overview)
2. [Engine Selection](#engine-selection)
3. [Reading All Sheets](#reading-all-sheets)
4. [Unpivoting to Long Format](#unpivoting-to-long-format)
5. [Complete Implementation](#complete-implementation)
6. [Output Schema](#output-schema)
7. [Usage Examples](#usage-examples)

## Overview

The goal is to:
1. Read all sheets from an Excel workbook (returns a dict of DataFrames)
2. Unpivot each sheet to a normalized long format
3. Save to Parquet with UUID-based filenames

### Output Schema

```
file_path   - Full absolute path to source Excel file (text)
file_name   - Basename of the Excel file (text)
worksheet   - Name of the worksheet (text)
row         - Row number, 0-indexed (integer)
column      - Column name like column_1, column_2 (text)
value       - Cell value converted to text (text)
```

## Engine Selection

Polars supports multiple engines for reading Excel files. Each engine handles different file formats:

| Extension | Format | Engine | Notes |
|-----------|--------|--------|-------|
| `.xlsx` | Excel 2007+ | `openpyxl` | Modern XML-based format |
| `.xlsm` | Excel Macro-enabled | `openpyxl` | Same as xlsx with macros |
| `.xlsb` | Excel Binary | `calamine` | Fast binary format (pyxlsb alternative) |
| `.xls` | Excel 97-2003 | `calamine` | Legacy format (xlrd backend) |

### Engine Selection Code

```python
def get_engine_for_extension(file_path: Path) -> str:
    """Determine the appropriate engine for the Excel file extension."""
    suffix = file_path.suffix.lower()

    engine_map = {
        '.xlsx': 'openpyxl',
        '.xlsm': 'openpyxl',
        '.xlsb': 'calamine',   # Binary workbooks
        '.xls': 'calamine',    # Legacy format
    }

    return engine_map.get(suffix, 'calamine')
```

### Available Engines in Polars

1. **calamine** (default): Rust-based engine using fastexcel. Fastest option, supports xlsx, xlsb, xls, ods.
2. **openpyxl**: Python library for xlsx/xlsm files. Slower but provides fallback if calamine fails.
3. **xlsx2csv**: Converts to CSV first, then parses. Useful for specific CSV parsing options.

## Reading All Sheets

Use `sheet_id=0` to load all sheets as a dictionary:

```python
import polars as pl
from pathlib import Path

def read_all_sheets(file_path: Path) -> dict[str, pl.DataFrame]:
    """Read all sheets from an Excel workbook into a dict of DataFrames."""

    engine = get_engine_for_extension(file_path)

    # sheet_id=0 returns all sheets as {sheet_name: DataFrame}
    sheets_dict = pl.read_excel(
        source=file_path,
        sheet_id=0,              # Load ALL sheets
        engine=engine,
        has_header=False,        # Treat first row as data, not headers
        raise_if_empty=False,    # Don't raise on empty sheets
    )

    return sheets_dict
```

### Key Parameters

- `sheet_id=0`: Magic value that loads all sheets, returns dict
- `sheet_name`: Alternative to sheet_id, accepts list of names
- `has_header=False`: Auto-generates column names (column_1, column_2, etc.)
- `raise_if_empty=False`: Returns empty DataFrame instead of raising error
- `drop_empty_rows=True`: (default) Removes empty rows
- `drop_empty_cols=True`: (default) Removes empty columns

## Unpivoting to Long Format

Polars provides the `.unpivot()` method (formerly `.melt()`) to convert wide data to long format:

```python
def unpivot_dataframe(
    df: pl.DataFrame,
    file_path: str,
    file_name: str,
    worksheet: str
) -> pl.DataFrame:
    """Unpivot a DataFrame to long format with metadata columns."""

    if df.is_empty():
        # Return empty DataFrame with correct schema
        return pl.DataFrame({
            'file_path': pl.Series([], dtype=pl.Utf8),
            'file_name': pl.Series([], dtype=pl.Utf8),
            'worksheet': pl.Series([], dtype=pl.Utf8),
            'row': pl.Series([], dtype=pl.Int64),
            'column': pl.Series([], dtype=pl.Utf8),
            'value': pl.Series([], dtype=pl.Utf8),
        })

    # Add row number column (0-indexed)
    df_with_row = df.with_row_index(name='row')

    # Get all original column names (excluding 'row')
    value_columns = [col for col in df_with_row.columns if col != 'row']

    # Unpivot: wide to long format
    unpivoted = df_with_row.unpivot(
        on=value_columns,        # Columns to unpivot
        index='row',             # Keep as identifier
        variable_name='column',  # New column for original column names
        value_name='value'       # New column for cell values
    )

    # Add metadata and cast value to string
    result = unpivoted.select([
        pl.lit(file_path).alias('file_path'),
        pl.lit(file_name).alias('file_name'),
        pl.lit(worksheet).alias('worksheet'),
        pl.col('row'),
        pl.col('column'),
        pl.col('value').cast(pl.Utf8).alias('value'),
    ])

    return result
```

### Understanding .unpivot()

The `unpivot()` method transforms data from wide to long format:

**Wide format (input):**
| row | column_1 | column_2 | column_3 |
|-----|----------|----------|----------|
| 0   | A        | B        | C        |
| 1   | D        | E        | F        |

**Long format (output):**
| row | column   | value |
|-----|----------|-------|
| 0   | column_1 | A     |
| 0   | column_2 | B     |
| 0   | column_3 | C     |
| 1   | column_1 | D     |
| 1   | column_2 | E     |
| 1   | column_3 | F     |

### Parameters

- `on`: Columns to unpivot (default: all except index columns)
- `index`: Column(s) to keep as identifiers
- `variable_name`: Name for the new column containing original column names
- `value_name`: Name for the new column containing cell values

## Complete Implementation

See `excel_to_parquet_polars.py` for the full implementation including:
- CLI argument parsing
- Logging configuration
- Error handling
- UUID filename generation
- Parquet output

### Core Processing Function

```python
import uuid
from pathlib import Path

def process_excel_file(file_path: Path, output_dir: Path) -> dict:
    """Process a single Excel file: read, unpivot, save to Parquet."""

    stats = {'sheets_processed': 0, 'rows_written': 0, 'errors': 0}

    sheets_dict = read_all_sheets(file_path)
    file_path_str = str(file_path.resolve())
    file_name = file_path.name

    for sheet_name, df in sheets_dict.items():
        try:
            unpivoted_df = unpivot_dataframe(
                df=df,
                file_path=file_path_str,
                file_name=file_name,
                worksheet=sheet_name
            )

            if not unpivoted_df.is_empty():
                output_filename = f"{uuid.uuid4()}.parquet"
                output_path = output_dir / output_filename
                unpivoted_df.write_parquet(output_path)

                stats['sheets_processed'] += 1
                stats['rows_written'] += len(unpivoted_df)

        except Exception as e:
            stats['errors'] += 1

    return stats
```

## Output Schema

The final Parquet files have this schema:

```python
schema = {
    'file_path': pl.Utf8,   # "/absolute/path/to/workbook.xlsx"
    'file_name': pl.Utf8,   # "workbook.xlsx"
    'worksheet': pl.Utf8,   # "Sheet1"
    'row': pl.Int64,        # 0, 1, 2, ...
    'column': pl.Utf8,      # "column_1", "column_2", ...
    'value': pl.Utf8,       # Cell value as text
}
```

### Reading the Output

```python
# Read all Parquet files from output directory
df = pl.read_parquet("/output/parquet/*.parquet")

# Filter by file or worksheet
filtered = df.filter(
    (pl.col('file_name') == 'data.xlsx') &
    (pl.col('worksheet') == 'Sheet1')
)

# Pivot back to wide format if needed
wide = filtered.pivot(
    values='value',
    index='row',
    on='column'
)
```

## Usage Examples

### Command Line

```bash
# Single file
uv run python excel_to_parquet_polars.py input.xlsx --output ./output

# Multiple files
uv run python excel_to_parquet_polars.py data1.xlsx data2.xls -o ./output

# With glob pattern (shell expansion)
uv run python excel_to_parquet_polars.py /data/*.xlsx -o ./output

# Debug logging
uv run python excel_to_parquet_polars.py input.xlsx -o ./output -l DEBUG

# With log file
uv run python excel_to_parquet_polars.py input.xlsx -o ./output --log-file convert.log
```

### Python API

```python
from pathlib import Path
from excel_to_parquet_polars import (
    read_all_sheets,
    unpivot_dataframe,
    process_excel_file
)

# Read all sheets from a workbook
sheets = read_all_sheets(Path("workbook.xlsx"))
for name, df in sheets.items():
    print(f"Sheet: {name}, Shape: {df.shape}")

# Process and save to Parquet
output_dir = Path("./output")
output_dir.mkdir(exist_ok=True)
stats = process_excel_file(Path("workbook.xlsx"), output_dir)
print(f"Processed {stats['sheets_processed']} sheets, {stats['rows_written']} rows")
```

## Dependencies

Add these to your project with:

```bash
uv add polars openpyxl xlrd pyxlsb
```

Or in `pyproject.toml`:

```toml
dependencies = [
    "polars>=1.0.0",
    "openpyxl>=3.1.0",
    "xlrd>=2.0.0",
    "pyxlsb>=1.0.0",
]
```

### Engine Dependencies

- **calamine** (default): Built into Polars via fastexcel, no extra install
- **openpyxl**: `uv add openpyxl` for xlsx/xlsm support
- **xlrd**: `uv add xlrd` for legacy xls files
- **pyxlsb**: `uv add pyxlsb` for xlsb binary files (calamine alternative)

## Performance Considerations

1. **Use calamine when possible**: It's significantly faster than openpyxl
2. **Memory**: Unpivoting creates rows × columns entries - large sheets can expand significantly
3. **Parquet compression**: Default snappy compression provides good balance
4. **Streaming**: For very large files, consider processing sheets in chunks

## Error Handling

The implementation includes:
- Per-file error handling (continues if one file fails)
- Per-sheet error handling (continues if one sheet fails)
- Empty sheet detection and skipping
- Missing file validation before processing
- Detailed logging at configurable levels

## References

- [Polars read_excel documentation](https://docs.pola.rs/py-polars/html/reference/api/polars.read_excel.html)
- [Polars DataFrame.unpivot documentation](https://docs.pola.rs/api/python/dev/reference/dataframe/api/polars.DataFrame.unpivot.html)
- [Polars User Guide - Excel](https://docs.pola.rs/user-guide/io/excel/)
