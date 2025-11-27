# Step 1: Implement File Discovery Function (`find_sov_folders`)

## Context
You are implementing part of an Excel-to-Parquet conversion pipeline. This is **Step 1 of 4** - implementing the file discovery mechanism that will locate all folders containing "/SOV/" in their path structure.

## Full System Context
The complete system will:
1. **[THIS STEP]** Find folders with "/SOV/" in path
2. **[Future Step]** Process Excel files in those folders
3. **[Future Step]** Wire up CLI and main function
4. **[Future Step]** Add comprehensive test coverage

## Specific Requirements

### Function Signature
```python
def find_sov_folders(root_dirs: List[str]) -> List[Path]:
```

### Detailed Implementation Requirements

1. **Input Handling**:
   - Accept a list of root directory paths as strings
   - Handle both absolute and relative paths
   - Convert all paths to `pathlib.Path` objects for consistent handling

2. **Search Logic**:
   - Recursively traverse ALL subdirectories from each root
   - Use `pathlib` methods exclusively (no `os.walk()`)
   - Use `.as_posix()` method when checking for "/SOV/" to ensure cross-platform compatibility
   - Match folders where "/SOV/" appears ANYWHERE in the full path (e.g., "data/project1/SOV/files" should match)
   - Case-sensitive matching: only "/SOV/" not "/sov/" or "/Sov/"

3. **Return Value**:
   - Return a list of `Path` objects (not strings)
   - Return only directories that exist and are accessible
   - Remove duplicates if any root_dirs overlap
   - Sort results alphabetically by full path for deterministic output

4. **Error Handling**:
   - Skip directories that cannot be accessed (permission errors)
   - Log warnings for inaccessible directories using `logging.warning()`
   - Never raise exceptions - be fault-tolerant
   - Continue processing remaining directories if one fails

5. **Code Quality**:
   - Follow PEP 8 strictly (max 79 chars per line)
   - Include complete type hints
   - Add comprehensive docstring following Google or NumPy style
   - Use meaningful variable names (e.g., `candidate_folder` not `f`)

### Critical Success Criteria

Your implementation must:
- ✅ Use ONLY `pathlib` (no `os` module for path operations)
- ✅ Check for "/SOV/" using `.as_posix()` method
- ✅ Return `Path` objects, not strings
- ✅ Handle permission errors gracefully without crashing
- ✅ Work correctly on Windows, Linux, and macOS
- ✅ Handle empty input list (return empty list)
- ✅ Handle non-existent root directories (log warning, continue)

### Common Pitfalls to Avoid

❌ **DON'T** use `os.walk()` - requirement specifies `pathlib`
❌ **DON'T** use string concatenation for paths - use `Path` operators
❌ **DON'T** assume forward slashes work on Windows - use `.as_posix()`
❌ **DON'T** crash on permission errors - catch and log
❌ **DON'T** forget to check if path is a directory before adding to results
❌ **DON'T** return duplicate paths

### Example Test Cases to Consider

```python
# Should match:
"/data/project1/SOV/files"           # SOV in middle
"/SOV/project"                       # SOV at start
"/data/reports/SOV"                  # SOV at end
"/data/SOV/sub1/SOV/sub2"           # Multiple SOV folders

# Should NOT match:
"/data/project1/sov/files"           # Wrong case
"/data/SOVFILES"                     # Not a separate folder
"/data/project1/files"               # No SOV
```

### Logging Setup

Initialize logging at module level:
```python
import logging

logger = logging.getLogger(__name__)
```

Use in function:
- `logger.info()` - when starting search on each root directory
- `logger.warning()` - for inaccessible directories
- `logger.debug()` - for verbose information about folders found

### Docstring Template

```python
def find_sov_folders(root_dirs: List[str]) -> List[Path]:
    """
    Recursively search for all subdirectories containing "/SOV/" in their path.
    
    This function walks through directory trees starting from the provided root
    directories and identifies folders where "/SOV/" appears anywhere in the
    full path. The search is case-sensitive and uses pathlib for cross-platform
    compatibility.
    
    Why this approach:
    - Uses pathlib exclusively for modern, cross-platform path handling
    - as_posix() ensures "/SOV/" matching works on Windows (with backslashes)
    - Fault-tolerant: continues processing even if some directories are inaccessible
    - Returns Path objects for consistency with modern Python practices
    
    Args:
        root_dirs: List of root directory paths (strings) to search from.
                  Can be absolute or relative paths.
    
    Returns:
        Sorted list of Path objects representing directories containing "/SOV/"
        in their path. Duplicates are removed. Empty list if no matches found.
    
    Example:
        >>> find_sov_folders(["/data/projects"])
        [Path('/data/projects/2024/SOV/client1'), 
         Path('/data/projects/2024/SOV/client2')]
    """
```

### Implementation Skeleton

```python
import logging
from pathlib import Path
from typing import List

logger = logging.getLogger(__name__)

def find_sov_folders(root_dirs: List[str]) -> List[Path]:
    """[Complete docstring here]"""
    sov_folders = []
    
    # TODO: Iterate through each root directory
    # TODO: Use Path.rglob() or recursive iteration
    # TODO: Check if "/SOV/" in path.as_posix()
    # TODO: Handle PermissionError specifically
    # TODO: Remove duplicates and sort
    
    return sov_folders
```

## Validation Checklist

Before considering this step complete, verify:

- [ ] Function has complete type hints
- [ ] Docstring explains "why" not just "what"
- [ ] Uses pathlib exclusively
- [ ] Uses .as_posix() for SOV checking
- [ ] Returns Path objects
- [ ] Handles permission errors without crashing
- [ ] Logs appropriately (info, warning, debug)
- [ ] Removes duplicates from results
- [ ] Sorts results alphabetically
- [ ] Works with empty input list
- [ ] PEP 8 compliant (run `flake8` to verify)

## Output Format

Provide the complete function implementation including:
1. All imports needed
2. Logger initialization
3. Complete function with docstring
4. Inline comments for complex logic
5. Brief explanation of design decisions

## Next Step Preview

Once this function is complete and validated, Step 2 will implement `process_excel_files()` which will:
- Use the folders found by this function
- Read Excel files with pandas/openpyxl
- Convert sheets to Parquet format
- Add metadata columns (file path, row number)
