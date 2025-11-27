<objective>
Document the CLI tools for the Excel-to-Parquet converter.

Create comprehensive documentation of both CLI entry points, their arguments, and usage patterns. This will be used as source material for the README.md file.
</objective>

<context>
This project has two CLI tools:
1. `excel_to_parquet.py` - Main CLI with directory scanning, caching, and SOV folder detection
2. `excel_to_parquet_polars.py` - Standalone converter for explicit file lists (no scanning/caching)

Read these files to understand the implementations:
- @excel_to_parquet.py - Main CLI tool
- @excel_to_parquet_polars.py - Standalone converter
</context>

<requirements>
For each CLI tool, document:

1. **Purpose and use case** - When to use this tool vs the other
2. **Command-line arguments** - All arguments with descriptions
   - Required vs optional
   - Default values
   - Data types and validation
3. **Usage examples** - Real-world command examples
   - Basic usage
   - Advanced usage with all options
   - Common workflows
4. **Exit codes** - What each exit code means
5. **Key differences** - Side-by-side comparison table

Also document:
- Logging configuration options
- How caching works (files.csv)
- The --rescan flag behavior
- Engine selection for different Excel formats
</requirements>

<output>
Save documentation to: `./prompts/completed/002-cli-documentation.md`

Structure the output as:
```markdown
# CLI Documentation

## Overview
[When to use which tool]

## excel_to_parquet.py (Main CLI)

### Purpose
[Description]

### Arguments
| Argument | Short | Required | Default | Description |
|----------|-------|----------|---------|-------------|
[Table...]

### Usage Examples
[Examples with explanations]

### Exit Codes
[Table of codes and meanings]

## excel_to_parquet_polars.py (Standalone)

[Same structure...]

## Comparison Table
[Side-by-side feature comparison]

## Configuration Details
### Caching
### Logging
### Engine Selection
```
</output>

<verification>
Before completing, verify:
- Both CLI tools are fully documented
- All arguments are listed with correct defaults
- Examples are runnable commands (use uv run python ...)
- Exit codes are complete
- Comparison table clearly shows when to use each tool
</verification>
