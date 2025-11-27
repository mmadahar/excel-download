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
from concurrent.futures import ThreadPoolExecutor, as_completed
from datetime import datetime
from pathlib import Path
from typing import List, Optional, Set

import polars as pl

# Exit code constants
EXIT_SUCCESS = 0
EXIT_USER_ERROR = 1
EXIT_PROCESSING_ERROR = 2
EXIT_UNEXPECTED_ERROR = 3


# File scanning constants
EXCEL_EXTENSIONS = {".xlsx", ".xlsm", ".xlsb", ".xls"}
FILES_CSV = Path("data/files.csv")


# Initialize module-level logger
logger = logging.getLogger(__name__)


def get_engine_for_extension(file_path: Path) -> str:
    """
    Determine the appropriate engine for the Excel file extension.

    Maps file extensions to their corresponding Excel reader engines:
    - .xlsx, .xlsm -> openpyxl (modern XML-based Excel format)
    - .xlsb -> pyxlsb (binary Excel format)
    - .xls -> xlrd (legacy Excel format)

    Args:
        file_path: Path object representing the Excel file

    Returns:
        String name of the engine to use with pl.read_excel()

    Example:
        >>> get_engine_for_extension(Path("data.xlsx"))
        'openpyxl'
        >>> get_engine_for_extension(Path("legacy.xls"))
        'xlrd'
    """
    suffix = file_path.suffix.lower()
    engine_map = {
        ".xlsx": "openpyxl",
        ".xlsm": "openpyxl",
        ".xlsb": "pyxlsb",
        ".xls": "xlrd",
    }
    return engine_map.get(suffix, "openpyxl")


def get_processed_file_paths(output_dir: Path) -> Set[str]:
    """
    Get set of file paths already processed in Parquet files.

    Scans all Parquet files in the output directory and extracts unique
    file_path values to enable idempotent processing. If a file path
    already exists in any Parquet file, it can be skipped on subsequent runs.

    WHY this approach works:
    - pl.scan_parquet() uses lazy evaluation for efficiency
    - Glob pattern "*.parquet" matches all Parquet files in directory
    - select("file_path").unique() minimizes data transfer
    - collect() only materializes the unique file paths, not all data
    - Returns set for O(1) lookup performance during skip checks
    - Empty set on error ensures processing continues even if no files exist

    Args:
        output_dir: Path to directory containing Parquet files

    Returns:
        Set of file path strings that have already been processed.
        Empty set if no Parquet files exist or on error.

    Example:
        >>> output_dir = Path("/output/parquet")
        >>> processed = get_processed_file_paths(output_dir)
        >>> if "/data/file1.xlsx" in processed:
        ...     print("Already processed, skipping")
    """
    parquet_pattern = str(output_dir / "*.parquet")
    try:
        df = (
            pl.scan_parquet(parquet_pattern)
            .select("file_path")
            .unique()
            .collect(engine="streaming")
        )
        return set(df["file_path"].to_list())
    except Exception as e:
        # No parquet files yet or error reading them
        logger.debug(f"Could not load processed file paths: {e}")
        return set()


def scan_for_excel_files(root_dirs: List[Path]) -> pl.DataFrame:
    """
    Scan directories for Excel files and return metadata as DataFrame.

    Recursively searches through provided root directories to find all Excel
    files with extensions: .xlsx, .xlsm, .xlsb, .xls (case-insensitive).
    Returns a Polars DataFrame with file paths, extensions, and discovery
    timestamps.

    WHY this approach works:
    - Case-insensitive extension matching using suffix.lower() ensures we
      catch files regardless of how they're named (.XLSX, .xlsx, etc.)
    - Set-based extension filtering is O(1) lookup time
    - Absolute path resolution via resolve() ensures consistent, unique paths
    - ISO timestamp provides sortable, human-readable discovery time
    - Polars DataFrame is more efficient than Pandas for I/O operations
    - Error handling per directory prevents one bad path from crashing scan

    Args:
        root_dirs: List of Path objects representing directories to search.
                   Can include both files and directories; non-directories
                   will be skipped.

    Returns:
        pl.DataFrame with schema:
            - file_path (str): Absolute path to Excel file
            - extension (str): Lowercase file extension with dot (e.g., '.xlsx')
            - discovered_at (str): ISO 8601 timestamp of discovery

    Example:
        >>> roots = [Path("/data/projects"), Path("/backup")]
        >>> df = scan_for_excel_files(roots)
        >>> print(df)
        shape: (15, 3)
        ┌─────────────────────────┬───────────┬─────────────────────────┐
        │ file_path               ┆ extension ┆ discovered_at           │
        │ ---                     ┆ ---       ┆ ---                     │
        │ str                     ┆ str       ┆ str                     │
        ╞═════════════════════════╪═══════════╪═════════════════════════╡
        │ /data/projects/a.xlsx   ┆ .xlsx     ┆ 2025-11-26T10:30:00     │
        │ /data/projects/b.xlsm   ┆ .xlsm     ┆ 2025-11-26T10:30:00     │
        └─────────────────────────┴───────────┴─────────────────────────┘
    """
    discovered_files = []
    discovery_time = datetime.now().isoformat()

    logger.info(f"Scanning {len(root_dirs)} root directory(ies) for Excel files")

    for root_path in root_dirs:
        if not root_path.exists():
            logger.warning(f"Root directory does not exist: {root_path}")
            continue

        if not root_path.is_dir():
            logger.warning(f"Root path is not a directory: {root_path}")
            continue

        try:
            # Recursively find all files
            for path in root_path.rglob("*"):
                if path.is_file():
                    # Check if extension matches (case-insensitive)
                    if path.suffix.lower() in EXCEL_EXTENSIONS:
                        discovered_files.append(
                            {
                                "file_path": str(path.resolve()),
                                "extension": path.suffix.lower(),
                                "discovered_at": discovery_time,
                            }
                        )

        except PermissionError as e:
            logger.warning(f"Permission denied accessing {root_path}: {e}")
            continue
        except Exception as e:
            logger.warning(f"Error scanning {root_path}: {e}")
            continue

    logger.info(f"Discovered {len(discovered_files)} Excel file(s)")

    # Create Polars DataFrame with explicit schema
    if discovered_files:
        df = pl.DataFrame(discovered_files)
    else:
        # Return empty DataFrame with correct schema
        df = pl.DataFrame(
            schema={
                "file_path": pl.Utf8,
                "extension": pl.Utf8,
                "discovered_at": pl.Utf8,
            }
        )

    return df


def load_or_scan_files(root_dirs: List[str], rescan: bool) -> pl.DataFrame:
    """
    Load existing file list from CSV or perform fresh scan.

    This function implements the caching logic for file discovery. If a CSV
    file exists and rescan is False, it loads the cached file list. Otherwise,
    it performs a fresh scan and saves the results to CSV.

    WHY this approach works:
    - Checking CSV existence before scanning avoids redundant filesystem traversal
    - Creating data/ directory with parents=True handles nested paths
    - exist_ok=True prevents errors if directory already exists
    - Polars read_csv/write_csv is faster than Pandas for I/O
    - Converting string paths to Path objects enables pathlib operations
    - Rescan flag gives users explicit control over cache invalidation

    Args:
        root_dirs: List of root directory paths as strings to search within
        rescan: If True, ignore existing CSV and perform fresh scan.
                If False, use existing CSV if present, otherwise scan.

    Returns:
        pl.DataFrame with columns: file_path, extension, discovered_at

    Example:
        >>> # First run - scans and creates CSV
        >>> df = load_or_scan_files(["/data/projects"], rescan=False)
        >>> # Second run - loads from CSV
        >>> df = load_or_scan_files(["/data/projects"], rescan=False)
        >>> # Force rescan - ignores CSV
        >>> df = load_or_scan_files(["/data/projects"], rescan=True)
    """
    # Check if we should use existing CSV
    if not rescan and FILES_CSV.exists():
        logger.info(f"Loading existing file list from {FILES_CSV}")
        try:
            df = pl.read_csv(FILES_CSV)
            logger.info(f"Loaded {len(df)} file(s) from CSV")
            return df
        except Exception as e:
            logger.warning(f"Error reading CSV file: {e}. Performing fresh scan.")

    # Perform fresh scan
    logger.info("Performing fresh scan for Excel files")
    root_paths = [Path(root_dir) for root_dir in root_dirs]
    df = scan_for_excel_files(root_paths)

    # Create data directory and save CSV
    try:
        FILES_CSV.parent.mkdir(parents=True, exist_ok=True)
        df.write_csv(FILES_CSV)
        logger.info(f"Saved file list to {FILES_CSV}")
    except Exception as e:
        logger.error(f"Error saving CSV file: {e}")
        # Continue processing even if CSV save fails

    return df


def _traverse_for_sov(root: Path) -> Set[Path]:
    """
    Helper function to recursively traverse a directory tree for SOV folders.

    This function performs the core traversal logic that searches through a
    directory tree and identifies all subdirectories that contain "/SOV/" in
    their path. Designed to be called by worker threads in parallel.

    Args:
        root: Path object representing the directory to traverse

    Returns:
        Set of Path objects representing directories containing "/SOV/" in
        their path. Empty set if no matches found or on error.
    """
    sov_folders = set()

    try:
        # Recursively find all subdirectories
        for path in root.rglob("**"):
            if path.is_dir():
                # Use as_posix() for cross-platform compatibility
                posix_path = path.as_posix()
                if "/SOV/" in posix_path:
                    sov_folders.add(path)

    except PermissionError as e:
        logger.warning(f"Permission denied accessing {root}: {e}")
    except Exception as e:
        logger.warning(f"Error traversing {root}: {e}")

    return sov_folders


def find_sov_folders(
    root_dirs: List[str],
    min_parallel_branches: int = 10,
    max_workers: Optional[int] = None,
) -> List[Path]:
    """
    Find all directories containing "/SOV/" in their path using parallel traversal.

    This function recursively searches through the provided root directories
    and identifies all subdirectories that contain "/SOV/" in their path.
    The search is case-sensitive and uses POSIX-style path notation for
    cross-platform compatibility.

    For performance on large directory trees, the function uses a two-phase
    approach:
    1. Breadth-first traversal to collect subdirectories until at least
       min_parallel_branches directories are accumulated
    2. Parallel traversal across those branches using ThreadPoolExecutor

    WHY this approach works:
    - Breadth-first collection ensures we have enough work to parallelize
    - ThreadPoolExecutor distributes I/O-bound filesystem operations across threads
    - as_posix() converts paths to forward-slash notation on all platforms
      (Windows backslashes become forward slashes), ensuring consistent
      pattern matching across operating systems
    - Case-sensitive matching prevents false positives like "/sov/" or "/Sov/"
    - Error handling with try/except ensures permission errors or missing
      directories don't crash the entire operation
    - Set deduplication handles cases where multiple root dirs might
      contain the same SOV folder (e.g., symlinks or overlapping paths)
    - Sorting provides predictable, reproducible output order

    Args:
        root_dirs: List of root directory paths as strings to search
                   within. Can be relative or absolute paths.
        min_parallel_branches: Minimum number of subdirectories to collect
                               before parallelizing (default: 10)
        max_workers: Maximum number of worker threads for ThreadPoolExecutor
                     (default: None, which uses ThreadPoolExecutor's default)

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

    # Validate and collect root paths
    valid_roots = []
    for root_str in root_dirs:
        root_path = Path(root_str)

        # Handle non-existent directories
        if not root_path.exists():
            logger.warning(f"Root directory does not exist: {root_path}")
            continue

        # Handle non-directory paths
        if not root_path.is_dir():
            logger.warning(f"Root path is not a directory: {root_path}")
            continue

        valid_roots.append(root_path)

    if not valid_roots:
        logger.warning("No valid root directories to process")
        return []

    # Phase 1: Breadth-first collection of subdirectories
    # Collect subdirectories level by level until we have enough to parallelize
    current_level = valid_roots[:]
    all_branches = []
    sov_folders = set()

    logger.debug(f"Starting breadth-first collection (target: {min_parallel_branches} branches)")

    while current_level and len(all_branches) < min_parallel_branches:
        next_level = []

        for directory in current_level:
            try:
                # Check if this directory itself contains /SOV/ in its path
                if "/SOV/" in directory.as_posix():
                    sov_folders.add(directory)

                # Get immediate subdirectories
                for item in directory.iterdir():
                    if item.is_dir():
                        next_level.append(item)

            except PermissionError as e:
                logger.warning(f"Permission denied accessing {directory}: {e}")
                continue
            except Exception as e:
                logger.warning(f"Error reading directory {directory}: {e}")
                continue

        # Add collected directories to branches list
        all_branches.extend(next_level)
        current_level = next_level

        logger.debug(f"Collected {len(all_branches)} branches so far")

    # If we have fewer branches than the threshold, fall back to sequential traversal
    if len(all_branches) < min_parallel_branches:
        logger.debug(
            f"Only {len(all_branches)} branches found (< {min_parallel_branches}), "
            "using sequential traversal"
        )

        # Traverse any remaining branches sequentially
        for branch in all_branches:
            try:
                branch_sov = _traverse_for_sov(branch)
                sov_folders.update(branch_sov)
            except Exception as e:
                logger.warning(f"Error traversing branch {branch}: {e}")
                continue

    else:
        # Phase 2: Parallel traversal across collected branches
        logger.debug(
            f"Starting parallel traversal of {len(all_branches)} branches "
            f"with max_workers={max_workers}"
        )

        with ThreadPoolExecutor(max_workers=max_workers) as executor:
            # Submit all branch traversals to the thread pool
            future_to_branch = {
                executor.submit(_traverse_for_sov, branch): branch
                for branch in all_branches
            }

            # Collect results as they complete
            for future in as_completed(future_to_branch):
                branch = future_to_branch[future]
                try:
                    branch_sov = future.result()
                    sov_folders.update(branch_sov)
                    logger.debug(f"Branch {branch} yielded {len(branch_sov)} SOV folder(s)")
                except Exception as e:
                    logger.warning(f"Error processing branch {branch}: {e}")
                    continue

    # Convert set to sorted list for deterministic output
    result = sorted(sov_folders)

    logger.info(
        f"Found {len(result)} SOV folder(s) across {len(root_dirs)} root directory(ies)"
    )

    return result


def _process_single_file(file_path: Path, output_dir: Path) -> dict:
    """
    Process a single Excel file and convert all sheets to Parquet format.

    This helper function handles the processing of one Excel file, including
    reading all sheets, unpivoting to long format, transforming column names
    to integers, and saving each sheet as a separate Parquet file.

    Args:
        file_path: Path to the Excel file to process
        output_dir: Path to directory where Parquet files will be saved

    Returns:
        dict with statistics:
            - sheets: Number of sheets converted
            - rows: Total rows written
            - errors: Number of errors encountered

    Example:
        >>> result = _process_single_file(Path("data.xlsx"), Path("/output"))
        >>> print(result)
        {'sheets': 3, 'rows': 1240, 'errors': 0}
    """
    stats = {"sheets": 0, "rows": 0, "errors": 0}
    file_path_str = str(file_path)

    try:
        logger.debug(f"Processing file: {file_path.name}")

        # Get appropriate engine for this file type
        engine = get_engine_for_extension(file_path)

        # Read all sheets from Excel file (returns dict)
        sheets_dict = pl.read_excel(
            source=file_path,
            sheet_id=0,  # Load ALL sheets as dict
            engine=engine,
            has_header=False,  # Treat first row as data
            raise_if_empty=False,  # Don't raise on empty sheets
        )

        logger.debug(f"File has {len(sheets_dict)} sheet(s)")

        # Process each sheet
        for sheet_name, df in sheets_dict.items():
            try:
                # Skip empty sheets
                if df.is_empty():
                    logger.warning(
                        f"Skipping empty sheet '{sheet_name}' in {file_path.name}"
                    )
                    continue

                # Add row numbers (0-indexed)
                df_with_row = df.with_row_index(name="row")

                # Get all original column names (excluding 'row')
                value_columns = [col for col in df_with_row.columns if col != "row"]

                # Unpivot: wide to long format
                unpivoted = df_with_row.unpivot(
                    on=value_columns,  # Columns to unpivot
                    index="row",  # Keep as identifier
                    variable_name="column",  # New column for original column names
                    value_name="value",  # New column for cell values
                )

                # Add metadata columns, transform column to integer, cast value to string
                result = unpivoted.select(
                    [
                        pl.lit(file_path_str).alias("file_path"),
                        pl.lit(file_path.name).alias("file_name"),
                        pl.lit(sheet_name).alias("worksheet"),
                        pl.col("row"),
                        pl.col("column").str.replace("column_", "").cast(pl.Int64).alias("column"),
                        pl.col("value").cast(pl.Utf8).alias("value"),
                    ]
                )

                # Generate UUID filename for output
                output_filename = f"{uuid.uuid4()}.parquet"
                output_path = output_dir / output_filename

                # Save to Parquet
                result.write_parquet(output_path)

                stats["sheets"] += 1
                stats["rows"] += len(result)
                logger.debug(
                    f"Saved sheet '{sheet_name}' ({len(result)} rows) to {output_filename}"
                )

            except Exception as e:
                stats["errors"] += 1
                logger.error(
                    f"Error processing sheet '{sheet_name}' in {file_path.name}: {e}"
                )
                continue

    except Exception as e:
        stats["errors"] += 1
        logger.error(f"Error processing file {file_path.name}: {e}")

    return stats


def process_excel_files(
    sov_folders: List[Path],
    output_dir: Path,
    max_workers: Optional[int] = None,
) -> None:
    """
    Convert Excel files to Parquet format with metadata tracking and unpivoting.

    This function reads Excel files from the files.csv registry, uses the correct
    engine per file type, unpivots each sheet to long format, and saves to Parquet.
    Files already processed (found in existing Parquet files) are skipped for
    idempotent operation. Processing is parallelized using ThreadPoolExecutor.

    Output schema:
    - file_path: Absolute path to source Excel file
    - file_name: Basename of Excel file
    - worksheet: Sheet name
    - row: 0-indexed row number
    - column: Column number as integer (1, 2, 3, etc.)
    - value: Cell value as string

    WHY this approach works:
    - Polars read_excel with sheet_id=0 reads all sheets as dict efficiently
    - Engine selection per extension ensures compatibility across formats
    - Skip logic prevents reprocessing files, making operation idempotent
    - Unpivot transforms wide data to normalized long format for analysis
    - with_row_index() adds row numbers before unpivoting
    - Column transformation converts "column_1" -> 1 for cleaner schema
    - Cast to Utf8 ensures all values are strings for consistent schema
    - ThreadPoolExecutor parallelizes I/O-bound file operations
    - Per-file and per-sheet error handling ensures resilience
    - UUID filenames prevent collisions

    Args:
        sov_folders: List of Path objects (not used but kept for compatibility)
        output_dir: Path to directory where Parquet files will be saved
        max_workers: Maximum number of parallel workers (default: None uses system default)

    Returns:
        None. Writes Parquet files to output_dir and logs statistics.

    Example:
        >>> process_excel_files([], Path("/output"))
        INFO: Loaded 4 file(s) from CSV
        INFO: Skipped 2 already-processed file(s)
        INFO: Processing 2 remaining file(s) in parallel
        INFO: Converted 8 sheet(s) with 1240 total rows
    """
    # Create output directory if it doesn't exist
    output_dir.mkdir(parents=True, exist_ok=True)
    logger.info(f"Output directory: {output_dir}")

    # Load file list from CSV
    if not FILES_CSV.exists():
        logger.warning(
            f"File registry {FILES_CSV} does not exist. Run with scan first."
        )
        return

    files_df = pl.read_csv(FILES_CSV)
    logger.info(f"Loaded {len(files_df)} file(s) from CSV")

    if len(files_df) == 0:
        logger.warning("No files to process")
        return

    # Get set of already-processed file paths
    processed_paths = get_processed_file_paths(output_dir)
    logger.info(f"Found {len(processed_paths)} already-processed file(s)")

    # Filter files to process (exclude already-processed and non-existent files)
    files_to_process = []
    total_files_skipped = 0

    for row in files_df.iter_rows(named=True):
        file_path_str = row["file_path"]
        file_path = Path(file_path_str)

        # Skip if already processed
        if file_path_str in processed_paths:
            logger.debug(f"Skipping already-processed file: {file_path.name}")
            total_files_skipped += 1
            continue

        # Verify file still exists
        if not file_path.exists():
            logger.warning(f"File no longer exists: {file_path}")
            continue

        files_to_process.append(file_path)

    if not files_to_process:
        logger.info(
            f"All {len(files_df)} file(s) already processed or missing. Nothing to do."
        )
        return

    logger.info(
        f"Processing {len(files_to_process)} file(s) in parallel (max_workers={max_workers})"
    )

    # Statistics tracking
    total_files_processed = 0
    total_sheets_converted = 0
    total_rows_written = 0
    total_errors = 0

    # Process files in parallel using ThreadPoolExecutor
    with ThreadPoolExecutor(max_workers=max_workers) as executor:
        # Submit all file processing tasks
        future_to_file = {
            executor.submit(_process_single_file, file_path, output_dir): file_path
            for file_path in files_to_process
        }

        # Collect results as they complete
        for future in as_completed(future_to_file):
            file_path = future_to_file[future]
            try:
                stats = future.result()
                total_files_processed += 1
                total_sheets_converted += stats["sheets"]
                total_rows_written += stats["rows"]
                total_errors += stats["errors"]

                logger.debug(
                    f"Completed {file_path.name}: {stats['sheets']} sheet(s), "
                    f"{stats['rows']} row(s), {stats['errors']} error(s)"
                )

            except Exception as e:
                total_errors += 1
                logger.error(f"Unexpected error processing {file_path.name}: {e}")

    # Log final summary statistics
    logger.info(
        f"Processing complete: converted {total_sheets_converted} sheet(s) "
        f"from {total_files_processed} file(s), "
        f"skipped {total_files_skipped} already-processed file(s), "
        f"wrote {total_rows_written} total rows, "
        f"{total_errors} error(s)"
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
        fmt="%(asctime)s - %(name)s - %(levelname)s - %(message)s",
        datefmt="%Y-%m-%d %H:%M:%S",
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
        file_handler = logging.FileHandler(log_file, mode="a")
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
        --rescan/-r: Force rescan for Excel files even if CSV exists

    Example:
        $ python excel_to_parquet.py /data/p1 /data/p2 -o /out -l DEBUG
        $ python excel_to_parquet.py /data/projects -o /out --rescan
    """
    # Parse command-line arguments
    parser = argparse.ArgumentParser(
        description="Convert Excel files in SOV folders to Parquet format",
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog="""
Examples:
  %(prog)s /data/projects --output /output/parquet
  %(prog)s /data/p1 /data/p2 -o /out -l DEBUG
  %(prog)s /data/projects -o /out --log-file conversion.log
        """,
    )

    parser.add_argument(
        "root_dirs",
        nargs="+",
        help="One or more root directories to search for SOV folders",
    )

    parser.add_argument(
        "--output",
        "-o",
        required=True,
        help="Output directory for Parquet files (required)",
    )

    parser.add_argument(
        "--log-level",
        "-l",
        choices=["DEBUG", "INFO", "WARNING", "ERROR", "CRITICAL"],
        default="INFO",
        help="Logging level (default: INFO)",
    )

    parser.add_argument(
        "--log-file", help="Optional log file path (appends to existing file)"
    )

    parser.add_argument(
        "--rescan",
        "-r",
        action="store_true",
        help="Force rescan for Excel files even if CSV exists",
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

        # Scan for Excel files (loads from CSV or performs fresh scan)
        files_df = load_or_scan_files(args.root_dirs, args.rescan)

        if len(files_df) == 0:
            logger.warning("No Excel files found. Nothing to process.")
            return EXIT_SUCCESS

        logger.info(f"Processing {len(files_df)} Excel file(s)")

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
