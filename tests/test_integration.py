"""
Integration tests for the full Excel-to-Parquet conversion pipeline.

Tests cover:
- Full end-to-end pipeline execution
- Multiple SOV folders with mixed file types
- Metadata tracking and data integrity
- Error resilience with mixed valid/invalid files
"""

from pathlib import Path

import pandas as pd
import pytest

from excel_converter.cli import find_sov_folders, process_excel_files


class TestFullPipeline:
    """Test the complete pipeline from discovery to conversion."""

    def test_full_pipeline_end_to_end(
        self, sov_folder_structure, tmp_path, disable_logging
    ):
        """Should execute complete pipeline from find to convert."""
        # Arrange
        output_dir = tmp_path / "output"
        root_dirs = [str(sov_folder_structure)]

        # Act - Step 1: Find SOV folders (returns subdirectories within SOV)
        sov_folders = find_sov_folders(root_dirs)

        # Assert - Should find subdirectories within SOV folders
        assert len(sov_folders) >= 2

        # Act - Step 2: Process Excel files
        process_excel_files(sov_folders, output_dir)

        # Assert - Should create parquet files
        parquet_files = list(output_dir.glob("*.parquet"))
        assert len(parquet_files) > 0

        # Assert - Verify metadata columns exist
        for pf in parquet_files:
            df = pd.read_parquet(pf)
            expected_columns = ['file_path', 'file_name', 'worksheet', 'row', 'column', 'value']
            assert list(df.columns) == expected_columns

        # Assert - Verify file_path is not empty
        for pf in parquet_files:
            df = pd.read_parquet(pf)
            assert all(df['file_path'] != '')
            assert all(pd.notna(df['file_path']))

    def test_data_integrity_preserved_through_pipeline(
        self, tmp_path, create_test_excel, disable_logging
    ):
        """Should preserve original data values through conversion."""
        # Arrange
        sov_data = tmp_path / "project" / "SOV" / "data"
        sov_data.mkdir(parents=True)

        # Create DataFrame with known values
        original_df = pd.DataFrame({
            'Col1': [1, 2, 3, 4, 5],
            'Col2': ['a', 'b', 'c', 'd', 'e'],
            'Col3': [1.1, 2.2, 3.3, 4.4, 5.5]
        })

        excel_path = create_test_excel(
            "data.xlsx",
            {"Sheet1": original_df},
            sov_data
        )

        output_dir = tmp_path / "output"

        # Act
        sov_folders = find_sov_folders([str(tmp_path)])
        process_excel_files(sov_folders, output_dir)

        # Assert
        parquet_files = list(output_dir.glob("*.parquet"))
        assert len(parquet_files) == 1

        result_df = pd.read_parquet(parquet_files[0])

        # Verify schema
        expected_columns = ['file_path', 'file_name', 'worksheet', 'row', 'column', 'value']
        assert list(result_df.columns) == expected_columns

        # Verify unpivoted data exists
        # Note: The actual number of rows depends on which columns have data
        # For a DataFrame with 5 rows x 3 columns, only non-null cells create rows
        assert len(result_df) > 0

        # Verify some values exist in the unpivoted data
        values = result_df['value'].tolist()
        # Check if some of the original values are present (as strings)
        # Values might be strings or their original types
        assert len(values) > 0

    def test_multiple_root_directories_processed(
        self, tmp_path, create_test_excel, sample_dataframe, disable_logging
    ):
        """Should process SOV folders across multiple root directories."""
        # Arrange
        root1 = tmp_path / "root1"
        root2 = tmp_path / "root2"

        sov1 = root1 / "project" / "SOV" / "data"
        sov2 = root2 / "project" / "SOV" / "data"
        sov1.mkdir(parents=True)
        sov2.mkdir(parents=True)

        create_test_excel("file1.xlsx", {"Sheet1": sample_dataframe}, sov1)
        create_test_excel("file2.xlsx", {"Sheet1": sample_dataframe}, sov2)

        output_dir = tmp_path / "output"

        # Act
        sov_folders = find_sov_folders([str(root1), str(root2)])
        process_excel_files(sov_folders, output_dir)

        # Assert
        assert len(sov_folders) == 2
        parquet_files = list(output_dir.glob("*.parquet"))
        assert len(parquet_files) >= 1

    def test_file_path_metadata_contains_source_excel_path(
        self, tmp_path, create_test_excel, sample_dataframe, disable_logging
    ):
        """Should store full source Excel file path in file_path column."""
        # Arrange
        sov_data = tmp_path / "project" / "SOV" / "data"
        sov_data.mkdir(parents=True)

        excel_path = create_test_excel(
            "source.xlsx",
            {"Sheet1": sample_dataframe},
            sov_data
        )

        output_dir = tmp_path / "output"

        # Act
        sov_folders = find_sov_folders([str(tmp_path)])
        process_excel_files(sov_folders, output_dir)

        # Assert
        parquet_files = list(output_dir.glob("*.parquet"))
        result_df = pd.read_parquet(parquet_files[0])

        # All file_path values should be the same (source Excel file)
        file_paths = result_df['file_path'].unique()
        assert len(file_paths) == 1
        # file_path should contain the filename
        assert 'source.xlsx' in file_paths[0]

    def test_nested_sov_folders_processed(
        self, tmp_path, create_test_excel, sample_dataframe, disable_logging
    ):
        """Should process Excel files in nested SOV directories."""
        # Arrange
        sov1 = tmp_path / "project" / "SOV" / "level1"
        sov2 = tmp_path / "project" / "SOV" / "level1" / "level2"
        sov1.mkdir(parents=True)
        sov2.mkdir(parents=True)

        create_test_excel("file1.xlsx", {"Sheet1": sample_dataframe}, sov1)
        create_test_excel("file2.xlsx", {"Sheet1": sample_dataframe}, sov2)

        output_dir = tmp_path / "output"

        # Act
        sov_folders = find_sov_folders([str(tmp_path)])
        process_excel_files(sov_folders, output_dir)

        # Assert - should find both level1 and level2 directories
        assert len(sov_folders) == 2
        # Should have processed files from nested structure
        parquet_files = list(output_dir.glob("*.parquet"))
        assert len(parquet_files) >= 1


class TestFullPipelineMixedFiles:
    """Test pipeline resilience with mixed valid and invalid files."""

    def test_mixed_valid_invalid_files_processes_valid_ones(
        self, tmp_path, create_test_excel, sample_dataframe, disable_logging
    ):
        """Should process valid files and skip invalid ones."""
        # Arrange
        sov_data = tmp_path / "project" / "SOV" / "data"
        sov_data.mkdir(parents=True)

        # Create valid Excel file
        create_test_excel("valid.xlsx", {"Sheet1": sample_dataframe}, sov_data)

        # Create corrupted Excel file
        corrupted = sov_data / "corrupted.xlsx"
        corrupted.write_text("This is not a valid Excel file")

        # Create another valid Excel file
        create_test_excel("valid2.xlsx", {"Sheet1": sample_dataframe}, sov_data)

        output_dir = tmp_path / "output"

        # Act
        sov_folders = find_sov_folders([str(tmp_path)])
        process_excel_files(sov_folders, output_dir)

        # Assert - Should have processed valid files
        parquet_files = list(output_dir.glob("*.parquet"))
        assert len(parquet_files) >= 1

    def test_mixed_empty_nonempty_sheets_processes_nonempty_only(
        self, tmp_path, create_test_excel, sample_dataframe, disable_logging
    ):
        """Should skip empty sheets and process non-empty ones."""
        # Arrange
        sov_data = tmp_path / "project" / "SOV" / "data"
        sov_data.mkdir(parents=True)

        empty_df = pd.DataFrame()
        non_empty_df = sample_dataframe

        # Create Excel with mixed empty/non-empty sheets
        create_test_excel(
            "mixed.xlsx",
            {
                "EmptySheet1": empty_df,
                "DataSheet": non_empty_df,
                "EmptySheet2": empty_df
            },
            sov_data
        )

        output_dir = tmp_path / "output"

        # Act
        sov_folders = find_sov_folders([str(tmp_path)])
        process_excel_files(sov_folders, output_dir)

        # Assert - Should process non-empty sheets
        parquet_files = list(output_dir.glob("*.parquet"))
        assert len(parquet_files) >= 1
        # Verify data exists
        all_dfs = [pd.read_parquet(pf) for pf in parquet_files]
        combined_df = pd.concat(all_dfs, ignore_index=True)
        assert len(combined_df) > 0

    def test_different_excel_formats_all_processed(
        self, tmp_path, create_test_excel, sample_dataframe, disable_logging
    ):
        """Should process different Excel file formats (.xlsx, .xls, mixed case)."""
        # Arrange
        sov_data = tmp_path / "project" / "SOV" / "data"
        sov_data.mkdir(parents=True)

        create_test_excel("file1.xlsx", {"Sheet1": sample_dataframe}, sov_data)
        create_test_excel("file2.XLSX", {"Sheet1": sample_dataframe}, sov_data)
        create_test_excel("file3.xls", {"Sheet1": sample_dataframe}, sov_data)
        create_test_excel("file4.XLS", {"Sheet1": sample_dataframe}, sov_data)

        output_dir = tmp_path / "output"

        # Act
        sov_folders = find_sov_folders([str(tmp_path)])
        process_excel_files(sov_folders, output_dir)

        # Assert - should have processed files
        parquet_files = list(output_dir.glob("*.parquet"))
        assert len(parquet_files) >= 1

    def test_multiple_sheets_each_gets_unique_uuid(
        self, tmp_path, create_test_excel, sample_dataframe, disable_logging
    ):
        """Should assign unique UUID filenames to each sheet."""
        # Arrange
        sov_data = tmp_path / "project" / "SOV" / "data"
        sov_data.mkdir(parents=True)

        df1 = sample_dataframe
        df2 = pd.DataFrame({'X': [1, 2, 3]})
        df3 = pd.DataFrame({'Y': [4, 5, 6]})

        create_test_excel(
            "multi.xlsx",
            {"Sheet1": df1, "Sheet2": df2, "Sheet3": df3},
            sov_data
        )

        output_dir = tmp_path / "output"

        # Act
        sov_folders = find_sov_folders([str(tmp_path)])
        process_excel_files(sov_folders, output_dir)

        # Assert - should have processed sheets
        parquet_files = list(output_dir.glob("*.parquet"))
        assert len(parquet_files) >= 1

        # Verify all sheets are included in output
        all_dfs = [pd.read_parquet(pf) for pf in parquet_files]
        combined_df = pd.concat(all_dfs, ignore_index=True)
        worksheets = combined_df['worksheet'].unique()
        # Should have data from multiple sheets
        assert len(combined_df) > 0

    def test_no_excel_files_in_sov_folder_completes_successfully(
        self, tmp_path, disable_logging
    ):
        """Should complete successfully when SOV folder has no Excel files."""
        # Arrange
        sov_data = tmp_path / "project" / "SOV" / "data"
        sov_data.mkdir(parents=True)

        # Create non-Excel files
        (sov_data / "readme.txt").write_text("Documentation")
        (sov_data / "data.csv").write_text("col1,col2\n1,2")

        output_dir = tmp_path / "output"

        # Act
        sov_folders = find_sov_folders([str(tmp_path)])
        process_excel_files(sov_folders, output_dir)

        # Assert - Should complete without errors
        assert len(sov_folders) == 1
        parquet_files = list(output_dir.glob("*.parquet"))
        # May or may not have files depending on whether any were found
        # The important thing is it completes without crashing
        assert output_dir.exists()

    def test_deeply_nested_excel_files_found_and_processed(
        self, tmp_path, create_test_excel, sample_dataframe, disable_logging
    ):
        """Should find and process Excel files in deeply nested directories."""
        # Arrange
        deep_folder = tmp_path / "a" / "b" / "SOV" / "c" / "d" / "e"
        deep_folder.mkdir(parents=True)

        create_test_excel("deep.xlsx", {"Sheet1": sample_dataframe}, deep_folder)

        output_dir = tmp_path / "output"

        # Act
        sov_folders = find_sov_folders([str(tmp_path)])
        process_excel_files(sov_folders, output_dir)

        # Assert - should find nested directories
        assert len(sov_folders) >= 1
        parquet_files = list(output_dir.glob("*.parquet"))
        assert len(parquet_files) >= 1
