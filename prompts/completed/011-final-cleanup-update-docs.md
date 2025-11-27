<objective>
Complete the restructuring by cleaning up the root directory, updating CLAUDE.md with new paths, and ensuring everything is properly documented.

This is the final step (step 5) of the restructuring. Clean up remaining loose ends and update project documentation to reflect the new structure.
</objective>

<context>
After previous steps, the structure should be:
```
src/
  excel_converter/
    __init__.py
    cli.py
    converter.py
    tui.py
    tui.tcss
    utils/
      __init__.py
      test_data.py
tests/
  conftest.py
  test_find_sov_folders.py
  test_process_excel_files.py
  test_integration.py
  test_tui.py
ai_docs/           # kept as-is per user request
data/              # runtime data directory
prompts/           # prompt files
```

Items that may need attention:
- Screenshot file at root
- .coverage file
- Any other loose files
- CLAUDE.md needs updated paths and commands
- .gitignore may need updates
</context>

<requirements>
1. Clean up root directory:
   - Move or delete the screenshot file (if not needed, delete; if documentation, move to docs/)
   - Ensure .coverage is in .gitignore
   - Remove any other unnecessary files

2. Update CLAUDE.md with:
   - New project structure section
   - Updated command examples reflecting new paths:
     ```bash
     # Run interactive TUI
     uv run python -m excel_converter.tui

     # Run CLI conversion
     uv run python -m excel_converter.cli /path/to/search -o /path/to/output

     # Or use entry points (if configured)
     uv run excel-converter /path/to/search -o /output
     uv run excel-tui
     ```
   - Updated architecture section with new file locations
   - Updated test commands if paths changed

3. Update .gitignore if needed:
   - Ensure .coverage is ignored
   - Ensure data/ contents are properly handled
   - Add any new patterns for src layout

4. Verify pyproject.toml is complete:
   - Has proper package discovery for src layout
   - Has entry point scripts defined
   - All dependencies are listed

5. Run final verification:
   - Run tests to ensure everything works
   - Try the CLI and TUI entry points
</requirements>

<output>
1. Use rm or git rm to remove unnecessary files
2. Use Edit tool to update CLAUDE.md
3. Use Edit tool to update .gitignore if needed
4. Verify with bash commands
</output>

<verification>
Final verification checklist:

1. Root directory is clean:
   ```bash
   ls -la  # Should show minimal files
   ```

2. Package works:
   ```bash
   uv run python -c "from excel_converter import cli, tui, converter; print('All imports OK')"
   ```

3. Tests pass:
   ```bash
   uv run pytest --cov -v
   ```

4. CLI works:
   ```bash
   uv run python -m excel_converter.cli --help
   ```

5. TUI starts (Ctrl+C to exit):
   ```bash
   uv run python -m excel_converter.tui
   ```

6. Git status is clean (or only expected changes):
   ```bash
   git status
   ```
</verification>

<success_criteria>
- Root directory contains only essential files (pyproject.toml, README.md, CLAUDE.md, .gitignore, uv.lock)
- CLAUDE.md accurately reflects new structure and commands
- All tests pass
- CLI and TUI work correctly
- Git history preserved for moved files
- Project is ready for use with new structure
</success_criteria>
