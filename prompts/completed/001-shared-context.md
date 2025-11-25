<objective>
Establish shared knowledge and project context for the Excel-to-Parquet conversion pipeline.

This document provides foundational context that all subsequent prompts reference. Read and internalize this before proceeding with any step.
</objective>

<project_overview>
You are building an Excel-to-Parquet conversion tool in Python. The tool:
1. Recursively searches directories for folders containing "/SOV/" in their path
2. Finds all Excel files (.xlsx, .xls) within those SOV folders
3. Converts each Excel sheet to a separate Parquet file with UUID naming
4. Adds metadata columns (file_path, row_number) to track data lineage
5. Provides a CLI interface with logging and error handling
</project_overview>

<architecture>
```
excel_to_parquet.py (main module)
├── find_sov_folders(root_dirs: List[str]) -> List[Path]
├── process_excel_files(sov_folders: List[Path], output_dir: Path) -> None
├── setup_logging(log_level: str, log_file: Optional[str]) -> None
├── validate_inputs(root_dirs: List[str], output: str) -> None
└── main() -> int

tests/
├── conftest.py (shared fixtures)
├── test_find_sov_folders.py
├── test_process_excel_files.py
├── test_main.py
└── test_integration.py
```
</architecture>

<data_flow>
```
CLI Arguments (root_dirs, output_dir)
        │
        ▼
┌─────────────────────┐
│  find_sov_folders() │  ─── Input: List[str] of root directories
│                     │  ─── Output: List[Path] of folders with "/SOV/" in path
└─────────────────────┘
        │
        ▼
┌─────────────────────┐
│ process_excel_files │  ─── Input: List[Path] of SOV folders, Path output_dir
│                     │  ─── Effect: Creates Parquet files with UUID names
└─────────────────────┘
        │
        ▼
Output: UUID-named Parquet files with metadata columns
```
</data_flow>

<tech_stack>
- Python 3.8+
- pathlib (file system operations - NO os.walk)
- pandas (DataFrame operations, Excel reading)
- openpyxl (Excel engine)
- argparse (CLI)
- logging (standard library)
- uuid (filename generation)
- pytest + pytest-cov (testing)
</tech_stack>

<critical_requirements>
1. **pathlib ONLY**: Use pathlib for all path operations. No os.walk(), no os.path.
2. **Cross-platform paths**: Use `.as_posix()` when checking for "/SOV/" in paths
3. **header=None**: Read Excel files without assuming headers exist
4. **UUID filenames**: All Parquet output files use uuid4() naming
5. **Metadata columns**: Every DataFrame gets file_path and row_number columns FIRST
6. **Fault tolerance**: Never crash the pipeline on individual file errors
7. **Comprehensive logging**: INFO for progress, WARNING for skipped items, ERROR for failures
</critical_requirements>

<code_quality_standards>
- PEP 8 compliance (max 79 chars per line)
- Complete type hints on all functions
- Docstrings explaining WHY, not just WHAT
- Meaningful variable names (candidate_folder, not f)
- Context managers for file handles
- Explicit error handling with specific exception types
</code_quality_standards>

<exit_codes>
EXIT_SUCCESS = 0          # Successful completion
EXIT_USER_ERROR = 1       # Invalid arguments, missing directories
EXIT_PROCESSING_ERROR = 2 # Processing failures (not user's fault)
EXIT_UNEXPECTED_ERROR = 3 # Unhandled exceptions
</exit_codes>

<logging_format>
Format: '%(asctime)s - %(name)s - %(levelname)s - %(message)s'
Date format: '%Y-%m-%d %H:%M:%S'

Usage patterns:
- logger.info(): Start/end of major operations, counts, summaries
- logger.warning(): Empty sheets, skipped items, non-fatal issues
- logger.error(): File failures, permission issues, exceptions
- logger.debug(): Per-file progress, detailed diagnostics
</logging_format>

<testing_requirements>
- Target: 90%+ code coverage
- Use tmp_path fixture for file system tests
- Use monkeypatch for mocking
- Test all error paths explicitly
- Integration tests for full pipeline
- Fast execution (<5 seconds total)
</testing_requirements>

<reference_this_document>
All step prompts (002-005) reference this shared context. Before implementing any step:
1. Read this document to understand the full system
2. Review where your step fits in the pipeline
3. Follow the code quality standards consistently
4. Ensure your output integrates with adjacent steps
</reference_this_document>
