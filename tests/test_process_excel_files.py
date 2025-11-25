"""
Tests for the process_excel_files() function.

Tests cover:
- Happy path scenarios (creates parquet, adds metadata, handles multiple sheets)
- Edge cases (empty sheets, no excel files, header=None behavior)
- Error handling (corrupted files continue processing)
"""

from pathlib import Path

import pandas as pd
import pytest

from excel_to_parquet import process_excel_files


class TestProcessExcelFilesHappyPath:
    """Test process_excel_files() with valid inputs and expected scenarios."""

    def test_creates_parquet_files_from_excel(
        self, sov_folder_structure, tmp_path, disable_logging
    ):
        """Should create parquet files from Excel sheets."""
        # Arrange
        output_dir = tmp_path / "output"
        sov_folders = [
            sov_folder_structure / "project1" / "SOV" / "2024"
        ]

        # Act
        process_excel_files(sov_folders, output_dir)

        # Assert
        parquet_files = list(output_dir.glob("*.parquet"))
        assert len(parquet_files) > 0

    def test_adds_file_path_column_to_output(
        self, sov_folder_structure, tmp_path, disable_logging
    ):
        """Should add file_path metadata column to each output."""
        # Arrange
        output_dir = tmp_path / "output"
        sov_folders = [
            sov_folder_structure / "project1" / "SOV" / "2024"
        ]

        # Act
        process_excel_files(sov_folders, output_dir)

        # Assert
        parquet_files = list(output_dir.glob("*.parquet"))
        assert len(parquet_files) > 0

        df = pd.read_parquet(parquet_files[0])
        assert 'file_path' in df.columns
        assert df['file_path'].iloc[0]  # Should not be empty

    def test_adds_row_number_column_to_output(
        self, sov_folder_structure, tmp_path, disable_logging
    ):
        """Should add row_number metadata column starting from 0."""
        # Arrange
        output_dir = tmp_path / "output"
        sov_folders = [
            sov_folder_structure / "project1" / "SOV" / "2024"
        ]

        # Act
        process_excel_files(sov_folders, output_dir)

        # Assert
        parquet_files = list(output_dir.glob("*.parquet"))
        assert len(parquet_files) > 0

        df = pd.read_parquet(parquet_files[0])
        assert 'row_number' in df.columns
        assert list(df['row_number']) == list(range(len(df)))

    def test_file_path_is_first_column(
        self, sov_folder_structure, tmp_path, disable_logging
    ):
        """Should insert file_path as the first column."""
        # Arrange
        output_dir = tmp_path / "output"
        sov_folders = [
            sov_folder_structure / "project1" / "SOV" / "2024"
        ]

        # Act
        process_excel_files(sov_folders, output_dir)

        # Assert
        parquet_files = list(output_dir.glob("*.parquet"))
        df = pd.read_parquet(parquet_files[0])
        assert df.columns[0] == 'file_path'

    def test_row_number_is_second_column(
        self, sov_folder_structure, tmp_path, disable_logging
    ):
        """Should insert row_number as the second column."""
        # Arrange
        output_dir = tmp_path / "output"
        sov_folders = [
            sov_folder_structure / "project1" / "SOV" / "2024"
        ]

        # Act
        process_excel_files(sov_folders, output_dir)

        # Assert
        parquet_files = list(output_dir.glob("*.parquet"))
        df = pd.read_parquet(parquet_files[0])
        assert df.columns[1] == 'row_number'

    def test_processes_multiple_sheets_in_single_file(
        self, tmp_path, create_test_excel, sample_dataframe, disable_logging
    ):
        """Should create separate parquet file for each sheet."""
        # Arrange
        sov_data = tmp_path / "project" / "SOV" / "data"
        sov_data.mkdir(parents=True)

        df1 = sample_dataframe
        df2 = pd.DataFrame({'X': [1, 2, 3]})

        create_test_excel(
            "multi_sheet.xlsx",
            {"Sheet1": df1, "Sheet2": df2},
            sov_data
        )

        output_dir = tmp_path / "output"

        # Act
        process_excel_files([sov_data], output_dir)

        # Assert
        parquet_files = list(output_dir.glob("*.parquet"))
        assert len(parquet_files) == 2

    def test_uses_uuid_filenames(
        self, sov_folder_structure, tmp_path, disable_logging
    ):
        """Should use UUID-based filenames for output."""
        # Arrange
        output_dir = tmp_path / "output"
        sov_folders = [
            sov_folder_structure / "project1" / "SOV" / "2024"
        ]

        # Act
        process_excel_files(sov_folders, output_dir)

        # Assert
        parquet_files = list(output_dir.glob("*.parquet"))
        assert len(parquet_files) > 0

        # UUID filenames should be 36 characters + .parquet extension
        for pf in parquet_files:
            name = pf.stem  # filename without extension
            # UUIDs are formatted as 8-4-4-4-12 (36 chars with hyphens)
            assert len(name) == 36
            assert name.count('-') == 4

    def test_creates_output_directory_if_not_exists(
        self, sov_folder_structure, tmp_path, disable_logging
    ):
        """Should create output directory including parents if needed."""
        # Arrange
        output_dir = tmp_path / "deeply" / "nested" / "output"
        sov_folders = [
            sov_folder_structure / "project1" / "SOV" / "2024"
        ]

        # Assert output directory doesn't exist yet
        assert not output_dir.exists()

        # Act
        process_excel_files(sov_folders, output_dir)

        # Assert
        assert output_dir.exists()
        assert output_dir.is_dir()

    def test_processes_xlsx_and_xls_files(
        self, sov_folder_structure, tmp_path, disable_logging
    ):
        """Should process both .xlsx and .xls files."""
        # Arrange
        output_dir = tmp_path / "output"
        sov_folders = [
            sov_folder_structure / "project1" / "SOV" / "2024",
            sov_folder_structure / "project2" / "SOV" / "archive" / "nested"
        ]

        # Act
        process_excel_files(sov_folders, output_dir)

        # Assert - should have files from both .xlsx and .xls
        parquet_files = list(output_dir.glob("*.parquet"))
        assert len(parquet_files) >= 2

    def test_case_insensitive_extension_matching(
        self, tmp_path, create_test_excel, sample_dataframe, disable_logging
    ):
        """Should find Excel files with uppercase extensions."""
        # Arrange
        sov_data = tmp_path / "project" / "SOV" / "data"
        sov_data.mkdir(parents=True)

        create_test_excel("uppercase.XLSX", {"Sheet1": sample_dataframe}, sov_data)
        create_test_excel("mixed.XlSx", {"Sheet1": sample_dataframe}, sov_data)

        output_dir = tmp_path / "output"

        # Act
        process_excel_files([sov_data], output_dir)

        # Assert
        parquet_files = list(output_dir.glob("*.parquet"))
        assert len(parquet_files) == 2


class TestProcessExcelFilesEdgeCases:
    """Test process_excel_files() with edge cases and boundary conditions."""

    def test_empty_sheet_skipped(
        self, tmp_path, create_test_excel, sample_dataframe, disable_logging
    ):
        """Should skip empty sheets and not create parquet files for them."""
        # Arrange
        sov_data = tmp_path / "project" / "SOV" / "data"
        sov_data.mkdir(parents=True)

        empty_df = pd.DataFrame()
        non_empty_df = sample_dataframe

        create_test_excel(
            "mixed.xlsx",
            {"EmptySheet": empty_df, "NonEmptySheet": non_empty_df},
            sov_data
        )

        output_dir = tmp_path / "output"

        # Act
        process_excel_files([sov_data], output_dir)

        # Assert - should only have 1 parquet file (non-empty sheet)
        parquet_files = list(output_dir.glob("*.parquet"))
        assert len(parquet_files) == 1

    def test_no_excel_files_creates_empty_output_dir(
        self, tmp_path, disable_logging
    ):
        """Should handle SOV folders with no Excel files."""
        # Arrange
        sov_data = tmp_path / "project" / "SOV" / "data"
        sov_data.mkdir(parents=True)

        # Create a non-Excel file
        (sov_data / "data.txt").write_text("not excel")

        output_dir = tmp_path / "output"

        # Act
        process_excel_files([sov_data], output_dir)

        # Assert
        assert output_dir.exists()
        parquet_files = list(output_dir.glob("*.parquet"))
        assert len(parquet_files) == 0

    def test_header_none_preserves_first_row_as_data(
        self, tmp_path, create_test_excel, disable_logging
    ):
        """Should treat first row as data, not headers (header=None behavior)."""
        # Arrange
        sov_data = tmp_path / "project" / "SOV" / "data"
        sov_data.mkdir(parents=True)

        # Create DataFrame that would normally have headers
        df = pd.DataFrame({
            'HeaderA': [1, 2, 3],
            'HeaderB': [4, 5, 6]
        })

        create_test_excel("test.xlsx", {"Sheet1": df}, sov_data)

        output_dir = tmp_path / "output"

        # Act
        process_excel_files([sov_data], output_dir)

        # Assert
        parquet_files = list(output_dir.glob("*.parquet"))
        result_df = pd.read_parquet(parquet_files[0])

        # Should have 3 rows (because create_test_excel uses index=False, header=False)
        assert len(result_df) == 3

        # Columns should be numbered (0, 1, etc.) plus metadata columns
        # file_path, row_number, 0, 1
        assert 'file_path' in result_df.columns
        assert 'row_number' in result_df.columns


class TestProcessExcelFilesErrorHandling:
    """Test process_excel_files() error handling and resilience."""

    def test_corrupted_file_continues_processing_others(
        self, tmp_path, create_test_excel, sample_dataframe, disable_logging
    ):
        """Should continue processing when one file is corrupted."""
        # Arrange
        sov_data = tmp_path / "project" / "SOV" / "data"
        sov_data.mkdir(parents=True)

        # Create valid Excel file
        create_test_excel("valid.xlsx", {"Sheet1": sample_dataframe}, sov_data)

        # Create corrupted "Excel" file
        corrupted = sov_data / "corrupted.xlsx"
        corrupted.write_text("This is not a valid Excel file")

        output_dir = tmp_path / "output"

        # Act
        process_excel_files([sov_data], output_dir)

        # Assert - should have processed the valid file
        parquet_files = list(output_dir.glob("*.parquet"))
        assert len(parquet_files) == 1

    def test_multiple_sov_folders_with_mixed_files(
        self, tmp_path, create_test_excel, sample_dataframe, disable_logging
    ):
        """Should process all valid files across multiple SOV folders."""
        # Arrange
        sov1 = tmp_path / "project1" / "SOV" / "data"
        sov2 = tmp_path / "project2" / "SOV" / "data"
        sov1.mkdir(parents=True)
        sov2.mkdir(parents=True)

        # Create files in both folders
        create_test_excel("file1.xlsx", {"Sheet1": sample_dataframe}, sov1)
        create_test_excel("file2.xlsx", {"Sheet1": sample_dataframe}, sov2)

        # Add a corrupted file in sov2
        (sov2 / "bad.xlsx").write_text("corrupted")

        output_dir = tmp_path / "output"

        # Act
        process_excel_files([sov1, sov2], output_dir)

        # Assert
        parquet_files = list(output_dir.glob("*.parquet"))
        assert len(parquet_files) == 2
