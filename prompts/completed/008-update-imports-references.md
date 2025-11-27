<objective>
Update all imports and references after the package restructure to make the codebase functional again.

This is step 2 of the restructuring. The files have been moved to src/excel_converter/, and now all internal imports and cross-references must be updated.
</objective>

<context>
Previous step moved files to:
- `src/excel_converter/cli.py` (was excel_to_parquet.py)
- `src/excel_converter/converter.py` (was excel_to_parquet_polars.py)
- `src/excel_converter/tui.py` (was tui.py)
- `src/excel_converter/utils/test_data.py` (was generate_test_data.py)
- `src/excel_converter/tui.tcss` (was tui.tcss)

Read CLAUDE.md for project conventions. Pay attention to:
- How modules currently import from each other
- The TUI imports functions from cli.py (formerly excel_to_parquet.py)
</context>

<requirements>
1. Update `src/excel_converter/tui.py`:
   - Change imports from `excel_to_parquet` to relative imports from `.cli`
   - Update the CSS path reference to point to the new location
   - Example: `from excel_to_parquet import scan_for_excel_files` becomes `from .cli import scan_for_excel_files`

2. Update `src/excel_converter/cli.py`:
   - If it imports from other modules, update to relative imports
   - Ensure the `if __name__ == "__main__"` block still works

3. Update `src/excel_converter/converter.py`:
   - Update any imports if present
   - Ensure standalone execution still works

4. Update `pyproject.toml`:
   - Add package configuration for src layout
   - Add entry points/scripts for CLI access:
     ```toml
     [project.scripts]
     excel-converter = "excel_converter.cli:main"
     excel-tui = "excel_converter.tui:main"
     ```
   - Ensure package is discoverable

5. Create wrapper scripts at root (optional, for backwards compatibility):
   - Simple scripts that import and run from the package
</requirements>

<implementation>
For relative imports within the package, use:
- `from .module import function` for same-level imports
- `from .subpackage.module import function` for subpackage imports
- `from . import module` for importing whole modules

For the CSS path in tui.py, use `Path(__file__).parent / "tui.tcss"` pattern.
</implementation>

<output>
Modify files in place using the Edit tool.
Update pyproject.toml with proper package configuration.
</output>

<verification>
After completing, verify the package works:

1. Test imports work:
   ```bash
   uv run python -c "from excel_converter import cli; print('cli ok')"
   uv run python -c "from excel_converter import tui; print('tui ok')"
   uv run python -c "from excel_converter import converter; print('converter ok')"
   ```

2. Test CLI still runs:
   ```bash
   uv run python -m excel_converter.cli --help
   ```

3. Test TUI can start (may need to Ctrl+C out):
   ```bash
   uv run python -m excel_converter.tui
   ```
</verification>

<success_criteria>
- All internal imports use relative import syntax
- pyproject.toml configured for src layout
- `uv run python -c "from excel_converter import cli"` works without error
- CLI help command works
- TUI can start without import errors
</success_criteria>
