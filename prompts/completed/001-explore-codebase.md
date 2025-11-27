<objective>
Explore the excel-download codebase to understand its architecture, data flow, and current functionality.

This exploration will provide context for subsequent prompts that add test data generation and a TUI interface.
</objective>

<context>
This is an Excel-to-Parquet conversion tool that:
- Scans directories for Excel files
- Converts Excel sheets to Parquet format with metadata
- Uses Polars for data processing

Read CLAUDE.md first for project conventions and commands.
</context>

<exploration_tasks>
1. Read and understand the main script structure in `excel_to_parquet.py`
2. Examine the test structure in `tests/` to understand testing patterns
3. Review `pyproject.toml` for dependencies and project configuration
4. Check for any existing data in `data/` directory
5. Understand the file scanning and conversion pipeline
</exploration_tasks>

<output>
Provide a concise summary covering:
- Core functions and their responsibilities
- Data flow from input to output
- Current test coverage approach
- Key dependencies (Polars, openpyxl, etc.)
- Entry points and CLI arguments
</output>

<success_criteria>
- All major functions documented
- Data flow clearly explained
- Dependencies identified
- Test patterns understood
</success_criteria>
