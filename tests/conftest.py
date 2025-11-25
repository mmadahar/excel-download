"""
Shared pytest fixtures for Excel-to-Parquet conversion tests.

This module provides reusable test fixtures that create temporary
directories, sample data, and Excel files for testing.
"""

import logging
from pathlib import Path
from typing import Callable

import pandas as pd
import pytest


@pytest.fixture
def sample_dataframe() -> pd.DataFrame:
    """
    Create a sample DataFrame with 5 rows for testing.

    Returns:
        DataFrame with columns A, B, C and 5 rows of test data.
    """
    return pd.DataFrame({
        'A': [1, 2, 3, 4, 5],
        'B': ['a', 'b', 'c', 'd', 'e'],
        'C': [1.1, 2.2, 3.3, 4.4, 5.5]
    })


@pytest.fixture
def create_test_excel(tmp_path) -> Callable:
    """
    Factory fixture to create test Excel files.

    Returns:
        Function that creates an Excel file with specified sheets.

    Example:
        excel_path = create_test_excel(
            filename="test.xlsx",
            sheets={"Sheet1": df1, "Sheet2": df2}
        )
    """
    def _create_excel(
        filename: str,
        sheets: dict[str, pd.DataFrame],
        directory: Path = None
    ) -> Path:
        """
        Create an Excel file with multiple sheets.

        Args:
            filename: Name of the Excel file (e.g., "test.xlsx")
            sheets: Dictionary mapping sheet names to DataFrames
            directory: Directory to create file in (defaults to tmp_path)

        Returns:
            Path to the created Excel file
        """
        if directory is None:
            directory = tmp_path

        excel_path = directory / filename

        with pd.ExcelWriter(excel_path, engine='openpyxl') as writer:
            for sheet_name, df in sheets.items():
                df.to_excel(writer, sheet_name=sheet_name, index=False, header=False)

        return excel_path

    return _create_excel


@pytest.fixture
def sov_folder_structure(tmp_path, create_test_excel, sample_dataframe) -> Path:
    """
    Create a realistic SOV folder structure with Excel files.

    Creates:
        tmp_path/
        ├── project1/
        │   └── SOV/
        │       └── 2024/
        │           ├── data1.xlsx (2 sheets)
        │           └── data2.XLSX (1 sheet)
        ├── project2/
        │   └── SOV/
        │       └── archive/
        │           └── nested/
        │               └── data3.xls (1 sheet)
        └── no_sov/
            └── data4.xlsx (not in SOV folder)

    Returns:
        Path to the temporary root directory containing the structure
    """
    # Create SOV folder structures with subdirectories (realistic structure)
    sov1_data = tmp_path / "project1" / "SOV" / "2024"
    sov1_data.mkdir(parents=True)

    sov2_data = tmp_path / "project2" / "SOV" / "archive" / "nested"
    sov2_data.mkdir(parents=True)

    no_sov = tmp_path / "no_sov"
    no_sov.mkdir(parents=True)

    # Create Excel files in SOV subdirectories
    df1 = sample_dataframe
    df2 = pd.DataFrame({'X': [10, 20, 30], 'Y': [40, 50, 60]})
    df3 = pd.DataFrame({'Z': [100, 200]})

    # data1.xlsx with 2 sheets
    create_test_excel(
        "data1.xlsx",
        {"Sheet1": df1, "Sheet2": df2},
        sov1_data
    )

    # data2.XLSX with 1 sheet (uppercase extension)
    create_test_excel(
        "data2.XLSX",
        {"Sheet1": df1},
        sov1_data
    )

    # data3.xls in nested SOV folder
    create_test_excel(
        "data3.xls",
        {"Sheet1": df3},
        sov2_data
    )

    # data4.xlsx NOT in SOV folder (should be ignored)
    create_test_excel(
        "data4.xlsx",
        {"Sheet1": df1},
        no_sov
    )

    return tmp_path


@pytest.fixture
def disable_logging():
    """
    Disable logging during tests to reduce noise in test output.

    Yields control back to the test, then restores original logging level.
    """
    # Save original logging level
    original_level = logging.root.level

    # Disable all logging
    logging.disable(logging.CRITICAL)

    yield

    # Restore original logging level
    logging.disable(original_level)
