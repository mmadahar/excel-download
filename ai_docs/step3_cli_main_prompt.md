# Step 3: Implement CLI Interface and Main Function

## Context
You are implementing part of an Excel-to-Parquet conversion pipeline. This is **Step 3 of 4** - creating the command-line interface and orchestrating the previously implemented functions.

## Full System Context
The complete system:
1. **[Completed]** `find_sov_folders()` - discovers SOV folders → `List[Path]`
2. **[Completed]** `process_excel_files()` - converts Excel to Parquet
3. **[THIS STEP]** CLI interface, logging setup, main orchestration
4. **[Future Step]** Add comprehensive test coverage

## Specific Requirements

### Main Function Responsibilities

The `main()` function must:
1. Parse command-line arguments using `argparse`
2. Configure logging system (level, format, handlers)
3. Validate input arguments
4. Call `find_sov_folders()` with root directories
5. Call `process_excel_files()` with found folders and output directory
6. Handle top-level exceptions gracefully
7. Exit with appropriate status codes

### Command-Line Interface Requirements

#### Required Arguments
```bash
python excel_to_parquet.py ROOT_DIRS [ROOT_DIRS ...] --output OUTPUT_DIR
```

**Positional Arguments:**
- `root_dirs` (nargs='+', type=str, required)
  - One or more root directories to search for SOV folders
  - Can accept multiple space-separated paths
  - Example: `python script.py /data/project1 /data/project2 --output /output`

**Named Arguments:**
- `--output` / `-o` (type=str, required)
  - Output directory for Parquet files
  - Must be provided explicitly (no default)

**Optional Arguments:**
- `--log-level` / `-l` (default='INFO')
  - Choices: ['DEBUG', 'INFO', 'WARNING', 'ERROR', 'CRITICAL']
  - Controls verbosity of logging output
  - Case-insensitive

- `--log-file` (type=str, optional)
  - If provided, write logs to specified file
  - If not provided, only log to console
  - Should append to existing file, not overwrite

#### Help Text Example
```
usage: excel_to_parquet.py [-h] [--output OUTPUT] [--log-level LOG_LEVEL] 
                           [--log-file LOG_FILE] 
                           ROOT_DIRS [ROOT_DIRS ...]

Convert Excel files in SOV folders to Parquet format.

positional arguments:
  ROOT_DIRS             Root directory/directories to search for SOV folders

optional arguments:
  -h, --help            show this help message and exit
  --output OUTPUT, -o OUTPUT
                        Output directory for Parquet files (required)
  --log-level LOG_LEVEL, -l LOG_LEVEL
                        Logging level (default: INFO)
  --log-file LOG_FILE   Optional log file path
```

### Logging Configuration

#### Requirements
1. Configure logging BEFORE any function calls
2. Use format: `'%(asctime)s - %(name)s - %(levelname)s - %(message)s'`
3. Include timestamp in ISO format
4. Support both console and file logging
5. Set level based on command-line argument

#### Configuration Pattern
```python
def setup_logging(log_level: str, log_file: Optional[str] = None) -> None:
    """
    Configure logging for the application.
    
    Sets up console handler always, and optionally adds file handler.
    This centralized configuration ensures consistent logging format
    across all modules.
    
    Why this approach:
    - Configures root logger to affect all modules
    - Console handler for interactive feedback
    - Optional file handler for audit trail
    - ISO timestamp for log analysis tools
    
    Args:
        log_level: Logging level as string (DEBUG, INFO, WARNING, ERROR, CRITICAL)
        log_file: Optional path to log file. If provided, logs are written to file.
    
    Returns:
        None
    """
    # Convert string to logging constant
    numeric_level = getattr(logging, log_level.upper())
    
    # Configure root logger
    logging.basicConfig(
        level=numeric_level,
        format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
        datefmt='%Y-%m-%d %H:%M:%S'
    )
    
    # Add file handler if specified
    if log_file:
        file_handler = logging.FileHandler(log_file, mode='a')
        file_handler.setLevel(numeric_level)
        formatter = logging.Formatter(
            '%(asctime)s - %(name)s - %(levelname)s - %(message)s',
            datefmt='%Y-%m-%d %H:%M:%S'
        )
        file_handler.setFormatter(formatter)
        logging.getLogger().addHandler(file_handler)
```

### Input Validation

Before processing, validate:
1. **Root directories exist**: Log error and exit if any don't exist
2. **Root directories are readable**: Check permissions
3. **Output directory is valid**: Can be created or already exists
4. **At least one root directory provided**: argparse handles this

### Error Handling and Exit Codes

```python
# Success
EXIT_SUCCESS = 0

# User error (invalid arguments, missing directories)
EXIT_USER_ERROR = 1

# Processing error (files couldn't be processed, but not user's fault)
EXIT_PROCESSING_ERROR = 2

# Unexpected error (unhandled exception)
EXIT_UNEXPECTED_ERROR = 3
```

### Main Function Structure

```python
def main() -> int:
    """
    Main entry point for the Excel to Parquet conversion script.
    
    This function orchestrates the entire conversion pipeline:
    1. Parse command-line arguments
    2. Set up logging
    3. Validate inputs
    4. Discover SOV folders
    5. Process Excel files
    6. Report results
    
    Why this structure:
    - Returns exit code for scriptability
    - Validates inputs before processing
    - Provides clear error messages to user
    - Logs all significant events
    - Graceful degradation on errors
    
    Returns:
        Integer exit code (0 for success, non-zero for error)
    
    Example:
        $ python excel_to_parquet.py /data/projects --output /output/parquet
        $ echo $?  # Check exit code
        0
    """
    # Parse arguments
    parser = argparse.ArgumentParser(
        description='Convert Excel files in SOV folders to Parquet format.',
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog='''
Examples:
  # Single root directory
  python excel_to_parquet.py /data/project1 --output /output/parquet
  
  # Multiple root directories with debug logging
  python excel_to_parquet.py /data/p1 /data/p2 -o /output -l DEBUG
  
  # With log file
  python excel_to_parquet.py /data -o /out --log-file conversion.log
        '''
    )
    
    # Add arguments
    # ... (implement argument definitions)
    
    args = parser.parse_args()
    
    # Setup logging
    setup_logging(args.log_level, args.log_file)
    logger = logging.getLogger(__name__)
    
    try:
        # Log startup information
        logger.info("="*60)
        logger.info("Excel to Parquet Conversion Starting")
        logger.info(f"Root directories: {args.root_dirs}")
        logger.info(f"Output directory: {args.output}")
        logger.info("="*60)
        
        # Validate inputs
        # ... (implement validation)
        
        # Convert to Path objects
        root_dirs = args.root_dirs  # Keep as strings for find_sov_folders
        output_dir = Path(args.output)
        
        # Step 1: Find SOV folders
        logger.info("Searching for SOV folders...")
        sov_folders = find_sov_folders(root_dirs)
        
        if not sov_folders:
            logger.warning("No SOV folders found. Nothing to process.")
            return EXIT_SUCCESS  # Not an error, just nothing to do
        
        logger.info(f"Found {len(sov_folders)} SOV folder(s)")
        
        # Step 2: Process Excel files
        logger.info("Processing Excel files...")
        process_excel_files(sov_folders, output_dir)
        
        # Success
        logger.info("="*60)
        logger.info("Conversion completed successfully")
        logger.info("="*60)
        return EXIT_SUCCESS
        
    except KeyboardInterrupt:
        logger.warning("Process interrupted by user")
        return EXIT_USER_ERROR
        
    except Exception as e:
        logger.error(f"Unexpected error: {type(e).__name__} - {e}", exc_info=True)
        return EXIT_UNEXPECTED_ERROR
```

### Input Validation Implementation

```python
def validate_inputs(root_dirs: List[str], output: str) -> None:
    """
    Validate command-line inputs before processing.
    
    Checks that all root directories exist and are accessible,
    and that output directory can be created or is writable.
    
    Args:
        root_dirs: List of root directory paths as strings
        output: Output directory path as string
    
    Raises:
        ValueError: If any validation check fails
        PermissionError: If directories are not accessible
    """
    logger = logging.getLogger(__name__)
    
    # Validate root directories
    for root_dir in root_dirs:
        root_path = Path(root_dir)
        if not root_path.exists():
            raise ValueError(f"Root directory does not exist: {root_dir}")
        if not root_path.is_dir():
            raise ValueError(f"Path is not a directory: {root_dir}")
        if not os.access(root_path, os.R_OK):
            raise PermissionError(f"Cannot read directory: {root_dir}")
    
    # Validate output directory (can be created or must be writable)
    output_path = Path(output)
    if output_path.exists():
        if not output_path.is_dir():
            raise ValueError(f"Output path exists but is not a directory: {output}")
        if not os.access(output_path, os.W_OK):
            raise PermissionError(f"Cannot write to output directory: {output}")
    else:
        # Check if parent exists and is writable
        parent = output_path.parent
        if not parent.exists():
            raise ValueError(f"Parent directory does not exist: {parent}")
        if not os.access(parent, os.W_OK):
            raise PermissionError(f"Cannot create output directory in: {parent}")
    
    logger.debug("Input validation passed")
```

### Complete File Structure

```python
#!/usr/bin/env python3
"""
Excel to Parquet Conversion Script

This script recursively searches for folders containing "/SOV/" in their path,
finds Excel files within those folders, and converts each sheet to a separate
Parquet file with UUID-based naming.

Usage:
    python excel_to_parquet.py <root_dirs...> --output <output_dir> [options]

Example:
    python excel_to_parquet.py /data/project1 /data/project2 \\
        --output /output/parquet \\
        --log-level DEBUG \\
        --log-file conversion.log
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

# Module logger
logger = logging.getLogger(__name__)


def setup_logging(log_level: str, log_file: Optional[str] = None) -> None:
    """Configure logging..."""
    pass


def validate_inputs(root_dirs: List[str], output: str) -> None:
    """Validate command-line inputs..."""
    pass


def find_sov_folders(root_dirs: List[str]) -> List[Path]:
    """Find SOV folders... (from Step 1)"""
    pass


def process_excel_files(sov_folders: List[Path], output_dir: Path) -> None:
    """Process Excel files... (from Step 2)"""
    pass


def main() -> int:
    """Main entry point..."""
    pass


if __name__ == "__main__":
    sys.exit(main())
```

### Critical Success Criteria

Your implementation must:
- ✅ Use argparse for all command-line parsing
- ✅ Accept multiple root directories (nargs='+')
- ✅ Require --output argument explicitly
- ✅ Configure logging before any processing
- ✅ Validate all inputs before processing
- ✅ Return proper exit codes
- ✅ Handle KeyboardInterrupt gracefully
- ✅ Log all significant events (start, found folders, complete)
- ✅ Provide helpful error messages
- ✅ Work correctly when called with sys.exit()

### Common Pitfalls to Avoid

❌ **DON'T** configure logging multiple times
❌ **DON'T** forget to convert log_level string to logging constant
❌ **DON'T** use print() statements - use logger instead
❌ **DON'T** forget to validate inputs before processing
❌ **DON'T** return None from main() - return int exit code
❌ **DON'T** raise exceptions to user - catch and log with proper exit code
❌ **DON'T** forget shebang line for Unix execution
❌ **DON'T** forget to make script executable (`chmod +x`)

### Testing Considerations

When testing in Step 4:
- Mock argparse arguments
- Test validation logic independently
- Test various exit code scenarios
- Test logging configuration
- Test with missing directories
- Test with invalid log levels

## Validation Checklist

Before considering this step complete:

- [ ] argparse configured with all required/optional arguments
- [ ] Help text is clear and includes examples
- [ ] Logging configured before any processing
- [ ] Both console and file logging supported
- [ ] Input validation implemented
- [ ] Proper exit codes defined and returned
- [ ] KeyboardInterrupt handled gracefully
- [ ] Top-level exception handler catches unexpected errors
- [ ] Functions from Steps 1 & 2 integrated correctly
- [ ] Shebang line included for Unix
- [ ] Module docstring explains purpose and usage
- [ ] PEP 8 compliant

## Output Format

Provide:
1. Complete main() function with all logic
2. setup_logging() function
3. validate_inputs() function
4. argparse configuration
5. Exit code constants
6. Module-level docstring
7. Shebang line
8. Integration with find_sov_folders and process_excel_files
9. Example invocation commands

## Integration Note

This step completes the main script. The file should now be executable:

```bash
# Make executable
chmod +x excel_to_parquet.py

# Run
./excel_to_parquet.py /data/projects --output /output/parquet

# Or with Python
python excel_to_parquet.py /data/projects --output /output/parquet -l DEBUG
```

Next step (Step 4) will add comprehensive test coverage for all functions.
