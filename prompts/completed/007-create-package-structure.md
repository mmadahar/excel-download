<objective>
Create the src/excel_converter/ package structure and move Python source files into it.

This is step 1 of a full codebase restructuring. The goal is to establish a proper Python package structure that will make the codebase more maintainable and follow Python best practices.
</objective>

<context>
Current state: Python files are scattered at the project root:
- `excel_to_parquet.py` - Main CLI tool with scanning, caching, SOV folder detection
- `excel_to_parquet_polars.py` - Standalone converter for explicit file lists
- `tui.py` - Interactive Textual TUI application
- `generate_test_data.py` - Test data generation utility
- `main.py` - Minimal entry point (likely unused)

Target structure:
```
src/
  excel_converter/
    __init__.py           # Package init, version info
    cli.py                # CLI entry point (from excel_to_parquet.py)
    converter.py          # Standalone converter (from excel_to_parquet_polars.py)
    tui.py                # TUI application
    utils/
      __init__.py
      test_data.py        # Test data generator (from generate_test_data.py)
```

Read CLAUDE.md first to understand project conventions.
</context>

<requirements>
1. Create the directory structure:
   - `src/excel_converter/`
   - `src/excel_converter/utils/`

2. Create `src/excel_converter/__init__.py` with:
   - Package version (extract from pyproject.toml or set to "0.1.0")
   - Brief docstring describing the package

3. Move and rename files:
   - `excel_to_parquet.py` → `src/excel_converter/cli.py`
   - `excel_to_parquet_polars.py` → `src/excel_converter/converter.py`
   - `tui.py` → `src/excel_converter/tui.py`
   - `generate_test_data.py` → `src/excel_converter/utils/test_data.py`

4. Create `src/excel_converter/utils/__init__.py`

5. Delete `main.py` if it's unused (check contents first)

6. Move `tui.tcss` to `src/excel_converter/tui.tcss`
</requirements>

<constraints>
- DO NOT update imports yet - that's handled in the next prompt
- DO NOT modify file contents except for creating __init__.py files
- Keep original files after copying until imports are verified working
- The moves should be done with git mv to preserve history
</constraints>

<output>
Use git mv commands to move files:
```bash
git mv excel_to_parquet.py src/excel_converter/cli.py
git mv excel_to_parquet_polars.py src/excel_converter/converter.py
# etc.
```

Create __init__.py files using Write tool.
</output>

<verification>
After completing:
1. Verify directory structure exists: `ls -la src/excel_converter/`
2. Verify utils directory: `ls -la src/excel_converter/utils/`
3. Run `git status` to confirm moves are staged
</verification>

<success_criteria>
- src/excel_converter/ package structure created
- All Python source files moved to appropriate locations
- __init__.py files created for package and utils subpackage
- Original root-level .py files no longer present (except test files)
- Changes tracked by git
</success_criteria>
