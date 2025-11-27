# Testing Documentation

## Test Organization

The Excel-to-Parquet converter uses a structured test organization pattern based on three distinct categories:

### Naming Convention

Test classes follow the pattern: `Test{FunctionName}{Category}`

**Categories:**
- **HappyPath** - Tests normal, expected behavior with valid inputs
- **EdgeCases** - Tests boundary conditions, empty inputs, and unusual but valid scenarios
- **ErrorHandling** - Tests resilience to invalid inputs, corrupted files, and error conditions

This structure ensures comprehensive coverage across the spectrum from ideal scenarios to failure modes.

### Example Structure
```python
class TestFindSovFoldersHappyPath:
    """Test find_sov_folders() with valid inputs and expected scenarios."""
    
class TestFindSovFoldersEdgeCases:
    """Test find_sov_folders() with edge cases and boundary conditions."""
    
class TestFindSovFoldersErrorHandling:
    """Test find_sov_folders() error handling and resilience."""
```

## Running Tests

```bash
# Run all tests
uv run pytest

# Run all tests with coverage report
uv run pytest --cov

# Run single test file
uv run pytest tests/test_find_sov_folders.py

# Run single test class
uv run pytest tests/test_find_sov_folders.py::TestFindSovFoldersHappyPath

# Run single test function
uv run pytest tests/test_find_sov_folders.py::TestFindSovFoldersHappyPath::test_find_subdirs_in_sov_folder

# Run with verbose output
uv run pytest -v

# Run with detailed coverage report (shows missing lines)
uv run pytest --cov --cov-report=term-missing

# Run tests matching a pattern
uv run pytest -k "sov_folders"

# Run tests and stop at first failure
uv run pytest -x

# Run with output from print statements
uv run pytest -s
```

## Shared Fixtures (conftest.py)

The test suite uses shared fixtures defined in `tests/conftest.py` to reduce code duplication and ensure consistent test setup.

### sample_dataframe
**Purpose**: Provides a simple 5-row DataFrame for basic testing

**Returns**: DataFrame with columns A, B, C containing mixed data types (int, str, float)

**Usage**:
```python
def test_something(sample_dataframe):
    # sample_dataframe is a 5x3 DataFrame
    assert len(sample_dataframe) == 5
```

### create_test_excel
**Purpose**: Factory fixture for creating Excel files with multiple sheets

**Returns**: Function that creates Excel files in temporary directories

**Parameters**:
- `filename` (str): Name of the Excel file (e.g., "test.xlsx")
- `sheets` (dict): Mapping of sheet names to DataFrames
- `directory` (Path, optional): Directory to create file in (defaults to tmp_path)

**Usage**:
```python
def test_something(create_test_excel, sample_dataframe):
    excel_path = create_test_excel(
        filename="test.xlsx",
        sheets={"Sheet1": sample_dataframe, "Sheet2": df2}
    )
    # excel_path now points to created file
```

**Note**: Creates Excel files with `header=False` to match production behavior (first row is data, not headers)

### sov_folder_structure
**Purpose**: Creates a realistic directory structure with SOV folders and Excel files for comprehensive testing

**Creates**:
```
tmp_path/
├── project1/
│   └── SOV/
│       └── 2024/
│           ├── data1.xlsx (2 sheets)
│           └── data2.XLSX (1 sheet, uppercase extension)
├── project2/
│   └── SOV/
│       └── archive/
│           └── nested/
│               └── data3.xls (1 sheet)
└── no_sov/
    └── data4.xlsx (not in SOV folder, should be ignored)
```

**Returns**: Path to the temporary root directory containing the structure

**Usage**:
```python
def test_something(sov_folder_structure):
    # Complex folder structure already created
    result = find_sov_folders([str(sov_folder_structure)])
    assert len(result) > 0
```

### disable_logging
**Purpose**: Suppresses logging output during tests to keep test output clean

**Usage**:
```python
def test_something(disable_logging):
    # All logging is disabled during this test
    # Logging level is restored after test completes
```

**Note**: Automatically yields control back to the test, then restores original logging level after test completion

## Test Files

### test_find_sov_folders.py
**Tests**: `find_sov_folders(root_dirs)` - Discovers directories containing `/SOV/` in their path

**Total Tests**: 17

**HappyPath** (7 tests):
- Finding subdirectories within SOV folders
- Finding multiple subdirectories in a single SOV folder
- Finding nested directories within SOV folders (all levels)
- Results are sorted alphabetically
- Returns Path objects, not strings
- Searching across multiple root directories
- Multiple SOV folders in the same directory tree

**EdgeCases** (7 tests):
- Empty root_dirs list returns empty list
- No SOV folders exist returns empty list
- SOV folder without subdirectories returns empty (only subdirs are returned)
- Case sensitivity: lowercase "sov" not found
- Case sensitivity: mixed case "Sov" not found
- "SOV" as part of larger folder name (e.g., "SOV_data") not found
- Duplicate paths in root_dirs are deduplicated

**ErrorHandling** (3 tests):
- Nonexistent root directory continues processing others
- File path as root_dir is skipped (not a directory)
- Mixed valid/invalid roots processes valid ones

**Key Insight**: The function finds directories that contain `/SOV/` in their path, meaning it returns subdirectories WITHIN SOV folders, not the SOV folders themselves.

### test_process_excel_files.py
**Tests**: `process_excel_files(sov_folders, output_dir)` - Converts Excel sheets to Parquet with metadata

**Total Tests**: 15

**HappyPath** (11 tests):
- Creates Parquet files from Excel sheets
- Adds file_path metadata column
- Adds row_number metadata column (starting from 0)
- file_path is first column
- row_number is second column
- Processes multiple sheets in a single file (separate Parquet for each)
- Uses UUID-based filenames (36 characters, format: 8-4-4-4-12)
- Creates output directory including parents if needed
- Processes both .xlsx and .xls files
- Case-insensitive extension matching (.XLSX, .XlSx)

**EdgeCases** (3 tests):
- Empty sheets are skipped (no Parquet created)
- No Excel files creates empty output directory
- header=None preserves first row as data (not headers)

**ErrorHandling** (2 tests):
- Corrupted Excel file continues processing other files
- Multiple SOV folders with mixed files processes all valid ones

**Note**: Currently some tests are failing due to changes in the underlying implementation (row_number column removed, output schema changed).

### test_main.py
**Tests**: `main()`, `validate_inputs()`, `setup_logging()` - CLI entry point and utilities

**Total Tests**: 19

**TestValidateInputs** (7 tests):
- Valid inputs pass without error
- Multiple valid root directories pass
- Nonexistent root raises ValueError
- File path as root raises ValueError
- Creates output directory if it doesn't exist
- Existing output directory passes validation
- File as output path raises ValueError

**TestSetupLogging** (4 tests):
- Sets root logger to specified level (DEBUG, INFO, WARNING, etc.)
- Creates console handler for stdout
- Creates file handler when log_file specified
- No file handler when log_file not specified

**TestMain** (8 tests):
- Success returns EXIT_SUCCESS (0)
- No SOV folders returns EXIT_SUCCESS (not an error)
- Invalid root returns EXIT_USER_ERROR
- KeyboardInterrupt (Ctrl+C) returns EXIT_USER_ERROR
- Unexpected exceptions return EXIT_UNEXPECTED_ERROR
- PermissionError returns EXIT_USER_ERROR
- Logging setup called with correct log level
- Log file argument passed to setup_logging

**Exit Codes**:
- `EXIT_SUCCESS = 0` - Normal completion
- `EXIT_USER_ERROR = 1` - User input errors, keyboard interrupt
- `EXIT_UNEXPECTED_ERROR = 2` - Unexpected runtime errors

### test_integration.py
**Tests**: Full end-to-end pipeline combining `find_sov_folders()` and `process_excel_files()`

**Total Tests**: 11

**TestFullPipeline** (5 tests):
- Complete pipeline from discovery to conversion
- Data integrity preserved through conversion
- Multiple root directories processed correctly
- file_path metadata contains source Excel path
- Nested SOV folders processed (all levels)

**TestFullPipelineMixedFiles** (6 tests):
- Mixed valid/invalid files processes valid ones
- Mixed empty/non-empty sheets processes non-empty only
- Different Excel formats all processed (.xlsx, .XLSX, .xls, .XLS)
- Multiple sheets each get unique UUID filename
- No Excel files in SOV folder completes successfully
- Deeply nested Excel files found and processed

**Key Scenarios Tested**:
- Metadata columns (file_path, row_number) in correct positions
- Sequential row numbering starting from 0
- UUID filename uniqueness across sheets
- Resilience to corrupted files
- Cross-platform path handling

**Note**: Currently some integration tests are failing due to implementation changes in the output schema.

## Coverage Summary

**Overall Coverage**: 74% (as of latest run)

### Well-Covered Areas

**Excellent Coverage (98-100%)**:
- `tests/conftest.py` - 98% coverage
- `tests/test_find_sov_folders.py` - 100% coverage
- `tests/test_main.py` - 100% coverage
- `tests/test_process_excel_files.py` - 99% coverage

**Core Functions**:
- `find_sov_folders()` - Thoroughly tested with 17 tests covering happy path, edge cases, and error handling
- `validate_inputs()` - Complete coverage of validation logic
- `setup_logging()` - Full coverage of logging configuration

### Areas with Good Coverage (75-84%)

**excel_to_parquet.py** - 75% coverage
- Main processing logic is well-tested
- Missing coverage in:
  - Some error handling paths (lines 407-412, 432-459)
  - Cache management functions (lines 519-522, 563-572)
  - File deduplication logic (lines 640-641, 657-659)
  - Some CLI argument parsing paths

**tests/test_integration.py** - 84% coverage
- Core integration scenarios covered
- Some edge cases not reached in current test runs

### Areas Needing More Coverage

**tui.py** - 26% coverage
- TUI application has minimal automated testing
- Most coverage is basic import/instantiation tests
- Screen interactions, user workflows not tested
- Recommendation: Add Textual app testing or rely on manual QA

**test_tui.py** - 58% coverage
- Basic smoke tests exist
- More comprehensive TUI testing needed

### Gaps and Recommendations

1. **Cache Management** - Add tests for:
   - `load_or_scan_files()` with existing cache
   - Cache invalidation with `--rescan` flag
   - Corrupted cache file handling

2. **File Deduplication** - Add tests for:
   - `get_processed_file_paths()` logic
   - Idempotent processing (skipping already-processed files)

3. **Additional Excel Formats** - Add tests for:
   - `.xlsm` (macro-enabled) files
   - `.xlsb` (binary) files
   - Mixed format processing

4. **Large File Handling** - Consider performance tests for:
   - Large Excel files (>100MB)
   - Many sheets (>50 sheets)
   - Deep directory structures (>10 levels)

5. **TUI Testing** - Consider:
   - Textual testing framework for screen navigation
   - Mock user interactions
   - Background worker error handling

6. **Error Messages** - Add tests verifying:
   - User-friendly error messages
   - Logging output format
   - Progress indicators

## Test Data Characteristics

The test suite uses controlled test data with known properties:

**sample_dataframe**:
- 5 rows, 3 columns
- Mixed types: integers, strings, floats
- Simple, predictable values

**Realistic Structure**:
- Multiple SOV folders at different depths
- Mixed file extensions (case variations)
- Non-SOV folders to test filtering
- Nested subdirectories

**Edge Case Files**:
- Empty sheets
- Corrupted files
- Multiple sheets per file
- Files with uppercase extensions

This ensures tests are deterministic, fast, and cover real-world scenarios.

## Running Specific Test Categories

```bash
# Run only HappyPath tests
uv run pytest -k "HappyPath"

# Run only EdgeCases tests
uv run pytest -k "EdgeCases"

# Run only ErrorHandling tests
uv run pytest -k "ErrorHandling"

# Run integration tests only
uv run pytest tests/test_integration.py

# Run unit tests only (exclude integration)
uv run pytest --ignore=tests/test_integration.py
```

## Notes on Test Failures

As of the latest run, 18 tests are failing, primarily in:
- `test_process_excel_files.py` - Schema changes (row_number column removed)
- `test_integration.py` - Schema and output format changes

These failures indicate the tests need updating to match recent implementation changes. The test structure and coverage remain valuable; the tests themselves need synchronization with the current codebase.

## Contributing New Tests

When adding new tests, follow these guidelines:

1. **Use the three-category structure** - Classify as HappyPath, EdgeCases, or ErrorHandling
2. **Use existing fixtures** - Leverage `sample_dataframe`, `create_test_excel`, `sov_folder_structure`
3. **Use `disable_logging` fixture** - Keep test output clean
4. **Write descriptive test names** - `test_finds_nested_dirs_in_sov` not `test_1`
5. **Add docstrings** - Explain what behavior is being tested
6. **Use tmp_path** - Never write to permanent filesystem locations
7. **Assert specific behaviors** - Not just "doesn't crash"
8. **Test one thing** - Keep tests focused and atomic

## Continuous Integration

The test suite is designed to run in CI environments:

- **Fast execution**: ~1.5 seconds for 67 tests
- **No external dependencies**: All tests use temporary directories
- **Deterministic**: No randomness, no network calls
- **Parallel-safe**: Tests use isolated tmp_path fixtures
- **Coverage reporting**: Integrated with pytest-cov

```bash
# CI-friendly command
uv run pytest --cov --cov-report=xml --cov-report=term -v
```
