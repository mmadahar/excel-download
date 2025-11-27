<objective>
Assemble a comprehensive README.md for the Excel-to-Parquet converter.

Combine the documentation from the previous research prompts into a polished, well-structured README that serves both new users and contributors.
</objective>

<context>
Four documentation files have been created by previous prompts:
- @prompts/completed/001-tui-documentation.md - TUI screens and workflow
- @prompts/completed/002-cli-documentation.md - CLI tools and arguments
- @prompts/completed/003-testing-documentation.md - Test structure and coverage
- @prompts/completed/004-architecture-documentation.md - Architecture and data flow

Also review:
- @README.md - Existing README to understand current structure
- @CLAUDE.md - Project conventions
- @pyproject.toml - Version and metadata
</context>

<requirements>
Create a comprehensive README with these sections (in order):

1. **Header**
   - Project name with brief tagline
   - Badges: Python version (>=3.12), license (if specified)

2. **Overview** (2-3 paragraphs)
   - What the tool does
   - Key capabilities
   - Who it's for

3. **Features**
   - Bullet list of key features
   - Organized by category (Discovery, Processing, Output, Interface)

4. **Quick Start**
   - 5-step guide to get running with the TUI
   - Minimal, copy-paste friendly

5. **Installation**
   - Prerequisites (Python 3.12+, uv)
   - Clone and install steps

6. **Usage**
   - **TUI** - Brief intro + link to TUI section
   - **CLI (Main)** - Basic usage + common examples
   - **CLI (Standalone)** - When to use + examples

7. **How It Works**
   - Pipeline overview with ASCII diagram
   - Brief explanation of each phase

8. **Output Format**
   - Schema table with all 6 columns
   - Example output data

9. **TUI Guide**
   - Screen flow diagram
   - Key screens with ASCII mockups
   - Keyboard shortcuts table

10. **CLI Reference**
    - Arguments table for main CLI
    - Arguments table for standalone CLI
    - Exit codes table

11. **Architecture**
    - Entry points table
    - Data flow diagram
    - Core functions (brief, link to code)

12. **Testing**
    - How to run tests
    - Test organization overview
    - Fixtures reference

13. **Design Decisions**
    - Key decisions with brief rationale
    - Keep concise (1-2 sentences each)

14. **Troubleshooting**
    - Common issues and solutions
    - At least 5 common scenarios

15. **Contributing**
    - Development setup
    - Code style notes
    - Test requirements

16. **License**
    - State license or "Not specified"

Quality requirements:
- Use GitHub-flavored markdown
- Include table of contents with anchor links
- Keep ASCII diagrams readable (80 char max width)
- Examples should use `uv run python ...` format
- Cross-reference sections where helpful
</requirements>

<output>
Save the final README to: `./README.md`

This will replace the existing README.
</output>

<verification>
Before completing, verify:
- All 16 sections are present
- Table of contents links work
- All code examples are syntactically correct
- ASCII diagrams render properly in markdown
- No broken internal links
- Information is consistent across sections
- README would help a new user get started in under 5 minutes
</verification>

<success_criteria>
- Comprehensive coverage of all tool capabilities
- Clear progression from quick start to detailed reference
- Professional appearance suitable for GitHub
- Accurate reflection of the codebase
</success_criteria>
