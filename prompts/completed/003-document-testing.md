<objective>
Document the test suite for the Excel-to-Parquet converter.

Create comprehensive documentation of the test organization, fixtures, and coverage. This will be used as source material for the README.md file.
</objective>

<context>
This project has a pytest-based test suite in the `tests/` directory with shared fixtures in `conftest.py`.

Read these files to understand the test structure:
- @tests/conftest.py - Shared fixtures
- @tests/test_find_sov_folders.py - SOV folder discovery tests
- @tests/test_process_excel_files.py - Excel conversion tests
- @tests/test_main.py - CLI entry point tests
- @tests/test_integration.py - End-to-end pipeline tests
</context>

<requirements>
Document:

1. **Test organization pattern** - The HappyPath/EdgeCases/ErrorHandling structure
2. **How to run tests** - Commands for different scenarios
   - All tests
   - Single file
   - Single test
   - With coverage
   - Verbose output
3. **Shared fixtures** - Each fixture in conftest.py
   - Name and purpose
   - What it creates/provides
   - Example usage
4. **Test file breakdown** - For each test file:
   - What function(s) it tests
   - Number of tests per category
   - Key test scenarios covered
5. **Coverage information** - What areas have good/minimal coverage

</requirements>

<output>
Save documentation to: `./prompts/completed/003-testing-documentation.md`

Structure the output as:
```markdown
# Testing Documentation

## Test Organization
[Explanation of the naming convention and categories]

## Running Tests
```bash
# Commands with descriptions
```

## Shared Fixtures (conftest.py)

### sample_dataframe
[Description, what it provides, usage]

### create_test_excel
[Description, parameters, usage]

[etc.]

## Test Files

### test_find_sov_folders.py
- **Tests**: find_sov_folders()
- **HappyPath** (X tests): [what's covered]
- **EdgeCases** (X tests): [what's covered]
- **ErrorHandling** (X tests): [what's covered]

[etc. for each test file]

## Coverage Summary
[What's well-covered, what could use more tests]
```
</output>

<verification>
Before completing, verify:
- All test files are documented
- All fixtures are explained
- Test counts are accurate
- Running instructions work (test with uv run pytest --help if needed)
- Coverage summary is honest about gaps
</verification>
