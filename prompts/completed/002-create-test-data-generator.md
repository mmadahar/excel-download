<objective>
Create a test data generator that produces 20 Excel spreadsheets with realistic tabular data that starts on random rows (1-20) with clear header rows.

These test files will be used to verify the Excel-to-Parquet conversion pipeline handles real-world data patterns where data doesn't always start at row 1.
</objective>

<context>
The excel_to_parquet.py tool processes Excel files with `has_header=False` and unpivots data to long format. Test data should exercise scenarios where:
- Data starts at various row offsets (simulating exported reports with titles/metadata above)
- Headers are recognizable column names
- Data contains mixed types (strings, numbers, dates)

Read CLAUDE.md for project conventions and existing test patterns.
</context>

<requirements>
1. Create a script `generate_test_data.py` in the project root
2. Generate 20 Excel files in `data/test_excel/` directory
3. Each file should have:
   - A random starting row between 1 and 20
   - Empty or title rows above the data (if start row > 1)
   - An obvious header row with descriptive column names
   - 10-50 rows of random tabular data below the header
   - 5-10 columns with varied data types
4. Data themes to include (vary across files):
   - Financial: invoices, transactions, account balances
   - Inventory: products, quantities, SKUs, prices
   - Personnel: employees, departments, salaries
   - Sales: orders, customers, revenue
5. Use appropriate libraries: openpyxl for Excel creation, Faker for realistic data
</requirements>

<implementation>
Create the generator with these functions:

```python
def generate_header_row(theme: str) -> list[str]:
    """Return appropriate column headers for the data theme."""

def generate_data_rows(theme: str, num_rows: int, num_cols: int) -> list[list]:
    """Generate random but realistic data matching the theme."""

def create_excel_file(output_path: Path, start_row: int, theme: str):
    """Create an Excel file with data starting at specified row."""

def main():
    """Generate 20 test Excel files with varied configurations."""
```

WHY start_row matters: Real-world Excel exports often have report titles, 
metadata, or blank rows before the actual data. The conversion tool needs 
to handle this gracefully.
</implementation>

<output>
Create/modify files:
- `./generate_test_data.py` - Main generator script
- `./data/test_excel/` - Directory containing 20 generated Excel files

The script should be runnable with: `uv run python generate_test_data.py`
</output>

<verification>
Before declaring complete, verify:
1. Run `uv run python generate_test_data.py` successfully
2. Confirm 20 .xlsx files exist in `data/test_excel/`
3. Manually inspect 2-3 files to verify:
   - Data starts at varied rows
   - Headers are clear and descriptive
   - Data looks realistic for its theme
4. Run the main tool against test data:
   `uv run python excel_to_parquet.py data/test_excel -o data/test_output`
</verification>

<success_criteria>
- 20 Excel files generated with varied start rows (1-20)
- Each file has recognizable headers and realistic tabular data
- Files span multiple data themes (financial, inventory, personnel, sales)
- Generator script is clean, well-documented, and rerunnable
- Main conversion tool processes all files without errors
</success_criteria>
