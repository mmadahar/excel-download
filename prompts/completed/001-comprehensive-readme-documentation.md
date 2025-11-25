<objective>
Explore this codebase thoroughly and update README.md to be comprehensive documentation.

The goal is to create documentation that helps new developers understand:
- What this project does
- How to install and use it
- The architecture and design decisions
- How to contribute and run tests
</objective>

<research>
Before writing, explore the codebase to understand:

1. Read @CLAUDE.md for existing project context and conventions
2. Examine @excel_to_parquet.py for:
   - All CLI arguments and options
   - Core functions and their purposes
   - Error handling and exit codes
   - Input/output formats
3. Review @pyproject.toml for:
   - Project metadata (name, version, description)
   - Dependencies
   - Python version requirements
4. Explore @tests/ directory for:
   - Test structure and organization
   - Test coverage areas
   - How to run tests
5. Check @conftest.py for shared test fixtures
</research>

<requirements>
The README.md must include these sections:

1. **Project Title and Description**
   - Clear one-line description
   - Badges if appropriate (Python version, license)

2. **Features**
   - Key capabilities as bullet points

3. **Installation**
   - Prerequisites (Python version, uv)
   - Step-by-step installation commands

4. **Usage**
   - Basic usage with examples
   - All CLI arguments with descriptions
   - Example commands showing common use cases

5. **How It Works**
   - Brief explanation of the processing pipeline
   - What gets converted and how
   - Output format details

6. **Architecture**
   - Core functions and their responsibilities
   - File structure overview

7. **Testing**
   - How to run tests
   - Test organization explanation
   - Coverage information

8. **Exit Codes**
   - Document all exit codes and their meanings

9. **License** (if applicable)
</requirements>

<constraints>
- Keep documentation accurate to the actual code behavior
- Use clear, concise language
- Include actual working examples (test them mentally against the code)
- Don't add features or capabilities that don't exist
- Preserve any existing content that's still accurate
</constraints>

<output>
Update the file: `./README.md`

The README should be comprehensive but not overwhelming - aim for documentation that a developer can scan quickly to understand the basics, then dive deeper into specific sections as needed.
</output>

<verification>
Before completing, verify:
- All CLI arguments from argparse are documented
- All exit codes are documented
- Test commands actually work with the project structure
- Installation steps use uv as specified in CLAUDE.md
</verification>
