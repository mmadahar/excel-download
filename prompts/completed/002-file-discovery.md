<objective>
Implement `find_sov_folders()` - Step 1 of 4 in the Excel-to-Parquet pipeline.

This function recursively searches directories to find all folders containing "/SOV/" in their path. Output will be consumed by Step 2 (process_excel_files).
</objective>

<context>
@prompts/001-shared-context.md - Read this first for project architecture and standards.

This is the FIRST function in the pipeline. It must:
- Accept root directories as strings
- Return Path objects for downstream processing
- Be completely fault-tolerant (never crash)
</context>

<function_signature>
```python
def find_sov_folders(root_dirs: List[str]) -> List[Path]:
```
</function_signature>

<requirements>
1. **Input Handling**
   - Accept list of root directory paths as strings
   - Handle both absolute and relative paths
   - Convert all inputs to pathlib.Path objects

2. **Search Logic**
   - Use pathlib methods ONLY (no os.walk, no os module)
   - Check for "/SOV/" using `path.as_posix()` for cross-platform compatibility
   - Case-sensitive: only "/SOV/" matches, not "/sov/" or "/Sov/"
   - Match folders where "/SOV/" appears ANYWHERE in the full path

3. **Return Value**
   - Return List[Path] objects (not strings)
   - Remove duplicates (if root_dirs overlap)
   - Sort results alphabetically by full path
   - Return empty list for empty input

4. **Error Handling**
   - Skip non-existent directories (log warning)
   - Skip inaccessible directories (log warning on PermissionError)
   - Never raise exceptions - always return a valid list
   - Continue processing remaining directories after any error
</requirements>

<implementation_pattern>
```python
import logging
from pathlib import Path
from typing import List

logger = logging.getLogger(__name__)

def find_sov_folders(root_dirs: List[str]) -> List[Path]:
    """
    Recursively search for directories containing '/SOV/' in their path.

    Uses pathlib exclusively for cross-platform compatibility. The as_posix()
    method ensures '/SOV/' matching works correctly on Windows paths that
    use backslashes natively.

    Args:
        root_dirs: List of root directory paths to search from.

    Returns:
        Sorted list of Path objects for directories containing '/SOV/'.
        Duplicates removed. Empty list if no matches or on empty input.

    Example:
        >>> find_sov_folders(['/data/projects'])
        [Path('/data/projects/2024/SOV/client1')]
    """
    sov_folders = set()  # Use set for automatic deduplication

    for root_dir in root_dirs:
        root_path = Path(root_dir)

        # Handle non-existent directory
        if not root_path.exists():
            logger.warning(f"Root directory does not exist: {root_dir}")
            continue

        logger.info(f"Searching for SOV folders in: {root_dir}")

        try:
            # Walk all directories recursively
            for candidate in root_path.rglob('*'):
                if candidate.is_dir():
                    # Use as_posix() for consistent "/" separator
                    if '/SOV/' in candidate.as_posix():
                        sov_folders.add(candidate)
                        logger.debug(f"Found SOV folder: {candidate}")

        except PermissionError as e:
            logger.warning(f"Permission denied accessing: {root_dir} - {e}")
            continue
        except Exception as e:
            logger.warning(f"Error scanning {root_dir}: {e}")
            continue

    # Convert to sorted list
    result = sorted(list(sov_folders))
    logger.info(f"Found {len(result)} SOV folder(s)")
    return result
```
</implementation_pattern>

<test_cases>
```python
# Should MATCH:
"/data/project1/SOV/files"       # SOV in middle
"/SOV/project"                   # SOV at start
"/data/reports/SOV"              # SOV at end
"/data/SOV/sub1/SOV/sub2"        # Multiple SOV (both match)

# Should NOT match:
"/data/project1/sov/files"       # Wrong case (lowercase)
"/data/SOVFILES"                 # Not a separate folder segment
"/data/project1/files"           # No SOV at all
```
</test_cases>

<common_pitfalls>
- Using os.walk() instead of pathlib - requirement specifies pathlib only
- Forgetting .as_posix() - causes failures on Windows with backslash paths
- Returning strings instead of Path objects - breaks Step 2 integration
- Crashing on permission errors - must catch and continue
- Not deduplicating when roots overlap
</common_pitfalls>

<output>
Create file: `./excel_to_parquet.py`

Include:
1. Module docstring
2. All necessary imports
3. Logger initialization at module level
4. Complete find_sov_folders() function with docstring
5. Inline comments for non-obvious logic

Do NOT include main() or other functions yet - those come in later steps.
</output>

<verification>
Before completing, verify:
- [ ] Uses pathlib exclusively (no os module)
- [ ] Uses .as_posix() for SOV pattern matching
- [ ] Returns List[Path], not List[str]
- [ ] Handles permission errors without crashing
- [ ] Handles non-existent directories without crashing
- [ ] Removes duplicates
- [ ] Sorts results
- [ ] Has complete type hints
- [ ] Has docstring explaining WHY the approach works
- [ ] PEP 8 compliant
</verification>

<next_step>
After validation, Step 2 will use this function's output to process Excel files:
```python
sov_folders = find_sov_folders(['/data/projects'])
process_excel_files(sov_folders, Path('/output'))
```
</next_step>
