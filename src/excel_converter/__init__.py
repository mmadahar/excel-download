"""
Excel Converter - Excel-to-Parquet conversion tool

Discovers Excel files (.xlsx, .xlsm, .xlsb, .xls), converts each sheet to
unpivoted long format, and saves as Parquet with metadata columns.

Key features:
- SOV folder detection and filtering
- Multiple Excel format support
- Unpivot to long format (file_path, file_name, worksheet, row, column, value)
- Caching and idempotent processing
- CLI and TUI interfaces
"""

__version__ = "0.1.0"

__all__ = ["__version__"]
