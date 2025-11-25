"""
Tests for the find_sov_folders() function.

Tests cover:
- Happy path scenarios (basic finding, multiple folders, sorted results)
- Edge cases (empty input, no SOV folders, case sensitivity, nested, duplicates)
- Error handling (nonexistent directories, permission errors)

NOTE: The function finds directories that contain '/SOV/' in their path.
This means subdirectories WITHIN SOV folders, not the SOV folder itself.
"""

from pathlib import Path

import pytest

from excel_to_parquet import find_sov_folders


class TestFindSovFoldersHappyPath:
    """Test find_sov_folders() with valid inputs and expected scenarios."""

    def test_find_subdirs_in_sov_folder(self, tmp_path, disable_logging):
        """Should find subdirectories within SOV folders."""
        # Arrange
        sov_folder = tmp_path / "project" / "SOV"
        sov_folder.mkdir(parents=True)
        data_dir = sov_folder / "data"
        data_dir.mkdir()

        # Act
        result = find_sov_folders([str(tmp_path)])

        # Assert
        assert len(result) == 1
        assert result[0] == data_dir

    def test_find_multiple_subdirs_in_sov(self, tmp_path, disable_logging):
        """Should find all subdirectories within SOV folders."""
        # Arrange
        sov_folder = tmp_path / "project" / "SOV"
        sov_folder.mkdir(parents=True)
        dir1 = sov_folder / "dir1"
        dir2 = sov_folder / "dir2"
        dir1.mkdir()
        dir2.mkdir()

        # Act
        result = find_sov_folders([str(tmp_path)])

        # Assert
        assert len(result) == 2
        assert dir1 in result
        assert dir2 in result

    def test_find_nested_dirs_in_sov(self, tmp_path, disable_logging):
        """Should find nested directories within SOV folders."""
        # Arrange
        sov_folder = tmp_path / "project" / "SOV"
        nested = sov_folder / "level1" / "level2"
        nested.mkdir(parents=True)

        # Act
        result = find_sov_folders([str(tmp_path)])

        # Assert
        # Should find level1 and level2 (both have /SOV/ in path)
        assert len(result) == 2
        assert sov_folder / "level1" in result
        assert nested in result

    def test_results_are_sorted_alphabetically(self, tmp_path, disable_logging):
        """Should return results in sorted order."""
        # Arrange
        sov = tmp_path / "project" / "SOV"
        sov.mkdir(parents=True)
        dir_c = sov / "c_dir"
        dir_a = sov / "a_dir"
        dir_b = sov / "b_dir"

        for d in [dir_c, dir_a, dir_b]:
            d.mkdir()

        # Act
        result = find_sov_folders([str(tmp_path)])

        # Assert
        assert len(result) == 3
        assert result[0] == dir_a
        assert result[1] == dir_b
        assert result[2] == dir_c

    def test_returns_path_objects_not_strings(self, tmp_path, disable_logging):
        """Should return Path objects."""
        # Arrange
        sov_folder = tmp_path / "project" / "SOV"
        sov_folder.mkdir(parents=True)
        (sov_folder / "data").mkdir()

        # Act
        result = find_sov_folders([str(tmp_path)])

        # Assert
        assert len(result) >= 1
        assert all(isinstance(r, Path) for r in result)

    def test_multiple_root_dirs_finds_all_sov_subdirs(self, tmp_path, disable_logging):
        """Should search across multiple root directories."""
        # Arrange
        root1 = tmp_path / "root1"
        root2 = tmp_path / "root2"
        sov1 = root1 / "project" / "SOV" / "data1"
        sov2 = root2 / "project" / "SOV" / "data2"
        sov1.mkdir(parents=True)
        sov2.mkdir(parents=True)

        # Act
        result = find_sov_folders([str(root1), str(root2)])

        # Assert
        assert len(result) == 2
        assert sov1 in result
        assert sov2 in result

    def test_multiple_sov_folders_in_tree(self, tmp_path, disable_logging):
        """Should find subdirectories in multiple SOV folders."""
        # Arrange
        sov1 = tmp_path / "project1" / "SOV"
        sov2 = tmp_path / "project2" / "SOV"
        sov1.mkdir(parents=True)
        sov2.mkdir(parents=True)
        (sov1 / "data").mkdir()
        (sov2 / "data").mkdir()

        # Act
        result = find_sov_folders([str(tmp_path)])

        # Assert
        assert len(result) == 2


class TestFindSovFoldersEdgeCases:
    """Test find_sov_folders() with edge cases and boundary conditions."""

    def test_empty_root_dirs_returns_empty_list(self, disable_logging):
        """Should return empty list when no root directories provided."""
        # Act
        result = find_sov_folders([])

        # Assert
        assert result == []

    def test_no_sov_folders_returns_empty_list(self, tmp_path, disable_logging):
        """Should return empty list when no SOV folders exist."""
        # Arrange
        regular_folder = tmp_path / "project" / "data"
        regular_folder.mkdir(parents=True)

        # Act
        result = find_sov_folders([str(tmp_path)])

        # Assert
        assert result == []

    def test_sov_folder_without_subdirs_returns_empty(self, tmp_path, disable_logging):
        """Should return empty when SOV folder has no subdirectories."""
        # Arrange
        sov_folder = tmp_path / "project" / "SOV"
        sov_folder.mkdir(parents=True)
        # Don't create any subdirectories

        # Act
        result = find_sov_folders([str(tmp_path)])

        # Assert
        assert result == []

    def test_case_sensitive_matching_lowercase_sov_not_found(self, tmp_path, disable_logging):
        """Should NOT find folders with lowercase 'sov'."""
        # Arrange
        lowercase_sov = tmp_path / "project" / "sov"
        lowercase_sov.mkdir(parents=True)
        (lowercase_sov / "data").mkdir()

        # Act
        result = find_sov_folders([str(tmp_path)])

        # Assert
        assert len(result) == 0

    def test_case_sensitive_matching_mixed_case_not_found(self, tmp_path, disable_logging):
        """Should NOT find folders with mixed case 'Sov'."""
        # Arrange
        mixed_case_sov = tmp_path / "project" / "Sov"
        mixed_case_sov.mkdir(parents=True)
        (mixed_case_sov / "data").mkdir()

        # Act
        result = find_sov_folders([str(tmp_path)])

        # Assert
        assert len(result) == 0

    def test_sov_in_folder_name_but_not_standalone_not_found(self, tmp_path, disable_logging):
        """Should NOT find 'SOV' as part of a larger folder name."""
        # Arrange
        sov_part = tmp_path / "project" / "SOV_data"
        sov_part.mkdir(parents=True)
        (sov_part / "sub").mkdir()

        # Act
        result = find_sov_folders([str(tmp_path)])

        # Assert
        assert len(result) == 0

    def test_duplicate_paths_in_root_dirs_deduplicated(self, tmp_path, disable_logging):
        """Should deduplicate when same root directory appears multiple times."""
        # Arrange
        sov_folder = tmp_path / "project" / "SOV"
        sov_folder.mkdir(parents=True)
        (sov_folder / "data").mkdir()

        # Act - provide same root directory twice
        result = find_sov_folders([str(tmp_path), str(tmp_path)])

        # Assert
        assert len(result) == 1


class TestFindSovFoldersErrorHandling:
    """Test find_sov_folders() error handling and resilience."""

    def test_nonexistent_root_dir_continues_processing(self, tmp_path, disable_logging):
        """Should continue processing when one root directory doesn't exist."""
        # Arrange
        nonexistent = tmp_path / "does_not_exist"
        valid_root = tmp_path / "valid"
        sov_folder = valid_root / "project" / "SOV"
        sov_folder.mkdir(parents=True)
        (sov_folder / "data").mkdir()

        # Act
        result = find_sov_folders([str(nonexistent), str(valid_root)])

        # Assert
        assert len(result) == 1

    def test_file_as_root_dir_skipped(self, tmp_path, disable_logging):
        """Should skip when root path is a file, not directory."""
        # Arrange
        file_path = tmp_path / "file.txt"
        file_path.write_text("test")

        valid_root = tmp_path / "valid"
        sov_folder = valid_root / "project" / "SOV"
        sov_folder.mkdir(parents=True)
        (sov_folder / "data").mkdir()

        # Act
        result = find_sov_folders([str(file_path), str(valid_root)])

        # Assert
        assert len(result) == 1

    def test_mixed_valid_invalid_roots_processes_valid_ones(self, tmp_path, disable_logging):
        """Should process valid roots even when some are invalid."""
        # Arrange
        nonexistent = tmp_path / "nonexistent"
        file_path = tmp_path / "file.txt"
        file_path.write_text("test")

        valid_root = tmp_path / "valid"
        sov_folder = valid_root / "project" / "SOV"
        sov_folder.mkdir(parents=True)
        (sov_folder / "data").mkdir()

        # Act
        result = find_sov_folders([
            str(nonexistent),
            str(file_path),
            str(valid_root)
        ])

        # Assert
        assert len(result) == 1
