<objective>
Reorganize the test suite to match the new package structure and ensure all tests pass.

This is step 3 of the restructuring. Tests need to be updated to import from the new package locations.
</objective>

<context>
Current test structure:
- `tests/` directory with proper test files
- `test_tui.py` at root level (should be moved into tests/)

New package structure:
- `src/excel_converter/cli.py`
- `src/excel_converter/converter.py`
- `src/excel_converter/tui.py`
- `src/excel_converter/utils/test_data.py`

Read CLAUDE.md for testing conventions. Tests follow pattern: `Test{FunctionName}{Category}` where category is HappyPath, EdgeCases, or ErrorHandling.
</context>

<requirements>
1. Move `test_tui.py` from root to `tests/test_tui.py`

2. Update all test file imports:
   - `tests/test_find_sov_folders.py` - update imports from excel_to_parquet
   - `tests/test_process_excel_files.py` - update imports
   - `tests/test_integration.py` - update imports
   - `tests/test_main.py` - update or remove if testing defunct main.py
   - `tests/test_tui.py` - update imports

3. Update `tests/conftest.py`:
   - Update any imports from the old module names
   - Ensure fixtures still work with new package structure

4. If `tests/test_main.py` was testing the old `main.py`, either:
   - Remove it if main.py was deleted
   - Or update it to test the new entry points
</requirements>

<implementation>
Import patterns to update:
- `from excel_to_parquet import function` → `from excel_converter.cli import function`
- `from excel_to_parquet_polars import function` → `from excel_converter.converter import function`
- `import excel_to_parquet` → `from excel_converter import cli`
- `from tui import ...` → `from excel_converter.tui import ...`
</implementation>

<output>
1. Use git mv to move test_tui.py
2. Use Edit tool to update imports in all test files
</output>

<verification>
Run the full test suite with coverage:
```bash
uv run pytest --cov -v
```

All tests should pass. If any fail, fix the issues before completing.

Also verify specific test files:
```bash
uv run pytest tests/test_find_sov_folders.py -v
uv run pytest tests/test_process_excel_files.py -v
```
</verification>

<success_criteria>
- All test files are in the tests/ directory
- All imports updated to use new package paths
- `uv run pytest --cov` passes with no failures
- Test coverage is maintained or improved
</success_criteria>
