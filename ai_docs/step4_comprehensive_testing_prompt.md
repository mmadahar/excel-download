# Step 4: Implement Comprehensive Test Suite

## Context
You are implementing part of an Excel-to-Parquet conversion pipeline. This is **Step 4 of 4** - creating a comprehensive test suite with pytest to ensure code quality and reliability.

## Full System Context
The complete system (all implemented):
1. **[Completed]** `find_sov_folders()` - discovers SOV folders
2. **[Completed]** `process_excel_files()` - converts Excel to Parquet  
3. **[Completed]** CLI interface, logging, main orchestration
4. **[THIS STEP]** Comprehensive test coverage

## Testing Goals

### Target Metrics
- **100% code coverage** (aspirational - minimum 90%)
- **All edge cases covered** (empty files, missing data, permissions)
- **All error paths tested** (exceptions, invalid inputs)
- **Fast execution** (<5 seconds for full suite)
- **Isolated tests** (no dependencies between tests)
- **Deterministic** (no flaky tests)

### Test Structure
```
tests/
├── __init__.py
├── test_find_sov_folders.py
├── test_process_excel_files.py
├── test_main.py
├── test_integration.py
└── conftest.py  # Shared fixtures
```

## Test Requirements by Function

### Testing `find_sov_folders()`

#### Test File: `tests/test_find_sov_folders.py`

**Required Test Cases:**

1. **test_find_sov_folders_basic** (happy path)
   - Create temp directory structure with SOV folders
   - Verify correct folders returned
   - Verify results are sorted
   
2. **test_find_sov_folders_multiple_roots**
   - Multiple root directories provided
   - Some with SOV folders, some without
   - Verify all SOV folders found across roots

3. **test_find_sov_folders_nested_sov**
   - SOV folders nested inside other SOV folders
   - Example: `/data/SOV/project/SOV/subfolder`
   - Verify both are found

4. **test_find_sov_folders_case_sensitive**
   - Create folders with /sov/, /Sov/, /SOV/
   - Verify only /SOV/ (exact case) is matched

5. **test_find_sov_folders_no_matches**
   - Directory structure without any SOV folders
   - Verify empty list returned

6. **test_find_sov_folders_empty_input**
   - Pass empty list as root_dirs
   - Verify empty list returned, no exceptions

7. **test_find_sov_folders_nonexistent_root**
   - Pass non-existent directory as root
   - Verify warning logged, continues processing
   - Other valid roots should still work

8. **test_find_sov_folders_permission_error**
   - Create directory with restricted permissions (Unix only)
   - Verify warning logged, continues processing
   - Requires special handling for Windows

9. **test_find_sov_folders_sov_as_filename**
   - File named "SOV" (not a folder)
   - Verify not included in results

10. **test_find_sov_folders_removes_duplicates**
    - Setup that could produce duplicate paths
    - Verify no duplicates in results

#### Mock Directory Structure Example
```python
@pytest.fixture
def mock_sov_structure(tmp_path):
    """
    Creates a realistic directory structure for testing.
    
    Structure:
        tmp_path/
        ├── project1/
        │   ├── SOV/
        │   │   ├── data/
        │   │   │   └── file1.xlsx
        │   │   └── reports/
        │   └── other/
        ├── project2/
        │   └── subfolder/
        └── project3/
            └── SOV/
                └── nested/
                    └── SOV/
    """
    # Create structure
    sov1 = tmp_path / "project1" / "SOV" / "data"
    sov1.mkdir(parents=True)
    (sov1 / "file1.xlsx").touch()
    
    sov2 = tmp_path / "project1" / "SOV" / "reports"
    sov2.mkdir(parents=True)
    
    other = tmp_path / "project1" / "other"
    other.mkdir(parents=True)
    
    no_sov = tmp_path / "project2" / "subfolder"
    no_sov.mkdir(parents=True)
    
    nested_sov1 = tmp_path / "project3" / "SOV" / "nested" / "SOV"
    nested_sov1.mkdir(parents=True)
    
    return tmp_path
```

---

### Testing `process_excel_files()`

#### Test File: `tests/test_process_excel_files.py`

**Required Test Cases:**

1. **test_process_excel_files_single_sheet** (happy path)
   - Create Excel with single sheet, 5 rows
   - Verify Parquet file created
   - Verify file_path and row_number columns added
   - Verify data integrity

2. **test_process_excel_files_multiple_sheets**
   - Create Excel with 3 sheets
   - Verify 3 Parquet files created
   - Each with correct data and metadata

3. **test_process_excel_files_header_none**
   - Create Excel with header row
   - Verify header treated as data (header=None behavior)
   - First row should be row 0, not treated as column names

4. **test_process_excel_files_uuid_filenames**
   - Process multiple sheets
   - Verify all filenames are valid UUIDs
   - Verify no filename collisions

5. **test_process_excel_files_empty_sheet**
   - Excel with empty sheet (0 rows)
   - Verify warning logged
   - Verify no Parquet file created for empty sheet
   - Other sheets still processed

6. **test_process_excel_files_empty_folder**
   - SOV folder with no Excel files
   - Verify no Parquet files created
   - Verify no exceptions raised

7. **test_process_excel_files_creates_output_dir**
   - Output directory doesn't exist
   - Verify directory created automatically
   - Verify files written successfully

8. **test_process_excel_files_xlsx_and_xls**
   - Mix of .xlsx and .xls files
   - Verify both processed correctly

9. **test_process_excel_files_corrupted_excel**
   - Create invalid Excel file (corrupt data)
   - Verify error logged, processing continues
   - Other valid files still processed

10. **test_process_excel_files_permission_error**
    - Read-only output directory
    - Verify error logged
    - Verify graceful failure

11. **test_process_excel_files_row_number_accuracy**
    - Verify row_number column starts at 0
    - Verify sequential numbering: 0, 1, 2, ...
    - Verify correct for each sheet independently

12. **test_process_excel_files_file_path_column**
    - Verify file_path contains full path to source Excel
    - Verify consistent across all rows in same sheet

13. **test_process_excel_files_special_characters**
    - Sheet name with special characters: "Data/Sheet!", "Sheet#1"
    - Verify handled correctly

14. **test_process_excel_files_large_file**
    - Excel with 1000 rows (performance test)
    - Verify completes in reasonable time (<10s)
    - Verify memory efficient

#### Excel File Creation Helper
```python
@pytest.fixture
def create_test_excel(tmp_path):
    """
    Factory fixture for creating test Excel files.
    
    Returns a function that creates Excel files with specified sheets.
    """
    def _create_excel(filename: str, sheets: dict) -> Path:
        """
        Create an Excel file with specified sheets.
        
        Args:
            filename: Name of Excel file to create
            sheets: Dict mapping sheet names to DataFrames
                   Example: {"Sheet1": df1, "Sheet2": df2}
        
        Returns:
            Path to created Excel file
        """
        excel_path = tmp_path / filename
        
        with pd.ExcelWriter(excel_path, engine='openpyxl') as writer:
            for sheet_name, df in sheets.items():
                df.to_excel(writer, sheet_name=sheet_name, 
                           index=False, header=False)
        
        return excel_path
    
    return _create_excel


# Usage in test:
def test_example(create_test_excel, tmp_path):
    # Create test data
    df1 = pd.DataFrame({'A': [1, 2, 3], 'B': [4, 5, 6]})
    df2 = pd.DataFrame({'X': [7, 8], 'Y': [9, 10]})
    
    # Create Excel file
    excel_file = create_test_excel('test.xlsx', {
        'Sheet1': df1,
        'Sheet2': df2
    })
    
    # Test processing...
```

---

### Testing `main()` Function

#### Test File: `tests/test_main.py`

**Required Test Cases:**

1. **test_main_success_path**
   - Mock argparse with valid arguments
   - Mock find_sov_folders to return folders
   - Mock process_excel_files
   - Verify exit code 0

2. **test_main_no_sov_folders_found**
   - Mock find_sov_folders to return empty list
   - Verify warning logged
   - Verify exit code 0 (not an error)

3. **test_main_invalid_root_directory**
   - Provide non-existent root directory
   - Verify error logged
   - Verify exit code 1 (user error)

4. **test_main_keyboard_interrupt**
   - Simulate KeyboardInterrupt during processing
   - Verify graceful shutdown
   - Verify exit code 1

5. **test_main_unexpected_exception**
   - Mock function to raise unexpected exception
   - Verify error logged with traceback
   - Verify exit code 3

6. **test_main_logging_configuration**
   - Verify logging configured before any processing
   - Test different log levels (DEBUG, INFO, WARNING)
   - Verify log file created if specified

7. **test_main_argument_parsing**
   - Test with various argument combinations
   - Verify all arguments parsed correctly

8. **test_validate_inputs_success**
   - Valid root directories and output
   - Verify no exceptions raised

9. **test_validate_inputs_missing_root**
   - Root directory doesn't exist
   - Verify ValueError raised

10. **test_validate_inputs_permission_error**
    - Root directory not readable
    - Verify PermissionError raised

#### Mocking Strategy for main()
```python
import sys
from unittest.mock import patch, MagicMock
import pytest

def test_main_success(tmp_path, capsys, monkeypatch):
    """
    Test successful execution of main().
    """
    # Setup
    root_dir = tmp_path / "root"
    root_dir.mkdir()
    output_dir = tmp_path / "output"
    
    # Mock command-line arguments
    test_args = [
        'excel_to_parquet.py',
        str(root_dir),
        '--output', str(output_dir),
        '--log-level', 'INFO'
    ]
    monkeypatch.setattr(sys, 'argv', test_args)
    
    # Mock the processing functions
    with patch('excel_to_parquet.find_sov_folders') as mock_find, \
         patch('excel_to_parquet.process_excel_files') as mock_process:
        
        mock_find.return_value = [Path('/fake/SOV/folder')]
        mock_process.return_value = None
        
        # Execute
        from excel_to_parquet import main
        exit_code = main()
        
        # Verify
        assert exit_code == 0
        mock_find.assert_called_once()
        mock_process.assert_called_once()
```

---

### Integration Tests

#### Test File: `tests/test_integration.py`

**End-to-End Tests:**

1. **test_full_pipeline_e2e**
   - Create realistic directory structure with SOV folders
   - Create realistic Excel files with multiple sheets
   - Run entire pipeline (find → process)
   - Verify correct number of Parquet files created
   - Verify data integrity in output files
   - Verify metadata columns present

2. **test_multiple_excel_files**
   - Multiple SOV folders
   - Multiple Excel files in each
   - Verify all processed correctly

3. **test_mixed_success_failure**
   - Some valid Excel files, some corrupted
   - Verify valid ones processed
   - Verify errors logged for invalid ones
   - Verify pipeline completes

---

### Shared Fixtures

#### File: `tests/conftest.py`

```python
import pytest
import pandas as pd
from pathlib import Path
import logging

@pytest.fixture
def sample_dataframe():
    """Create a sample DataFrame for testing."""
    return pd.DataFrame({
        'col1': [1, 2, 3, 4, 5],
        'col2': ['a', 'b', 'c', 'd', 'e'],
        'col3': [1.1, 2.2, 3.3, 4.4, 5.5]
    })


@pytest.fixture
def disable_logging():
    """Disable logging during tests to reduce noise."""
    logging.disable(logging.CRITICAL)
    yield
    logging.disable(logging.NOTSET)


@pytest.fixture
def sov_folder_structure(tmp_path):
    """
    Create a realistic SOV folder structure for testing.
    """
    # Create multiple SOV folders with Excel files
    sov1 = tmp_path / "project1" / "SOV" / "data"
    sov1.mkdir(parents=True)
    
    sov2 = tmp_path / "project2" / "reports" / "SOV"
    sov2.mkdir(parents=True)
    
    # Create sample Excel files
    df = pd.DataFrame({'A': [1, 2, 3], 'B': [4, 5, 6]})
    
    excel1 = sov1 / "data1.xlsx"
    df.to_excel(excel1, index=False)
    
    excel2 = sov2 / "report1.xlsx"
    df.to_excel(excel2, index=False)
    
    return {
        'root': tmp_path,
        'sov_folders': [sov1, sov2],
        'excel_files': [excel1, excel2]
    }
```

---

## Testing Best Practices

### Assertions to Include

```python
# File existence
assert output_file.exists()
assert output_file.is_file()

# Parquet content validation
df = pd.read_parquet(output_file)
assert 'file_path' in df.columns
assert 'row_number' in df.columns
assert df['file_path'].iloc[0] == str(source_file)
assert list(df['row_number']) == list(range(len(df)))

# UUID validation
import uuid
try:
    uuid.UUID(output_file.stem)  # filename without extension
    valid_uuid = True
except ValueError:
    valid_uuid = False
assert valid_uuid

# Logging assertions (with caplog fixture)
assert "Error processing" in caplog.text
assert caplog.records[0].levelname == "ERROR"
```

### Parametrized Tests

```python
@pytest.mark.parametrize("log_level,expected_count", [
    ("DEBUG", 10),  # Many debug messages
    ("INFO", 5),    # Fewer info messages
    ("WARNING", 2), # Only warnings
    ("ERROR", 0),   # No errors in success case
])
def test_logging_levels(log_level, expected_count, caplog):
    """Test different logging levels produce expected output."""
    # Test implementation
    pass
```

### Performance Tests

```python
import time

def test_performance_large_dataset(tmp_path):
    """Verify processing completes in reasonable time."""
    # Create large Excel file (1000 rows)
    large_df = pd.DataFrame({
        'col1': range(1000),
        'col2': ['data'] * 1000
    })
    
    excel_file = tmp_path / "large.xlsx"
    large_df.to_excel(excel_file, index=False)
    
    # Time the processing
    start = time.time()
    # ... process file ...
    duration = time.time() - start
    
    # Should complete in under 10 seconds
    assert duration < 10.0
```

---

## Coverage Requirements

### Measuring Coverage
```bash
# Install coverage tools
pip install pytest-cov

# Run with coverage
pytest --cov=excel_to_parquet --cov-report=html --cov-report=term

# View report
open htmlcov/index.html
```

### Coverage Targets
- `find_sov_folders()`: 100%
- `process_excel_files()`: ≥95% (some error paths hard to trigger)
- `main()`: ≥90%
- `validate_inputs()`: 100%
- `setup_logging()`: 100%

### Uncovered Lines Strategy
If unable to reach 100% coverage:
1. Identify uncovered lines with coverage report
2. Add specific tests for those paths
3. If truly untestable (e.g., OS-specific error), add `# pragma: no cover`

---

## Critical Success Criteria

Your test suite must:
- ✅ Test all public functions
- ✅ Cover all edge cases identified
- ✅ Use pytest fixtures for test data
- ✅ Use mocking for external dependencies
- ✅ Be fast (<5 seconds total)
- ✅ Be deterministic (no random failures)
- ✅ Use clear test names (test_function_scenario_expected)
- ✅ Include docstrings for complex tests
- ✅ Achieve ≥90% code coverage
- ✅ Test error handling explicitly

## Common Testing Pitfalls to Avoid

❌ **DON'T** use real file system extensively - use tmp_path
❌ **DON'T** depend on test execution order - tests must be isolated
❌ **DON'T** leave test files around - pytest cleans tmp_path automatically
❌ **DON'T** test implementation details - test behavior
❌ **DON'T** write tests that take minutes - keep them fast
❌ **DON'T** skip error path testing - errors are critical
❌ **DON'T** use sleep() - use proper mocking
❌ **DON'T** hardcode paths - use fixtures

## Validation Checklist

Before considering testing complete:

- [ ] All functions have unit tests
- [ ] All edge cases covered
- [ ] All error paths tested
- [ ] Integration test covers full pipeline
- [ ] Mocking used appropriately
- [ ] Fixtures in conftest.py
- [ ] Tests run fast (<5 seconds)
- [ ] Coverage report generated (≥90%)
- [ ] All tests pass consistently
- [ ] Test names are descriptive
- [ ] Complex tests have docstrings
- [ ] No skipped tests without reason

## Output Format

Provide:
1. Complete test files for each module
2. conftest.py with shared fixtures
3. Instructions for running tests
4. Coverage report interpretation
5. List of any intentionally uncovered code with justification

## Running the Test Suite

```bash
# Install dependencies
pip install pytest pytest-cov pandas openpyxl

# Run all tests
pytest

# Run with coverage
pytest --cov=excel_to_parquet --cov-report=html --cov-report=term-missing

# Run specific test file
pytest tests/test_find_sov_folders.py

# Run specific test
pytest tests/test_find_sov_folders.py::test_find_sov_folders_basic

# Run with verbose output
pytest -v

# Run with print statements visible
pytest -s
```

This completes the 4-step implementation plan. With all steps complete, you'll have a production-ready, well-tested Excel-to-Parquet conversion tool.
