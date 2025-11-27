"""
Tests for main(), validate_inputs(), and setup_logging() functions.

Tests cover:
- Input validation (valid inputs, nonexistent paths, files as roots)
- Logging setup (log levels, file handlers)
- Main function (success, errors, keyboard interrupt, exit codes)
"""

import logging
import os
from pathlib import Path
from unittest.mock import patch

import pytest

from excel_converter.cli import (
    EXIT_SUCCESS,
    EXIT_USER_ERROR,
    EXIT_UNEXPECTED_ERROR,
    main,
    setup_logging,
    validate_inputs,
)


class TestValidateInputs:
    """Test validate_inputs() function."""

    def test_valid_inputs_pass_without_error(self, tmp_path):
        """Should pass validation with valid root and output directories."""
        # Arrange
        root_dir = tmp_path / "root"
        root_dir.mkdir()
        output_dir = tmp_path / "output"

        # Act & Assert - should not raise
        validate_inputs([str(root_dir)], str(output_dir))

    def test_multiple_valid_roots_pass(self, tmp_path):
        """Should pass validation with multiple valid root directories."""
        # Arrange
        root1 = tmp_path / "root1"
        root2 = tmp_path / "root2"
        root1.mkdir()
        root2.mkdir()
        output_dir = tmp_path / "output"

        # Act & Assert - should not raise
        validate_inputs([str(root1), str(root2)], str(output_dir))

    def test_nonexistent_root_raises_value_error(self, tmp_path):
        """Should raise ValueError when root directory doesn't exist."""
        # Arrange
        nonexistent = tmp_path / "does_not_exist"
        output_dir = tmp_path / "output"

        # Act & Assert
        with pytest.raises(ValueError, match="Root directory does not exist"):
            validate_inputs([str(nonexistent)], str(output_dir))

    def test_file_as_root_raises_value_error(self, tmp_path):
        """Should raise ValueError when root path is a file, not directory."""
        # Arrange
        file_path = tmp_path / "file.txt"
        file_path.write_text("test")
        output_dir = tmp_path / "output"

        # Act & Assert
        with pytest.raises(ValueError, match="Root path is not a directory"):
            validate_inputs([str(file_path)], str(output_dir))

    def test_creates_output_directory_if_not_exists(self, tmp_path):
        """Should create output directory if it doesn't exist."""
        # Arrange
        root_dir = tmp_path / "root"
        root_dir.mkdir()
        output_dir = tmp_path / "output"

        assert not output_dir.exists()

        # Act
        validate_inputs([str(root_dir)], str(output_dir))

        # Assert
        assert output_dir.exists()
        assert output_dir.is_dir()

    def test_existing_output_directory_passes(self, tmp_path):
        """Should pass validation when output directory already exists."""
        # Arrange
        root_dir = tmp_path / "root"
        output_dir = tmp_path / "output"
        root_dir.mkdir()
        output_dir.mkdir()

        # Act & Assert - should not raise
        validate_inputs([str(root_dir)], str(output_dir))

    def test_file_as_output_raises_value_error(self, tmp_path):
        """Should raise ValueError when output path is a file."""
        # Arrange
        root_dir = tmp_path / "root"
        root_dir.mkdir()
        output_file = tmp_path / "output.txt"
        output_file.write_text("test")

        # Act & Assert
        with pytest.raises(ValueError, match="Output path exists but is not a directory"):
            validate_inputs([str(root_dir)], str(output_file))


class TestSetupLogging:
    """Test setup_logging() function."""

    def test_sets_root_logger_level(self):
        """Should set the root logger to the specified level."""
        # Arrange
        original_level = logging.root.level

        try:
            # Act
            setup_logging('DEBUG')

            # Assert
            assert logging.root.level == logging.DEBUG

            # Test other levels
            setup_logging('WARNING')
            assert logging.root.level == logging.WARNING

        finally:
            # Cleanup
            logging.root.setLevel(original_level)
            logging.root.handlers.clear()

    def test_creates_console_handler(self):
        """Should create a console handler."""
        # Arrange
        original_handlers = logging.root.handlers.copy()

        try:
            # Act
            setup_logging('INFO')

            # Assert
            assert len(logging.root.handlers) > 0
            has_stream_handler = any(
                isinstance(h, logging.StreamHandler)
                for h in logging.root.handlers
            )
            assert has_stream_handler

        finally:
            # Cleanup
            logging.root.handlers = original_handlers

    def test_creates_file_handler_when_log_file_specified(self, tmp_path):
        """Should create a file handler when log_file is provided."""
        # Arrange
        log_file = tmp_path / "test.log"
        original_handlers = logging.root.handlers.copy()

        try:
            # Act
            setup_logging('INFO', str(log_file))

            # Assert
            assert len(logging.root.handlers) >= 2  # Console + file handler
            has_file_handler = any(
                isinstance(h, logging.FileHandler)
                for h in logging.root.handlers
            )
            assert has_file_handler
            assert log_file.exists()

        finally:
            # Cleanup
            logging.root.handlers = original_handlers

    def test_no_file_handler_when_log_file_not_specified(self):
        """Should not create file handler when log_file is None."""
        # Arrange
        original_handlers = logging.root.handlers.copy()

        try:
            # Act
            setup_logging('INFO', log_file=None)

            # Assert
            file_handlers = [
                h for h in logging.root.handlers
                if isinstance(h, logging.FileHandler)
            ]
            assert len(file_handlers) == 0

        finally:
            # Cleanup
            logging.root.handlers = original_handlers


class TestMain:
    """Test main() function and exit codes."""

    def test_success_returns_zero_exit_code(
        self, tmp_path, monkeypatch, disable_logging
    ):
        """Should return EXIT_SUCCESS when processing completes successfully."""
        # Arrange
        root_dir = tmp_path / "root"
        sov_folder = root_dir / "project" / "SOV"
        sov_folder.mkdir(parents=True)

        output_dir = tmp_path / "output"

        # Create a test Excel file
        import pandas as pd
        excel_file = sov_folder / "test.xlsx"
        df = pd.DataFrame({'A': [1, 2, 3]})
        df.to_excel(excel_file, index=False, header=False)

        # Mock sys.argv
        monkeypatch.setattr(
            'sys.argv',
            ['excel_to_parquet.py', str(root_dir), '--output', str(output_dir)]
        )

        # Act
        exit_code = main()

        # Assert
        assert exit_code == EXIT_SUCCESS

    def test_no_sov_folders_returns_success(
        self, tmp_path, monkeypatch, disable_logging
    ):
        """Should return EXIT_SUCCESS even when no SOV folders found."""
        # Arrange
        root_dir = tmp_path / "root"
        root_dir.mkdir()
        output_dir = tmp_path / "output"

        monkeypatch.setattr(
            'sys.argv',
            ['excel_to_parquet.py', str(root_dir), '--output', str(output_dir)]
        )

        # Act
        exit_code = main()

        # Assert
        assert exit_code == EXIT_SUCCESS

    def test_invalid_root_returns_user_error_code(
        self, tmp_path, monkeypatch, disable_logging
    ):
        """Should return EXIT_USER_ERROR when root directory doesn't exist."""
        # Arrange
        nonexistent = tmp_path / "nonexistent"
        output_dir = tmp_path / "output"

        monkeypatch.setattr(
            'sys.argv',
            ['excel_to_parquet.py', str(nonexistent), '--output', str(output_dir)]
        )

        # Act
        exit_code = main()

        # Assert
        assert exit_code == EXIT_USER_ERROR

    def test_keyboard_interrupt_returns_user_error_code(
        self, tmp_path, monkeypatch, disable_logging
    ):
        """Should return EXIT_USER_ERROR when user interrupts with Ctrl+C."""
        # Arrange
        root_dir = tmp_path / "root"
        root_dir.mkdir()
        output_dir = tmp_path / "output"

        monkeypatch.setattr(
            'sys.argv',
            ['excel_to_parquet.py', str(root_dir), '--output', str(output_dir)]
        )

        # Mock find_sov_folders to raise KeyboardInterrupt
        with patch('excel_converter.cli.find_sov_folders') as mock_find:
            mock_find.side_effect = KeyboardInterrupt()

            # Act
            exit_code = main()

            # Assert
            assert exit_code == EXIT_USER_ERROR

    def test_unexpected_error_returns_error_code(
        self, tmp_path, monkeypatch, disable_logging
    ):
        """Should return EXIT_UNEXPECTED_ERROR for unexpected exceptions."""
        # Arrange
        root_dir = tmp_path / "root"
        root_dir.mkdir()
        output_dir = tmp_path / "output"

        monkeypatch.setattr(
            'sys.argv',
            ['excel_to_parquet.py', str(root_dir), '--output', str(output_dir)]
        )

        # Mock find_sov_folders to raise unexpected exception
        with patch('excel_converter.cli.find_sov_folders') as mock_find:
            mock_find.side_effect = RuntimeError("Unexpected error")

            # Act
            exit_code = main()

            # Assert
            assert exit_code == EXIT_UNEXPECTED_ERROR

    def test_permission_error_returns_user_error_code(
        self, tmp_path, monkeypatch, disable_logging
    ):
        """Should return EXIT_USER_ERROR for permission errors."""
        # Arrange
        root_dir = tmp_path / "root"
        root_dir.mkdir()
        output_dir = tmp_path / "output"

        monkeypatch.setattr(
            'sys.argv',
            ['excel_to_parquet.py', str(root_dir), '--output', str(output_dir)]
        )

        # Mock validate_inputs to raise PermissionError
        with patch('excel_converter.cli.validate_inputs') as mock_validate:
            mock_validate.side_effect = PermissionError("Permission denied")

            # Act
            exit_code = main()

            # Assert
            assert exit_code == EXIT_USER_ERROR

    def test_logging_setup_called_with_correct_level(
        self, tmp_path, monkeypatch
    ):
        """Should call setup_logging with the specified log level."""
        # Arrange
        root_dir = tmp_path / "root"
        root_dir.mkdir()
        output_dir = tmp_path / "output"

        monkeypatch.setattr(
            'sys.argv',
            ['excel_to_parquet.py', str(root_dir), '--output', str(output_dir),
             '--log-level', 'DEBUG']
        )

        # Act
        with patch('excel_converter.cli.setup_logging') as mock_setup:
            with patch('excel_converter.cli.find_sov_folders', return_value=[]):
                main()

            # Assert
            mock_setup.assert_called_once_with('DEBUG', None)

    def test_log_file_argument_passed_to_setup_logging(
        self, tmp_path, monkeypatch
    ):
        """Should pass log file argument to setup_logging."""
        # Arrange
        root_dir = tmp_path / "root"
        root_dir.mkdir()
        output_dir = tmp_path / "output"
        log_file = tmp_path / "test.log"

        monkeypatch.setattr(
            'sys.argv',
            ['excel_to_parquet.py', str(root_dir), '--output', str(output_dir),
             '--log-file', str(log_file)]
        )

        # Act
        with patch('excel_converter.cli.setup_logging') as mock_setup:
            with patch('excel_converter.cli.find_sov_folders', return_value=[]):
                main()

            # Assert
            mock_setup.assert_called_once_with('INFO', str(log_file))
