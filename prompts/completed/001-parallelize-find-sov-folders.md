<objective>
Update the `find_sov_folders()` function in `excel_to_parquet.py` to traverse the directory tree until it accumulates at least 5 subdirectories, then parallelize the remaining traversal across those branches using ThreadPoolExecutor.

This improves performance on large directory trees by distributing the filesystem traversal work across multiple threads once sufficient parallelism is available.
</objective>

<context>
Read @excel_to_parquet.py to understand the current implementation.

The current `find_sov_folders()` function (lines 271-353):
- Takes a list of root directories
- Recursively traverses each using `rglob("**")`
- Finds directories containing "/SOV/" in their path
- Returns a sorted, deduplicated list

The issue: On large directory trees, single-threaded traversal is slow because filesystem operations are I/O-bound.
</context>

<requirements>
1. Traverse the directory tree breadth-first from each root until you have accumulated at least 10 subdirectories
2. Once 10+ subdirectories are collected, spawn parallel workers to traverse each branch concurrently
3. Use `concurrent.futures.ThreadPoolExecutor` for parallelism (filesystem I/O benefits from threads, not processes)
4. Maintain all existing behavior:
   - Case-sensitive "/SOV/" matching using `as_posix()`
   - Error handling for PermissionError and other exceptions
   - Set-based deduplication
   - Sorted output
   - Logging
5. Add a configurable `min_parallel_branches` parameter with default of 10
6. Add a configurable `max_workers` parameter with default of `None` (ThreadPoolExecutor default)
</requirements>

<example_folder_structure>
Consider this directory tree:

```
/data/projects/
├── 2023/
│   ├── Q1/
│   │   └── SOV/
│   │       └── reports/
│   └── Q2/
│       └── SOV/
│           └── reports/
├── 2024/
│   ├── Q1/
│   │   └── SOV/
│   │       └── reports/
│   ├── Q2/
│   │   └── SOV/
│   │       └── reports/
│   └── Q3/
│       └── SOV/
│           └── reports/
└── archive/
    └── old/
        └── SOV/
            └── legacy/
```

**How it should work:**

1. Start at `/data/projects/`
2. Find immediate subdirectories: `2023/`, `2024/`, `archive/` (3 dirs)
3. Not enough (< 10), so go one level deeper:
   - From `2023/`: `Q1/`, `Q2/`
   - From `2024/`: `Q1/`, `Q2/`, `Q3/`
   - From `archive/`: `old/`
   - Total: 6 directories
4. Still not enough (< 10), so go one level deeper:
   - From `2023/Q1/`: `SOV/`
   - From `2023/Q2/`: `SOV/`
   - From `2024/Q1/`: `SOV/`
   - From `2024/Q2/`: `SOV/`
   - From `2024/Q3/`: `SOV/`
   - From `archive/old/`: `SOV/`
   - Total: 12 directories (6 SOV dirs + 6 parent dirs from previous level)
5. Now >= 10 dirs, so parallelize: spawn a worker for each of the 12 branches
6. Each worker recursively searches its subtree for "/SOV/" paths
7. Collect and deduplicate results from all workers

**Expected output:**
```
[
    Path('/data/projects/2023/Q1/SOV'),
    Path('/data/projects/2023/Q1/SOV/reports'),
    Path('/data/projects/2023/Q2/SOV'),
    Path('/data/projects/2023/Q2/SOV/reports'),
    Path('/data/projects/2024/Q1/SOV'),
    Path('/data/projects/2024/Q1/SOV/reports'),
    Path('/data/projects/2024/Q2/SOV'),
    Path('/data/projects/2024/Q2/SOV/reports'),
    Path('/data/projects/2024/Q3/SOV'),
    Path('/data/projects/2024/Q3/SOV/reports'),
    Path('/data/projects/archive/old/SOV'),
    Path('/data/projects/archive/old/SOV/legacy'),
]
```
</example_folder_structure>

<implementation>
1. Extract the core traversal logic into a helper function `_traverse_for_sov(root: Path) -> Set[Path]`
2. Implement breadth-first collection of subdirectories until threshold is reached
3. Use `ThreadPoolExecutor.map()` to parallelize the remaining traversal
4. Update the function signature to include new parameters with defaults
5. Keep the existing single-threaded behavior when fewer than `min_parallel_branches` directories are found (fall back to sequential traversal)

Avoid:
- Using multiprocessing (overkill for I/O-bound filesystem operations)
- Breaking the existing return type (List[Path])
- Modifying the function's public API in a breaking way (new params should have defaults)
</implementation>

<output>
Modify `./excel_to_parquet.py` with the updated `find_sov_folders()` function.
</output>

<verification>
After implementing, verify:
1. The function still returns the same results for small directory trees (< 10 subdirs)
2. The function parallelizes correctly for larger trees
3. All existing tests in `tests/test_find_sov_folders.py` still pass
4. Run: `uv run pytest tests/test_find_sov_folders.py -v`
</verification>

<success_criteria>
- Function traverses breadth-first until 10+ subdirectories are found
- Parallel workers are spawned for each branch once threshold is reached
- Existing behavior and return type are preserved
- All existing tests pass
- Code includes appropriate logging for debugging parallel execution
</success_criteria>
