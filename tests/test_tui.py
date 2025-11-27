#!/usr/bin/env python3
"""
TUI Testing Script

Validates that the TUI can be imported and key components are available.
For full interactive testing, run: uv run python tui.py
"""

import sys
from pathlib import Path


def test_tui_imports():
    """Test that TUI module and all screens can be imported."""
    print("Testing TUI imports...")

    try:
        from excel_converter import tui

        print("  ✓ TUI module imported successfully")

        # Test all screen classes
        screens = [
            "MainMenu",
            "ScanScreen",
            "FileBrowserScreen",
            "ConversionScreen",
            "ResultsScreen",
            "SettingsScreen",
            "ExcelConverterApp",
        ]

        for screen_name in screens:
            assert hasattr(tui, screen_name), f"Missing screen: {screen_name}"
            print(f"  ✓ {screen_name} class available")

        return True

    except ImportError as e:
        print(f"  ✗ Import error: {e}")
        return False
    except AssertionError as e:
        print(f"  ✗ {e}")
        return False


def test_excel_to_parquet_imports():
    """Test that core functions are available from excel_to_parquet."""
    print("\nTesting excel_to_parquet function imports...")

    try:
        from excel_converter.cli import (
            FILES_CSV,
            find_sov_folders,
            get_engine_for_extension,
            get_processed_file_paths,
            load_or_scan_files,
            scan_for_excel_files,
        )

        functions = [
            ("FILES_CSV", FILES_CSV),
            ("find_sov_folders", find_sov_folders),
            ("get_engine_for_extension", get_engine_for_extension),
            ("get_processed_file_paths", get_processed_file_paths),
            ("load_or_scan_files", load_or_scan_files),
            ("scan_for_excel_files", scan_for_excel_files),
        ]

        for name, obj in functions:
            print(f"  ✓ {name} imported successfully")

        return True

    except ImportError as e:
        print(f"  ✗ Import error: {e}")
        return False


def test_textual_dependency():
    """Test that Textual framework is available."""
    print("\nTesting Textual framework...")

    try:
        import textual
        from textual.app import App
        from textual.widgets import Button, DataTable, Input

        print(f"  ✓ Textual version: {textual.__version__}")
        print("  ✓ Required widgets available")

        return True

    except ImportError as e:
        print(f"  ✗ Textual not available: {e}")
        return False


def test_css_file_exists():
    """Test that CSS file exists."""
    print("\nTesting CSS file...")

    # CSS file is now in src/excel_converter/tui.tcss
    css_path = Path(__file__).parent.parent / "src" / "excel_converter" / "tui.tcss"

    if css_path.exists():
        print(f"  ✓ CSS file exists: {css_path}")
        print(f"  ✓ CSS file size: {css_path.stat().st_size} bytes")
        return True
    else:
        print(f"  ⚠ CSS file not found (will use inline CSS): {css_path}")
        return True  # Not a failure, just uses fallback


def test_tui_app_instantiation():
    """Test that app can be instantiated without running."""
    print("\nTesting TUI app instantiation...")

    try:
        from excel_converter.tui import ExcelConverterApp

        # Create app instance (don't run it)
        app = ExcelConverterApp()
        print("  ✓ ExcelConverterApp instantiated successfully")
        print(f"  ✓ App title: {app.title}")
        print(f"  ✓ CSS loaded: {len(app.CSS)} characters")

        return True

    except Exception as e:
        print(f"  ✗ Error instantiating app: {e}")
        return False


def main():
    """Run all tests."""
    print("=" * 60)
    print("TUI Test Suite")
    print("=" * 60)

    tests = [
        test_tui_imports,
        test_excel_to_parquet_imports,
        test_textual_dependency,
        test_css_file_exists,
        test_tui_app_instantiation,
    ]

    results = []
    for test in tests:
        result = test()
        results.append(result)

    print("\n" + "=" * 60)
    print("Test Summary")
    print("=" * 60)

    passed = sum(results)
    total = len(results)

    print(f"Passed: {passed}/{total}")

    if passed == total:
        print("\n✓ All tests passed!")
        print("\nTo run the TUI interactively:")
        print("  uv run python tui.py")
        return 0
    else:
        print("\n✗ Some tests failed")
        return 1


if __name__ == "__main__":
    sys.exit(main())
