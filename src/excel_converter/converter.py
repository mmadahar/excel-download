#!/usr/bin/env python3
"""
Excel to Parquet Conversion Script using Polars

Downloads all sheets from Excel workbooks and unpivots them to a normalized
long format with the schema: file_path, file_name, worksheet, row, column, value

Engine selection:
- xlsx, xlsm: openpyxl engine
- xlsb: pyxlsb engine (calamine also supports)
- xls: xlrd engine

Usage:
    uv run python excel_to_parquet_polars.py input.xlsx --output /output/parquet
    uv run python excel_to_parquet_polars.py /data/*.xlsx -o /out
"""

import argparse
import logging
import sys
import uuid
from pathlib import Path
from typing import Dict, List, Optional

import polars as pl

# Exit code constants
EXIT_SUCCESS = 0
EXIT_USER_ERROR = 1
EXIT_PROCESSING_ERROR = 2
EXIT_UNEXPECTED_ERROR = 3

# Initialize module-level logger
logger = logging.getLogger(__name__)


def get_engine_for_extension(file_path: Path) -> str:
    """
    Determine the appropriate engine for the given Excel file extension.

    Args:
        file_path: Path to the Excel file

    Returns:
        Engine name string for polars.read_excel()

    Engine mapping:
    - .xlsx, .xlsm: openpyxl (full support for modern Excel formats)
    - .xlsb: calamine (Rust-based, fast binary format support)
    - .xls: xlrd (legacy Excel 97-2003 format)
    """
    suffix = file_path.suffix.lower()

    engine_map = {
        '.xlsx': 'openpyxl',
        '.xlsm': 'openpyxl',  # Macro-enabled workbooks
        '.xlsb': 'calamine',   # Binary workbooks (pyxlsb alternative)
        '.xls': 'calamine',    # Legacy format - calamine supports via xlrd backend
    }

    engine = engine_map.get(suffix, 'calamine')
    logger.debug(f"Selected engine '{engine}' for extension '{suffix}'")
    return engine


def read_all_sheets(file_path: Path) -> Dict[str, pl.DataFrame]:
    """
    Read all sheets from an Excel workbook into a dictionary of DataFrames.

    Args:
        file_path: Path to the Excel file

    Returns:
        Dictionary mapping sheet names to polars DataFrames

    Notes:
        - Uses sheet_id=0 to load all sheets
        - has_header=False treats first row as data, not column names
        - Columns are auto-named as column_1, column_2, etc.
    """
    engine = get_engine_for_extension(file_path)

    logger.info(f"Reading all sheets from {file_path} using engine '{engine}'")

    try:
        # sheet_id=0 returns all sheets as dict {sheet_name: DataFrame}
        sheets_dict = pl.read_excel(
            source=file_path,
            sheet_id=0,  # Load ALL sheets
            engine=engine,
            has_header=False,  # Treat first row as data
            raise_if_empty=False,  # Don't raise on empty sheets
        )

        logger.info(f"Found {len(sheets_dict)} sheet(s): {list(sheets_dict.keys())}")
        return sheets_dict

    except Exception as e:
        logger.error(f"Error reading {file_path}: {e}")
        raise


def unpivot_dataframe(
    df: pl.DataFrame,
    file_path: str,
    file_name: str,
    worksheet: str
) -> pl.DataFrame:
    """
    Unpivot a DataFrame to long format with metadata columns.

    Transforms wide-format data into a normalized schema:
    file_path, file_name, worksheet, row, column, value

    Args:
        df: Input DataFrame with columns like column_1, column_2, etc.
        file_path: Full path to the source Excel file
        file_name: Basename of the Excel file
        worksheet: Name of the worksheet

    Returns:
        DataFrame in long format with all values as text
    """
    if df.is_empty():
        logger.warning(f"Empty DataFrame for sheet '{worksheet}'")
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

    # Get all original column names (excluding our new 'row' column)
    value_columns = [col for col in df_with_row.columns if col != 'row']

    # Unpivot: convert all value columns to rows
    # This transforms wide format to long format
    unpivoted = df_with_row.unpivot(
        on=value_columns,
        index='row',
        variable_name='column',
        value_name='value'
    )

    # Cast value column to string (text) and add metadata columns
    result = unpivoted.select([
        pl.lit(file_path).alias('file_path'),
        pl.lit(file_name).alias('file_name'),
        pl.lit(worksheet).alias('worksheet'),
        pl.col('row'),
        pl.col('column'),
        pl.col('value').cast(pl.Utf8).alias('value'),
    ])

    return result


def process_excel_file(
    file_path: Path,
    output_dir: Path
) -> Dict[str, int]:
    """
    Process a single Excel file: read all sheets, unpivot, and save to Parquet.

    Args:
        file_path: Path to the Excel file
        output_dir: Directory to save Parquet files

    Returns:
        Dictionary with statistics:
        - sheets_processed: Number of sheets successfully processed
        - rows_written: Total rows written to Parquet
        - errors: Number of errors encountered
    """
    stats = {
        'sheets_processed': 0,
        'rows_written': 0,
        'errors': 0
    }

    try:
        sheets_dict = read_all_sheets(file_path)
    except Exception as e:
        logger.error(f"Failed to read {file_path}: {e}")
        stats['errors'] += 1
        return stats

    file_path_str = str(file_path.resolve())
    file_name = file_path.name

    for sheet_name, df in sheets_dict.items():
        try:
            logger.debug(f"Processing sheet '{sheet_name}' with shape {df.shape}")

            # Unpivot the DataFrame
            unpivoted_df = unpivot_dataframe(
                df=df,
                file_path=file_path_str,
                file_name=file_name,
                worksheet=sheet_name
            )

            if unpivoted_df.is_empty():
                logger.warning(f"Skipping empty sheet '{sheet_name}'")
                continue

            # Generate UUID filename
            output_filename = f"{uuid.uuid4()}.parquet"
            output_path = output_dir / output_filename

            # Save to Parquet
            unpivoted_df.write_parquet(output_path)

            stats['sheets_processed'] += 1
            stats['rows_written'] += len(unpivoted_df)

            logger.info(
                f"Saved sheet '{sheet_name}' ({len(unpivoted_df)} rows) "
                f"to {output_filename}"
            )

        except Exception as e:
            stats['errors'] += 1
            logger.error(f"Error processing sheet '{sheet_name}': {e}")
            continue

    return stats


def process_multiple_files(
    file_paths: List[Path],
    output_dir: Path
) -> Dict[str, int]:
    """
    Process multiple Excel files.

    Args:
        file_paths: List of paths to Excel files
        output_dir: Directory to save Parquet files

    Returns:
        Aggregated statistics dictionary
    """
    # Create output directory
    output_dir.mkdir(parents=True, exist_ok=True)
    logger.info(f"Output directory: {output_dir}")

    total_stats = {
        'files_processed': 0,
        'sheets_processed': 0,
        'rows_written': 0,
        'errors': 0
    }

    for file_path in file_paths:
        logger.info(f"Processing file: {file_path}")

        stats = process_excel_file(file_path, output_dir)

        total_stats['files_processed'] += 1
        total_stats['sheets_processed'] += stats['sheets_processed']
        total_stats['rows_written'] += stats['rows_written']
        total_stats['errors'] += stats['errors']

    logger.info(
        f"Processing complete: {total_stats['files_processed']} file(s), "
        f"{total_stats['sheets_processed']} sheet(s), "
        f"{total_stats['rows_written']} row(s), "
        f"{total_stats['errors']} error(s)"
    )

    return total_stats


def setup_logging(log_level: str, log_file: Optional[str] = None) -> None:
    """
    Configure logging with console and optional file output.
    """
    formatter = logging.Formatter(
        fmt='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
        datefmt='%Y-%m-%d %H:%M:%S'
    )

    root_logger = logging.getLogger()
    root_logger.setLevel(log_level.upper())
    root_logger.handlers.clear()

    console_handler = logging.StreamHandler(sys.stdout)
    console_handler.setFormatter(formatter)
    root_logger.addHandler(console_handler)

    if log_file:
        file_handler = logging.FileHandler(log_file, mode='a')
        file_handler.setFormatter(formatter)
        root_logger.addHandler(file_handler)


def main() -> int:
    """
    Main entry point for the Polars Excel-to-Parquet conversion script.
    """
    parser = argparse.ArgumentParser(
        description='Convert Excel files to unpivoted Parquet format using Polars',
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog="""
Output Schema:
  file_path   - Full path to source Excel file
  file_name   - Basename of the Excel file
  worksheet   - Name of the worksheet
  row         - Row number (0-indexed)
  column      - Column name (column_1, column_2, etc.)
  value       - Cell value as text

Examples:
  %(prog)s input.xlsx --output /output/parquet
  %(prog)s /data/*.xlsx -o /out -l DEBUG
  %(prog)s file1.xlsx file2.xls -o /out --log-file conversion.log
        """
    )

    parser.add_argument(
        'files',
        nargs='+',
        help='One or more Excel files to process (.xlsx, .xlsm, .xlsb, .xls)'
    )

    parser.add_argument(
        '--output', '-o',
        required=True,
        help='Output directory for Parquet files (required)'
    )

    parser.add_argument(
        '--log-level', '-l',
        choices=['DEBUG', 'INFO', 'WARNING', 'ERROR', 'CRITICAL'],
        default='INFO',
        help='Logging level (default: INFO)'
    )

    parser.add_argument(
        '--log-file',
        help='Optional log file path'
    )

    args = parser.parse_args()

    try:
        setup_logging(args.log_level, args.log_file)

        logger.info("Starting Polars Excel-to-Parquet conversion")

        # Convert file arguments to Path objects and validate
        file_paths = []
        for file_arg in args.files:
            path = Path(file_arg)
            if not path.exists():
                logger.error(f"File not found: {file_arg}")
                return EXIT_USER_ERROR
            if not path.is_file():
                logger.error(f"Not a file: {file_arg}")
                return EXIT_USER_ERROR
            file_paths.append(path)

        logger.info(f"Processing {len(file_paths)} file(s)")

        output_dir = Path(args.output)
        stats = process_multiple_files(file_paths, output_dir)

        if stats['errors'] > 0:
            logger.warning(f"Completed with {stats['errors']} error(s)")
            return EXIT_PROCESSING_ERROR

        logger.info("Conversion completed successfully")
        return EXIT_SUCCESS

    except KeyboardInterrupt:
        logger.warning("Process interrupted by user")
        return EXIT_USER_ERROR

    except Exception as e:
        logger.exception(f"Unexpected error: {e}")
        return EXIT_UNEXPECTED_ERROR


if __name__ == "__main__":
    sys.exit(main())
