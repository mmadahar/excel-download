<objective>
Implement comprehensive test suite - Step 4 of 4 in the Excel-to-Parquet pipeline.

Create pytest tests with 90%+ code coverage for all functions. This validates all previous work and ensures production readiness.
</objective>

<context>
@prompts/001-shared-context.md - Read this first for project architecture and standards.
@excel_to_parquet.py - Complete implementation from Steps 1-3.

All functions are implemented. This step tests:
- find_sov_folders() - SOV folder discovery
- process_excel_files() - Excel to Parquet conversion
- setup_logging() - Logging configuration
- validate_inputs() - Input validation
- main() - CLI orchestration
</context>

<test_structure>
```
tests/
├── __init__.py           # Empty, marks as package
├── conftest.py           # Shared fixtures
├── test_find_sov_folders.py
├── test_process_excel_files.py
├── test_main.py
└── test_integration.py
```
</test_structure>

<requirements>
1. **Coverage Target**: 90%+ line coverage
2. **Execution Speed**: <5 seconds for full suite
3. **Isolation**: Tests don't depend on each other
4. **Determinism**: No flaky tests
5. **File System**: Use tmp_path fixture exclusively

Test each function for:
- Happy path (normal operation)
- Edge cases (empty input, boundary conditions)
- Error paths (exceptions, invalid data)
</requirements>

<conftest_py>
```python
# tests/conftest.py
"""Shared fixtures for Excel-to-Parquet test suite."""

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
def create_test_excel(tmp_path):
    """
    Factory fixture for creating test Excel files.

    Usage:
        excel_file = create_test_excel('test.xlsx', {'Sheet1': df})
    """
    def _create_excel(filename: str, sheets: dict) -> Path:
        excel_path = tmp_path / filename
        with pd.ExcelWriter(excel_path, engine='openpyxl') as writer:
            for sheet_name, df in sheets.items():
                df.to_excel(writer, sheet_name=sheet_name,
                           index=False, header=False)
        return excel_path
    return _create_excel


@pytest.fixture
def sov_folder_structure(tmp_path):
    """
    Create realistic SOV folder structure with Excel files.

    Structure:
        tmp_path/
        ├── project1/SOV/data/file1.xlsx
        ├── project2/reports/SOV/file2.xlsx
        └── project3/other/  (no SOV)
    """
    # Create SOV folders
    sov1 = tmp_path / "project1" / "SOV" / "data"
    sov1.mkdir(parents=True)

    sov2 = tmp_path / "project2" / "reports" / "SOV"
    sov2.mkdir(parents=True)

    # Create non-SOV folder
    other = tmp_path / "project3" / "other"
    other.mkdir(parents=True)

    # Create Excel files
    df = pd.DataFrame({'A': [1, 2, 3], 'B': [4, 5, 6]})

    excel1 = sov1 / "file1.xlsx"
    df.to_excel(excel1, index=False, header=False)

    excel2 = sov2 / "file2.xlsx"
    df.to_excel(excel2, index=False, header=False)

    return {
        'root': tmp_path,
        'sov_folders': [sov1.parent, sov2],
        'excel_files': [excel1, excel2],
        'non_sov': other
    }


@pytest.fixture
def disable_logging():
    """Disable logging during tests."""
    logging.disable(logging.CRITICAL)
    yield
    logging.disable(logging.NOTSET)
```
</conftest_py>

<test_find_sov_folders>
```python
# tests/test_find_sov_folders.py
"""Tests for find_sov_folders() function."""

import pytest
from pathlib import Path
import sys
sys.path.insert(0, str(Path(__file__).parent.parent))
from excel_to_parquet import find_sov_folders


class TestFindSovFoldersHappyPath:
    """Tests for normal operation."""

    def test_finds_sov_folders_basic(self, tmp_path):
        """Should find folders with /SOV/ in path."""
        sov_folder = tmp_path / "project" / "SOV" / "data"
        sov_folder.mkdir(parents=True)

        result = find_sov_folders([str(tmp_path)])

        assert len(result) == 1
        assert sov_folder in result

    def test_finds_multiple_sov_folders(self, tmp_path):
        """Should find all SOV folders across multiple roots."""
        sov1 = tmp_path / "p1" / "SOV"
        sov2 = tmp_path / "p2" / "SOV"
        sov1.mkdir(parents=True)
        sov2.mkdir(parents=True)

        result = find_sov_folders([str(tmp_path)])

        assert len(result) == 2

    def test_returns_sorted_list(self, tmp_path):
        """Should return results sorted alphabetically."""
        (tmp_path / "z_project" / "SOV").mkdir(parents=True)
        (tmp_path / "a_project" / "SOV").mkdir(parents=True)

        result = find_sov_folders([str(tmp_path)])

        assert result == sorted(result)

    def test_returns_path_objects(self, tmp_path):
        """Should return Path objects, not strings."""
        (tmp_path / "project" / "SOV").mkdir(parents=True)

        result = find_sov_folders([str(tmp_path)])

        assert all(isinstance(p, Path) for p in result)


class TestFindSovFoldersEdgeCases:
    """Tests for edge cases and boundary conditions."""

    def test_empty_input_returns_empty_list(self):
        """Should return empty list for empty input."""
        result = find_sov_folders([])
        assert result == []

    def test_no_sov_folders_returns_empty_list(self, tmp_path):
        """Should return empty list when no SOV folders exist."""
        (tmp_path / "project" / "data").mkdir(parents=True)

        result = find_sov_folders([str(tmp_path)])

        assert result == []

    def test_case_sensitive_matching(self, tmp_path):
        """Should only match /SOV/, not /sov/ or /Sov/."""
        (tmp_path / "p1" / "SOV").mkdir(parents=True)  # Should match
        (tmp_path / "p2" / "sov").mkdir(parents=True)  # Should NOT match
        (tmp_path / "p3" / "Sov").mkdir(parents=True)  # Should NOT match

        result = find_sov_folders([str(tmp_path)])

        assert len(result) == 1
        assert "SOV" in str(result[0])

    def test_nested_sov_folders(self, tmp_path):
        """Should find nested SOV folders."""
        (tmp_path / "SOV" / "inner" / "SOV").mkdir(parents=True)

        result = find_sov_folders([str(tmp_path)])

        # Should find both the outer SOV and inner SOV paths
        assert len(result) >= 2

    def test_removes_duplicates(self, tmp_path):
        """Should not return duplicate paths."""
        sov = tmp_path / "project" / "SOV"
        sov.mkdir(parents=True)

        # Pass same root twice
        result = find_sov_folders([str(tmp_path), str(tmp_path)])

        assert len(result) == len(set(result))


class TestFindSovFoldersErrorHandling:
    """Tests for error handling."""

    def test_nonexistent_root_continues(self, tmp_path, caplog):
        """Should log warning and continue for non-existent root."""
        (tmp_path / "valid" / "SOV").mkdir(parents=True)

        result = find_sov_folders([
            "/nonexistent/path",
            str(tmp_path / "valid")
        ])

        assert len(result) == 1
        assert "does not exist" in caplog.text

    def test_file_not_directory_skipped(self, tmp_path):
        """Should skip files named SOV (not directories)."""
        (tmp_path / "SOV").touch()  # File, not directory

        result = find_sov_folders([str(tmp_path)])

        assert len(result) == 0
```
</test_find_sov_folders>

<test_process_excel_files>
```python
# tests/test_process_excel_files.py
"""Tests for process_excel_files() function."""

import pytest
import pandas as pd
from pathlib import Path
import uuid
import sys
sys.path.insert(0, str(Path(__file__).parent.parent))
from excel_to_parquet import process_excel_files


class TestProcessExcelFilesHappyPath:
    """Tests for normal operation."""

    def test_creates_parquet_file(self, tmp_path, create_test_excel):
        """Should create Parquet file from Excel."""
        df = pd.DataFrame({'A': [1, 2, 3]})
        excel = create_test_excel('test.xlsx', {'Sheet1': df})
        output_dir = tmp_path / "output"

        process_excel_files([excel.parent], output_dir)

        parquet_files = list(output_dir.glob('*.parquet'))
        assert len(parquet_files) == 1

    def test_adds_file_path_column(self, tmp_path, create_test_excel):
        """Should add file_path column with source path."""
        df = pd.DataFrame({'A': [1, 2, 3]})
        excel = create_test_excel('test.xlsx', {'Sheet1': df})
        output_dir = tmp_path / "output"

        process_excel_files([excel.parent], output_dir)

        parquet = list(output_dir.glob('*.parquet'))[0]
        result = pd.read_parquet(parquet)
        assert 'file_path' in result.columns
        assert result['file_path'].iloc[0] == str(excel)

    def test_adds_row_number_column(self, tmp_path, create_test_excel):
        """Should add row_number column starting at 0."""
        df = pd.DataFrame({'A': [1, 2, 3]})
        excel = create_test_excel('test.xlsx', {'Sheet1': df})
        output_dir = tmp_path / "output"

        process_excel_files([excel.parent], output_dir)

        parquet = list(output_dir.glob('*.parquet'))[0]
        result = pd.read_parquet(parquet)
        assert 'row_number' in result.columns
        assert list(result['row_number']) == [0, 1, 2]

    def test_multiple_sheets_create_multiple_files(
        self, tmp_path, create_test_excel
    ):
        """Should create one Parquet file per sheet."""
        df1 = pd.DataFrame({'A': [1, 2]})
        df2 = pd.DataFrame({'B': [3, 4]})
        excel = create_test_excel('test.xlsx', {
            'Sheet1': df1,
            'Sheet2': df2
        })
        output_dir = tmp_path / "output"

        process_excel_files([excel.parent], output_dir)

        parquet_files = list(output_dir.glob('*.parquet'))
        assert len(parquet_files) == 2

    def test_uuid_filenames(self, tmp_path, create_test_excel):
        """Should use valid UUID4 for filenames."""
        df = pd.DataFrame({'A': [1]})
        excel = create_test_excel('test.xlsx', {'Sheet1': df})
        output_dir = tmp_path / "output"

        process_excel_files([excel.parent], output_dir)

        parquet = list(output_dir.glob('*.parquet'))[0]
        # Should not raise ValueError if valid UUID
        uuid.UUID(parquet.stem)

    def test_creates_output_directory(self, tmp_path, create_test_excel):
        """Should create output directory if it doesn't exist."""
        df = pd.DataFrame({'A': [1]})
        excel = create_test_excel('test.xlsx', {'Sheet1': df})
        output_dir = tmp_path / "new" / "nested" / "output"

        process_excel_files([excel.parent], output_dir)

        assert output_dir.exists()


class TestProcessExcelFilesEdgeCases:
    """Tests for edge cases."""

    def test_empty_sheet_skipped(self, tmp_path, caplog):
        """Should skip empty sheets with warning."""
        excel = tmp_path / "test.xlsx"
        with pd.ExcelWriter(excel, engine='openpyxl') as writer:
            pd.DataFrame().to_excel(writer, sheet_name='Empty', index=False)
            pd.DataFrame({'A': [1]}).to_excel(
                writer, sheet_name='Data', index=False, header=False
            )
        output_dir = tmp_path / "output"

        process_excel_files([tmp_path], output_dir)

        parquet_files = list(output_dir.glob('*.parquet'))
        assert len(parquet_files) == 1
        assert "Empty sheet" in caplog.text

    def test_no_excel_files_no_error(self, tmp_path):
        """Should handle folders with no Excel files."""
        output_dir = tmp_path / "output"

        process_excel_files([tmp_path], output_dir)

        parquet_files = list(output_dir.glob('*.parquet'))
        assert len(parquet_files) == 0

    def test_header_none_preserves_first_row(
        self, tmp_path, create_test_excel
    ):
        """Should treat first row as data, not header."""
        # Create Excel with what looks like a header
        df = pd.DataFrame([
            ['Name', 'Value'],  # This should be data, not header
            ['Alice', 100],
            ['Bob', 200]
        ])
        excel = create_test_excel('test.xlsx', {'Sheet1': df})
        output_dir = tmp_path / "output"

        process_excel_files([excel.parent], output_dir)

        parquet = list(output_dir.glob('*.parquet'))[0]
        result = pd.read_parquet(parquet)
        # Should have 3 data rows (including "header" row)
        assert len(result) == 3


class TestProcessExcelFilesErrorHandling:
    """Tests for error handling."""

    def test_corrupted_file_continues(self, tmp_path, caplog):
        """Should log error and continue for corrupted files."""
        # Create corrupted "Excel" file
        corrupted = tmp_path / "corrupted.xlsx"
        corrupted.write_text("not an excel file")

        # Create valid Excel file
        df = pd.DataFrame({'A': [1]})
        valid = tmp_path / "valid.xlsx"
        df.to_excel(valid, index=False, header=False)

        output_dir = tmp_path / "output"

        process_excel_files([tmp_path], output_dir)

        # Should have processed valid file
        parquet_files = list(output_dir.glob('*.parquet'))
        assert len(parquet_files) == 1
        assert "Error processing" in caplog.text
```
</test_process_excel_files>

<test_main>
```python
# tests/test_main.py
"""Tests for main() function and CLI."""

import pytest
import sys
from pathlib import Path
from unittest.mock import patch
sys.path.insert(0, str(Path(__file__).parent.parent))
from excel_to_parquet import (
    main, setup_logging, validate_inputs,
    EXIT_SUCCESS, EXIT_USER_ERROR, EXIT_UNEXPECTED_ERROR
)


class TestValidateInputs:
    """Tests for validate_inputs()."""

    def test_valid_inputs_pass(self, tmp_path):
        """Should not raise for valid inputs."""
        root = tmp_path / "root"
        root.mkdir()
        output = tmp_path / "output"

        validate_inputs([str(root)], str(output))  # Should not raise

    def test_nonexistent_root_raises(self, tmp_path):
        """Should raise ValueError for non-existent root."""
        with pytest.raises(ValueError, match="does not exist"):
            validate_inputs(["/nonexistent"], str(tmp_path))

    def test_file_as_root_raises(self, tmp_path):
        """Should raise ValueError if root is a file."""
        file = tmp_path / "file.txt"
        file.touch()

        with pytest.raises(ValueError, match="not a directory"):
            validate_inputs([str(file)], str(tmp_path))


class TestSetupLogging:
    """Tests for setup_logging()."""

    def test_sets_log_level(self):
        """Should configure logging level."""
        import logging
        setup_logging('DEBUG')
        assert logging.getLogger().level == logging.DEBUG

    def test_creates_file_handler(self, tmp_path):
        """Should create file handler when log_file specified."""
        import logging
        log_file = tmp_path / "test.log"

        setup_logging('INFO', str(log_file))
        logging.info("Test message")

        assert log_file.exists()


class TestMain:
    """Tests for main() function."""

    def test_success_returns_zero(self, tmp_path, monkeypatch):
        """Should return EXIT_SUCCESS on successful run."""
        root = tmp_path / "root" / "SOV"
        root.mkdir(parents=True)
        output = tmp_path / "output"

        args = [
            'excel_to_parquet.py',
            str(root.parent.parent),
            '--output', str(output)
        ]
        monkeypatch.setattr(sys, 'argv', args)

        exit_code = main()

        assert exit_code == EXIT_SUCCESS

    def test_no_sov_folders_returns_success(self, tmp_path, monkeypatch):
        """Should return EXIT_SUCCESS even when no SOV folders found."""
        root = tmp_path / "root"
        root.mkdir()
        output = tmp_path / "output"

        args = [
            'excel_to_parquet.py',
            str(root),
            '--output', str(output)
        ]
        monkeypatch.setattr(sys, 'argv', args)

        exit_code = main()

        assert exit_code == EXIT_SUCCESS

    def test_invalid_root_returns_user_error(self, tmp_path, monkeypatch):
        """Should return EXIT_USER_ERROR for invalid root."""
        args = [
            'excel_to_parquet.py',
            '/nonexistent/path',
            '--output', str(tmp_path)
        ]
        monkeypatch.setattr(sys, 'argv', args)

        exit_code = main()

        assert exit_code == EXIT_USER_ERROR

    def test_keyboard_interrupt_returns_user_error(
        self, tmp_path, monkeypatch
    ):
        """Should return EXIT_USER_ERROR on KeyboardInterrupt."""
        root = tmp_path / "root"
        root.mkdir()

        args = [
            'excel_to_parquet.py',
            str(root),
            '--output', str(tmp_path / "output")
        ]
        monkeypatch.setattr(sys, 'argv', args)

        with patch(
            'excel_to_parquet.find_sov_folders',
            side_effect=KeyboardInterrupt
        ):
            exit_code = main()

        assert exit_code == EXIT_USER_ERROR

    def test_unexpected_error_returns_error_code(
        self, tmp_path, monkeypatch
    ):
        """Should return EXIT_UNEXPECTED_ERROR on unexpected exception."""
        root = tmp_path / "root"
        root.mkdir()

        args = [
            'excel_to_parquet.py',
            str(root),
            '--output', str(tmp_path / "output")
        ]
        monkeypatch.setattr(sys, 'argv', args)

        with patch(
            'excel_to_parquet.find_sov_folders',
            side_effect=RuntimeError("Unexpected")
        ):
            exit_code = main()

        assert exit_code == EXIT_UNEXPECTED_ERROR
```
</test_main>

<test_integration>
```python
# tests/test_integration.py
"""Integration tests for full pipeline."""

import pytest
import pandas as pd
from pathlib import Path
import sys
sys.path.insert(0, str(Path(__file__).parent.parent))
from excel_to_parquet import find_sov_folders, process_excel_files


class TestFullPipeline:
    """End-to-end integration tests."""

    def test_full_pipeline(self, sov_folder_structure):
        """Should process entire pipeline correctly."""
        root = sov_folder_structure['root']
        output_dir = root / "output"

        # Step 1: Find SOV folders
        sov_folders = find_sov_folders([str(root)])

        # Should find the SOV folders
        assert len(sov_folders) >= 2

        # Step 2: Process Excel files
        process_excel_files(sov_folders, output_dir)

        # Should create Parquet files
        parquet_files = list(output_dir.glob('*.parquet'))
        assert len(parquet_files) == 2

        # Verify metadata columns
        for pq in parquet_files:
            df = pd.read_parquet(pq)
            assert 'file_path' in df.columns
            assert 'row_number' in df.columns

    def test_mixed_valid_invalid_files(self, tmp_path):
        """Should process valid files and skip invalid ones."""
        sov = tmp_path / "project" / "SOV"
        sov.mkdir(parents=True)

        # Valid Excel
        valid_df = pd.DataFrame({'A': [1, 2, 3]})
        valid = sov / "valid.xlsx"
        valid_df.to_excel(valid, index=False, header=False)

        # Invalid "Excel"
        invalid = sov / "invalid.xlsx"
        invalid.write_text("not excel content")

        output_dir = tmp_path / "output"

        # Run pipeline
        sov_folders = find_sov_folders([str(tmp_path)])
        process_excel_files(sov_folders, output_dir)

        # Should have processed valid file only
        parquet_files = list(output_dir.glob('*.parquet'))
        assert len(parquet_files) == 1
```
</test_integration>

<output>
Create the following files:
1. `./tests/__init__.py` (empty file)
2. `./tests/conftest.py` (shared fixtures)
3. `./tests/test_find_sov_folders.py`
4. `./tests/test_process_excel_files.py`
5. `./tests/test_main.py`
6. `./tests/test_integration.py`

Run tests with:
```bash
uv run pytest --cov=excel_to_parquet --cov-report=term-missing -v
```
</output>

<verification>
Before completing, verify:
- [ ] All test files created
- [ ] conftest.py has shared fixtures
- [ ] Each function has tests for: happy path, edge cases, errors
- [ ] Tests use tmp_path fixture (no real filesystem)
- [ ] Tests use monkeypatch for sys.argv
- [ ] Tests are isolated (no dependencies between tests)
- [ ] All tests pass: `pytest -v`
- [ ] Coverage >=90%: `pytest --cov=excel_to_parquet`
- [ ] Fast execution: <5 seconds total
- [ ] Test names are descriptive (test_function_scenario_expected)
</verification>

<running_tests>
```bash
# Install test dependencies
uv add pytest pytest-cov --dev

# Run all tests
uv run pytest

# Run with coverage
uv run pytest --cov=excel_to_parquet --cov-report=term-missing

# Run specific test file
uv run pytest tests/test_find_sov_folders.py -v

# Run specific test
uv run pytest tests/test_main.py::TestMain::test_success_returns_zero -v
```
</running_tests>
