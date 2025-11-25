#!/usr/bin/env python3
"""
Excel to Parquet Conversion Script

Recursively searches for folders containing '/SOV/' in their path,
finds Excel files within, and converts each sheet to Parquet format
with UUID-based naming and metadata columns.

Usage:
    python excel_to_parquet.py /data/projects --output /output/parquet
    python excel_to_parquet.py /data/p1 /data/p2 -o /out -l DEBUG
"""

import argparse
import logging
import os
import sys
import uuid
from pathlib import Path
from typing import List, Optional

import pandas as pd


# Exit code constants
EXIT_SUCCESS = 0
EXIT_USER_ERROR = 1
EXIT_PROCESSING_ERROR = 2
EXIT_UNEXPECTED_ERROR = 3


# Initialize module-level logger
logger = logging.getLogger(__name__)


def find_sov_folders(root_dirs: List[str]) -> List[Path]:
    """
    Find all directories containing "/SOV/" in their path.

    This function recursively searches through the provided root directories
    and identifies all subdirectories that contain "/SOV/" in their path.
    The search is case-sensitive and uses POSIX-style path notation for
    cross-platform compatibility.

    WHY this approach works:
    - pathlib's rglob('**') recursively traverses all subdirectories
    - as_posix() converts paths to forward-slash notation on all platforms
      (Windows backslashes become forward slashes), ensuring consistent
      pattern matching across operating systems
    - Case-sensitive matching prevents false positives like "/sov/" or
      "/Sov/"
    - Error handling with try/except ensures permission errors or missing
      directories don't crash the entire operation
    - Set deduplication handles cases where multiple root dirs might
      contain the same SOV folder (e.g., symlinks or overlapping paths)
    - Sorting provides predictable, reproducible output order

    Args:
        root_dirs: List of root directory paths as strings to search
                   within. Can be relative or absolute paths.

    Returns:
        Sorted list of Path objects representing directories containing
        "/SOV/" in their path. Empty list if no matches found or if
        root_dirs is empty.

    Example:
        >>> roots = ["/data/projects", "/backup/archive"]
        >>> sov_folders = find_sov_folders(roots)
        >>> for folder in sov_folders:
        ...     print(folder)
        /data/projects/2024/SOV/Q1
        /data/projects/2024/SOV/Q2
        /backup/archive/old/SOV/2023
    """
    if not root_dirs:
        logger.warning("Empty root_dirs list provided")
        return []

    sov_folders = set()

    for root_str in root_dirs:
        root_path = Path(root_str)

        # Handle non-existent directories
        if not root_path.exists():
            logger.warning(
                f"Root directory does not exist: {root_path}"
            )
            continue

        # Handle non-directory paths
        if not root_path.is_dir():
            logger.warning(
                f"Root path is not a directory: {root_path}"
            )
            continue

        try:
            # Recursively find all subdirectories
            for path in root_path.rglob('**'):
                if path.is_dir():
                    # Use as_posix() for cross-platform compatibility
                    posix_path = path.as_posix()
                    if '/SOV/' in posix_path:
                        sov_folders.add(path)

        except PermissionError as e:
            logger.warning(
                f"Permission denied accessing {root_path}: {e}"
            )
            continue
        except Exception as e:
            logger.warning(
                f"Error traversing {root_path}: {e}"
            )
            continue

    # Convert set to sorted list for deterministic output
    result = sorted(sov_folders)

    logger.info(
        f"Found {len(result)} SOV folder(s) across "
        f"{len(root_dirs)} root directory(ies)"
    )

    return result


def process_excel_files(sov_folders: List[Path], output_dir: Path) -> None:
    """
    Convert Excel files to Parquet format with metadata tracking.

    This function discovers all Excel files (.xlsx, .xls) within the provided
    SOV folders, reads each sheet without assuming headers exist, adds metadata
    columns (file_path and row_number), and saves each sheet as a separate
    Parquet file with a UUID filename.

    WHY this approach works:
    - header=None prevents pandas from treating first row as column names
    - pd.ExcelFile context manager efficiently handles multi-sheet workbooks
    - Case-insensitive extension matching (.XLSX, .xlsx, .XLS, .xls) ensures
      we don't miss files due to inconsistent naming
    - Per-file and per-sheet error handling ensures pipeline continues even
      when individual files or sheets fail
    - UUID filenames prevent collisions and provide unique identifiers
    - Metadata columns enable traceability back to source files and original
      row positions
    - Inserting metadata at index 0,1 ensures consistent column ordering

    Args:
        sov_folders: List of Path objects representing directories containing
                     Excel files to process. Typically output from
                     find_sov_folders().
        output_dir: Path object representing the directory where Parquet files
                    will be saved. Created if it doesn't exist (including
                    parent directories).

    Returns:
        None. Writes Parquet files to output_dir and logs processing statistics.

    Example:
        >>> sov_folders = find_sov_folders(["/data/projects"])
        >>> output_dir = Path("/data/output/parquet")
        >>> process_excel_files(sov_folders, output_dir)
        INFO: Processing 3 SOV folder(s)
        INFO: Found 15 Excel file(s) to process
        INFO: Converted 42 sheet(s) from 15 file(s) with 0 error(s)
    """
    # Create output directory if it doesn't exist
    output_dir.mkdir(parents=True, exist_ok=True)
    logger.info(f"Output directory: {output_dir}")

    # Statistics tracking
    total_files_processed = 0
    total_sheets_converted = 0
    total_errors = 0

    # Find all Excel files across all SOV folders
    excel_files = []
    for sov_folder in sov_folders:
        # Find .xlsx files (case-insensitive)
        excel_files.extend(sov_folder.rglob('*.[xX][lL][sS][xX]'))
        # Find .xls files (case-insensitive)
        excel_files.extend(sov_folder.rglob('*.[xX][lL][sS]'))

    logger.info(
        f"Processing {len(sov_folders)} SOV folder(s), "
        f"found {len(excel_files)} Excel file(s) to process"
    )

    # Process each Excel file
    for excel_file in excel_files:
        try:
            logger.debug(f"Processing file: {excel_file}")
            file_path_str = str(excel_file)

            # Use context manager for efficient multi-sheet processing
            with pd.ExcelFile(excel_file, engine='openpyxl') as xls:
                sheet_names = xls.sheet_names
                logger.debug(
                    f"File has {len(sheet_names)} sheet(s): {sheet_names}"
                )

                # Process each sheet in the Excel file
                for sheet_name in sheet_names:
                    try:
                        # Read sheet without assuming headers exist
                        df = pd.read_excel(
                            xls,
                            sheet_name=sheet_name,
                            header=None,
                            engine='openpyxl'
                        )

                        # Skip empty sheets
                        if df.empty:
                            logger.warning(
                                f"Skipping empty sheet '{sheet_name}' "
                                f"in {excel_file}"
                            )
                            continue

                        # Add metadata columns at the beginning
                        # file_path: full path to source Excel file
                        df.insert(0, 'file_path', file_path_str)

                        # row_number: sequential starting from 0
                        df.insert(1, 'row_number', range(len(df)))

                        # Generate UUID filename for output
                        output_filename = f"{uuid.uuid4()}.parquet"
                        output_path = output_dir / output_filename

                        # Save to Parquet
                        df.to_parquet(output_path, index=False)

                        total_sheets_converted += 1
                        logger.debug(
                            f"Saved sheet '{sheet_name}' to {output_filename}"
                        )

                    except Exception as e:
                        total_errors += 1
                        logger.error(
                            f"Error processing sheet '{sheet_name}' "
                            f"in {excel_file}: {e}"
                        )
                        continue

            total_files_processed += 1

        except Exception as e:
            total_errors += 1
            logger.error(
                f"Error processing file {excel_file}: {e}"
            )
            continue

    # Log final summary statistics
    logger.info(
        f"Processing complete: converted {total_sheets_converted} sheet(s) "
        f"from {total_files_processed} file(s) with {total_errors} error(s)"
    )


def setup_logging(log_level: str, log_file: Optional[str] = None) -> None:
    """
    Configure logging with console and optional file output.

    Sets up the root logger with a consistent format and handlers for both
    console output (always enabled) and file output (if specified). This
    function should be called before any logging operations occur.

    Args:
        log_level: Logging level as string (DEBUG, INFO, WARNING, ERROR, CRITICAL)
        log_file: Optional path to log file. If provided, logs will be appended
                  to this file in addition to console output.

    Returns:
        None
    """
    # Create formatter
    formatter = logging.Formatter(
        fmt='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
        datefmt='%Y-%m-%d %H:%M:%S'
    )

    # Get root logger and set level
    root_logger = logging.getLogger()
    root_logger.setLevel(log_level.upper())

    # Clear any existing handlers
    root_logger.handlers.clear()

    # Console handler (always enabled)
    console_handler = logging.StreamHandler(sys.stdout)
    console_handler.setFormatter(formatter)
    root_logger.addHandler(console_handler)

    # File handler (optional)
    if log_file:
        file_handler = logging.FileHandler(log_file, mode='a')
        file_handler.setFormatter(formatter)
        root_logger.addHandler(file_handler)
        logger.info(f"Logging to file: {log_file}")


def validate_inputs(root_dirs: List[str], output: str) -> None:
    """
    Validate that input directories exist and output directory is writable.

    Checks that all provided root directories exist and are readable, and
    verifies that the output directory either exists and is writable or can
    be created.

    Args:
        root_dirs: List of root directory paths to validate
        output: Output directory path to validate

    Raises:
        ValueError: If any root directory doesn't exist or isn't a directory
        PermissionError: If directories aren't readable or output isn't writable

    Returns:
        None
    """
    # Validate root directories
    for root_dir in root_dirs:
        root_path = Path(root_dir)

        if not root_path.exists():
            raise ValueError(f"Root directory does not exist: {root_dir}")

        if not root_path.is_dir():
            raise ValueError(f"Root path is not a directory: {root_dir}")

        if not os.access(root_path, os.R_OK):
            raise PermissionError(f"Root directory is not readable: {root_dir}")

    # Validate output directory
    output_path = Path(output)

    if output_path.exists():
        if not output_path.is_dir():
            raise ValueError(f"Output path exists but is not a directory: {output}")

        if not os.access(output_path, os.W_OK):
            raise PermissionError(f"Output directory is not writable: {output}")
    else:
        # Check if we can create the directory by checking parent
        try:
            output_path.mkdir(parents=True, exist_ok=True)
        except PermissionError as e:
            raise PermissionError(f"Cannot create output directory: {output}") from e


def main() -> int:
    """
    Main entry point for the Excel-to-Parquet conversion script.

    Parses command-line arguments, validates inputs, configures logging,
    discovers SOV folders, and processes Excel files to Parquet format.

    Returns:
        int: Exit code:
            - EXIT_SUCCESS (0): Successful completion or no folders found
            - EXIT_USER_ERROR (1): Invalid arguments, missing directories, or
                                   user interruption
            - EXIT_UNEXPECTED_ERROR (3): Unhandled exceptions

    Command-line arguments:
        root_dirs: One or more root directories to search for SOV folders
        --output/-o: Required output directory for Parquet files
        --log-level/-l: Logging level (DEBUG, INFO, WARNING, ERROR, CRITICAL)
        --log-file: Optional log file path

    Example:
        $ python excel_to_parquet.py /data/p1 /data/p2 -o /out -l DEBUG
    """
    # Parse command-line arguments
    parser = argparse.ArgumentParser(
        description='Convert Excel files in SOV folders to Parquet format',
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog="""
Examples:
  %(prog)s /data/projects --output /output/parquet
  %(prog)s /data/p1 /data/p2 -o /out -l DEBUG
  %(prog)s /data/projects -o /out --log-file conversion.log
        """
    )

    parser.add_argument(
        'root_dirs',
        nargs='+',
        help='One or more root directories to search for SOV folders'
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
        help='Optional log file path (appends to existing file)'
    )

    args = parser.parse_args()

    try:
        # Setup logging FIRST before any other operations
        setup_logging(args.log_level, args.log_file)

        logger.info("Starting Excel-to-Parquet conversion")
        logger.info(f"Root directories: {args.root_dirs}")
        logger.info(f"Output directory: {args.output}")

        # Validate inputs
        validate_inputs(args.root_dirs, args.output)

        # Find SOV folders
        sov_folders = find_sov_folders(args.root_dirs)

        if not sov_folders:
            logger.warning("No SOV folders found. Nothing to process.")
            return EXIT_SUCCESS

        # Process Excel files
        output_path = Path(args.output)
        process_excel_files(sov_folders, output_path)

        logger.info("Excel-to-Parquet conversion completed successfully")
        return EXIT_SUCCESS

    except KeyboardInterrupt:
        logger.warning("Process interrupted by user")
        return EXIT_USER_ERROR

    except (ValueError, PermissionError) as e:
        logger.error(f"Input validation error: {e}")
        return EXIT_USER_ERROR

    except Exception as e:
        logger.exception(f"Unexpected error: {e}")
        return EXIT_UNEXPECTED_ERROR


if __name__ == "__main__":
    sys.exit(main())
