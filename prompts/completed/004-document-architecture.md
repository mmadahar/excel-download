<objective>
Document the architecture and data flow for the Excel-to-Parquet converter.

Create comprehensive documentation of the system architecture, core functions, and data transformations. This will be used as source material for the README.md file.
</objective>

<context>
This project converts Excel files to Parquet format with a specific focus on SOV (Statement of Value) folders. It has multiple entry points and uses Polars for data processing.

Read these files to understand the architecture:
- @excel_to_parquet.py - Main module with core functions
- @excel_to_parquet_polars.py - Standalone converter
- @pyproject.toml - Dependencies and project metadata
- @CLAUDE.md - Existing architecture notes
</context>

<requirements>
Document:

1. **High-level architecture**
   - Entry points and when to use each
   - Module dependencies diagram
   - How modules relate to each other

2. **Data flow pipeline**
   - Discovery phase (scanning, caching)
   - SOV folder location
   - Processing phase (reading, unpivoting, saving)
   - ASCII diagram showing the flow

3. **Core functions reference**
   - For each key function: signature, purpose, key behaviors, example
   - Functions to document:
     - find_sov_folders()
     - scan_for_excel_files()
     - load_or_scan_files()
     - get_processed_file_paths()
     - process_excel_files()
     - validate_inputs()
     - setup_logging()

4. **Output schema**
   - The 6-column Parquet schema explained
   - Why each column exists
   - Example data

5. **Design decisions**
   - Why Polars over Pandas?
   - Why UUID filenames?
   - Why case-sensitive /SOV/?
   - Why header=False?
   - Why unpivot to long format?
   - Why ThreadPoolExecutor?

6. **Dependencies**
   - Each dependency and its purpose
   - Engine selection for Excel formats
</requirements>

<output>
Save documentation to: `./prompts/completed/004-architecture-documentation.md`

Structure the output as:
```markdown
# Architecture Documentation

## Overview
[High-level description]

## Entry Points
| Script | Purpose | When to Use |
[Table...]

## Data Flow Pipeline
```
[ASCII diagram]
```

### Phase 1: Discovery
[Details...]

### Phase 2: SOV Location
[Details...]

### Phase 3: Processing
[Details...]

## Core Functions Reference

### find_sov_folders()
- **Signature**: `find_sov_folders(root_dirs: List[str], ...) -> List[Path]`
- **Purpose**: [description]
- **Key behaviors**: [list]
- **Example**: [code]

[etc. for each function]

## Output Schema
| Column | Type | Description |
[Table with examples]

## Design Decisions
[Each decision with rationale]

## Dependencies
| Package | Version | Purpose |
[Table...]
```
</output>

<verification>
Before completing, verify:
- All core functions are documented with accurate signatures
- Data flow diagram is clear and complete
- Design decisions explain the WHY, not just the WHAT
- Output schema includes concrete examples
- Dependencies list matches pyproject.toml
</verification>
