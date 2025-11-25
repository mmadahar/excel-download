<objective>
Implement CLI interface and main() function - Step 3 of 4 in the Excel-to-Parquet pipeline.

This step creates the command-line interface, logging configuration, input validation, and orchestrates Steps 1 & 2. This completes the main script.
</objective>

<context>
@prompts/001-shared-context.md - Read this first for project architecture and standards.
@excel_to_parquet.py - Contains find_sov_folders() and process_excel_files() from Steps 1-2.

This step ORCHESTRATES previous steps:
```python
def main() -> int:
    # Parse args, setup logging, validate
    sov_folders = find_sov_folders(args.root_dirs)
    process_excel_files(sov_folders, Path(args.output))
    return EXIT_SUCCESS
```
</context>

<cli_specification>
```bash
# Usage pattern:
python excel_to_parquet.py ROOT_DIRS [ROOT_DIRS ...] --output OUTPUT_DIR [options]

# Examples:
python excel_to_parquet.py /data/project1 --output /output/parquet
python excel_to_parquet.py /data/p1 /data/p2 -o /out -l DEBUG
python excel_to_parquet.py /data -o /out --log-file conversion.log

# Arguments:
ROOT_DIRS          One or more root directories to search (positional, required)
--output, -o       Output directory for Parquet files (required)
--log-level, -l    DEBUG|INFO|WARNING|ERROR|CRITICAL (default: INFO)
--log-file         Optional file to write logs (appends if exists)
```
</cli_specification>

<requirements>
1. **Argument Parsing (argparse)**
   - root_dirs: positional, nargs='+', required
   - --output/-o: required string
   - --log-level/-l: choices, default='INFO', case-insensitive
   - --log-file: optional string
   - Include helpful description and examples in epilog

2. **Logging Configuration**
   - Configure BEFORE any processing
   - Format: '%(asctime)s - %(name)s - %(levelname)s - %(message)s'
   - Date format: '%Y-%m-%d %H:%M:%S'
   - Console handler always
   - File handler if --log-file specified (append mode)

3. **Input Validation**
   - All root directories must exist and be readable
   - Output directory must be creatable or writable
   - Fail fast with clear error messages

4. **Exit Codes**
   - EXIT_SUCCESS = 0 (successful completion OR no folders found)
   - EXIT_USER_ERROR = 1 (invalid args, missing dirs, KeyboardInterrupt)
   - EXIT_PROCESSING_ERROR = 2 (processing failures)
   - EXIT_UNEXPECTED_ERROR = 3 (unhandled exceptions)

5. **Error Handling**
   - Catch KeyboardInterrupt gracefully
   - Catch all exceptions at top level
   - Log with exc_info=True for tracebacks
   - Return appropriate exit code (never raise to user)
</requirements>

<implementation_pattern>
```python
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
from pathlib import Path
from typing import List, Optional
import pandas as pd
import uuid

# Exit codes
EXIT_SUCCESS = 0
EXIT_USER_ERROR = 1
EXIT_PROCESSING_ERROR = 2
EXIT_UNEXPECTED_ERROR = 3

logger = logging.getLogger(__name__)


def setup_logging(log_level: str, log_file: Optional[str] = None) -> None:
    """
    Configure logging for the application.

    Sets up console handler always, file handler if log_file specified.
    Centralizes logging config to ensure consistent format across modules.

    Args:
        log_level: Logging level as string (DEBUG, INFO, etc.)
        log_file: Optional path to log file. Appends if exists.
    """
    numeric_level = getattr(logging, log_level.upper())

    logging.basicConfig(
        level=numeric_level,
        format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
        datefmt='%Y-%m-%d %H:%M:%S'
    )

    if log_file:
        file_handler = logging.FileHandler(log_file, mode='a')
        file_handler.setLevel(numeric_level)
        file_handler.setFormatter(logging.Formatter(
            '%(asctime)s - %(name)s - %(levelname)s - %(message)s',
            datefmt='%Y-%m-%d %H:%M:%S'
        ))
        logging.getLogger().addHandler(file_handler)


def validate_inputs(root_dirs: List[str], output: str) -> None:
    """
    Validate command-line inputs before processing.

    Checks directories exist and are accessible. Fails fast with
    clear error messages rather than cryptic errors mid-processing.

    Args:
        root_dirs: List of root directory paths to validate.
        output: Output directory path to validate.

    Raises:
        ValueError: If directory doesn't exist or is invalid.
        PermissionError: If directory is not accessible.
    """
    for root_dir in root_dirs:
        root_path = Path(root_dir)
        if not root_path.exists():
            raise ValueError(f"Root directory does not exist: {root_dir}")
        if not root_path.is_dir():
            raise ValueError(f"Path is not a directory: {root_dir}")
        if not os.access(root_path, os.R_OK):
            raise PermissionError(f"Cannot read directory: {root_dir}")

    output_path = Path(output)
    if output_path.exists():
        if not output_path.is_dir():
            raise ValueError(f"Output exists but is not a directory: {output}")
        if not os.access(output_path, os.W_OK):
            raise PermissionError(f"Cannot write to: {output}")
    else:
        parent = output_path.parent
        if parent.exists() and not os.access(parent, os.W_OK):
            raise PermissionError(f"Cannot create directory in: {parent}")


def main() -> int:
    """
    Main entry point for Excel to Parquet conversion.

    Orchestrates the full pipeline: parse args, configure logging,
    validate inputs, find SOV folders, process Excel files.

    Returns:
        Integer exit code (0 for success, non-zero for errors).
    """
    parser = argparse.ArgumentParser(
        description='Convert Excel files in SOV folders to Parquet format.',
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog='''
Examples:
  python excel_to_parquet.py /data/project1 --output /output/parquet
  python excel_to_parquet.py /data/p1 /data/p2 -o /output -l DEBUG
  python excel_to_parquet.py /data -o /out --log-file conversion.log
        '''
    )

    parser.add_argument(
        'root_dirs',
        nargs='+',
        help='Root directory/directories to search for SOV folders'
    )
    parser.add_argument(
        '--output', '-o',
        required=True,
        help='Output directory for Parquet files'
    )
    parser.add_argument(
        '--log-level', '-l',
        default='INFO',
        choices=['DEBUG', 'INFO', 'WARNING', 'ERROR', 'CRITICAL'],
        help='Logging level (default: INFO)'
    )
    parser.add_argument(
        '--log-file',
        help='Optional log file path (appends if exists)'
    )

    args = parser.parse_args()

    # Setup logging FIRST
    setup_logging(args.log_level, args.log_file)

    try:
        logger.info("=" * 60)
        logger.info("Excel to Parquet Conversion Starting")
        logger.info(f"Root directories: {args.root_dirs}")
        logger.info(f"Output directory: {args.output}")
        logger.info("=" * 60)

        # Validate inputs
        validate_inputs(args.root_dirs, args.output)

        # Step 1: Find SOV folders
        logger.info("Searching for SOV folders...")
        sov_folders = find_sov_folders(args.root_dirs)

        if not sov_folders:
            logger.warning("No SOV folders found. Nothing to process.")
            return EXIT_SUCCESS

        logger.info(f"Found {len(sov_folders)} SOV folder(s)")

        # Step 2: Process Excel files
        logger.info("Processing Excel files...")
        process_excel_files(sov_folders, Path(args.output))

        logger.info("=" * 60)
        logger.info("Conversion completed successfully")
        logger.info("=" * 60)
        return EXIT_SUCCESS

    except (ValueError, PermissionError) as e:
        logger.error(f"Input validation failed: {e}")
        return EXIT_USER_ERROR

    except KeyboardInterrupt:
        logger.warning("Process interrupted by user")
        return EXIT_USER_ERROR

    except Exception as e:
        logger.error(f"Unexpected error: {e}", exc_info=True)
        return EXIT_UNEXPECTED_ERROR


if __name__ == "__main__":
    sys.exit(main())
```
</implementation_pattern>

<common_pitfalls>
- Configuring logging multiple times (use basicConfig once)
- Forgetting to convert log_level string to logging constant
- Using print() instead of logger
- Returning None from main() instead of int exit code
- Raising exceptions to user instead of logging and returning exit code
- Forgetting shebang line (#!/usr/bin/env python3)
- Not making --output required
- Not handling KeyboardInterrupt
</common_pitfalls>

<output>
Edit file: `./excel_to_parquet.py`

Complete the file by adding:
1. Module docstring at top
2. Shebang line
3. Additional imports (argparse, sys, os)
4. Exit code constants
5. setup_logging() function
6. validate_inputs() function
7. main() function
8. if __name__ == "__main__" block

Preserve find_sov_folders() and process_excel_files() from Steps 1-2.
</output>

<verification>
Before completing, verify:
- [ ] Shebang line present
- [ ] Module docstring with usage examples
- [ ] All exit codes defined as constants
- [ ] argparse accepts multiple root_dirs (nargs='+')
- [ ] --output is required
- [ ] --log-level has correct choices and default
- [ ] setup_logging() configures format and handlers
- [ ] validate_inputs() checks all requirements
- [ ] main() sets up logging BEFORE processing
- [ ] main() returns int exit codes (never None)
- [ ] KeyboardInterrupt handled gracefully
- [ ] Top-level exception handler catches everything
- [ ] No print() statements (use logger)
- [ ] PEP 8 compliant

Test with:
```bash
python excel_to_parquet.py --help
python excel_to_parquet.py /nonexistent --output /tmp  # Should fail gracefully
```
</verification>

<next_step>
After validation, Step 4 will add comprehensive test coverage for all functions.
The script should now be fully functional:
```bash
chmod +x excel_to_parquet.py
./excel_to_parquet.py /data/projects --output /output/parquet -l DEBUG
```
</next_step>
