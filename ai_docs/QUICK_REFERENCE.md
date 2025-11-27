# Quick Reference: Excel-to-Parquet Prompt Set

## What This Is

A set of 4 optimized prompts that guide an LLM to build a production-ready Excel-to-Parquet conversion tool with comprehensive testing. Each prompt is designed for maximum accuracy and minimal revision.

## Files in This Set

| File | Purpose | Est. Time |
|------|---------|-----------|
| `step1_file_discovery_prompt.md` | Implement `find_sov_folders()` | 10-15 min |
| `step2_excel_processing_prompt.md` | Implement `process_excel_files()` | 20-30 min |
| `step3_cli_main_prompt.md` | Implement CLI, main(), integration | 15-20 min |
| `step4_comprehensive_testing_prompt.md` | Implement full test suite | 30-45 min |
| `PROMPT_ENGINEERING_STRATEGY.md` | Understanding the approach | Reference |
| `THIS_FILE.md` | Quick start guide | You are here |

**Total Implementation Time**: ~75-110 minutes with an LLM

## Quick Start

### Prerequisites
```bash
# Python 3.8+
python --version

# Install dependencies
pip install pandas openpyxl pytest pytest-cov
```

### Execution Sequence

#### Step 1: File Discovery (15 min)
```bash
# 1. Copy step1_file_discovery_prompt.md content
# 2. Paste into your LLM interface
# 3. Save output to: excel_to_parquet.py
# 4. Quick validation:
python -c "from excel_to_parquet import find_sov_folders; print('✓ Step 1 complete')"
```

**Expected Output**: `find_sov_folders()` function with full docstring, type hints, error handling

**Validation**: Function should find folders containing "/SOV/" in path

#### Step 2: Excel Processing (30 min)
```bash
# 1. Copy step2_excel_processing_prompt.md content
# 2. Paste into your LLM interface
# 3. Add output to excel_to_parquet.py (after step 1)
# 4. Quick validation:
python -c "from excel_to_parquet import process_excel_files; print('✓ Step 2 complete')"
```

**Expected Output**: `process_excel_files()` function that reads Excel, adds metadata, saves Parquet

**Validation**: Function should accept `List[Path]` and create output directory

#### Step 3: CLI Integration (20 min)
```bash
# 1. Copy step3_cli_main_prompt.md content
# 2. Paste into your LLM interface  
# 3. Add output to excel_to_parquet.py (complete file now)
# 4. Quick validation:
python excel_to_parquet.py --help
```

**Expected Output**: Complete `main()`, argparse setup, logging configuration

**Validation**: Should show help text with all arguments

#### Step 4: Comprehensive Testing (45 min)
```bash
# 1. Create tests/ directory
mkdir -p tests

# 2. Copy step4_comprehensive_testing_prompt.md content
# 3. Paste into your LLM interface
# 4. Save outputs to tests/ directory
# 5. Run tests:
pytest --cov=excel_to_parquet --cov-report=term-missing
```

**Expected Output**: Complete test suite with fixtures, mocks, integration tests

**Validation**: Should achieve >90% code coverage, all tests passing

## Usage After Implementation

### Basic Usage
```bash
python excel_to_parquet.py /data/projects --output /output/parquet
```

### With Options
```bash
python excel_to_parquet.py \
    /data/project1 /data/project2 \
    --output /output/parquet \
    --log-level DEBUG \
    --log-file conversion.log
```

### Running Tests
```bash
# All tests
pytest

# With coverage
pytest --cov=excel_to_parquet --cov-report=html

# Specific test
pytest tests/test_find_sov_folders.py -v
```

## Troubleshooting

### Common Issues

**Issue**: LLM skips error handling
- **Fix**: Point to "Error Handling" section in prompt
- **Reminder**: "Every file operation needs try-except"

**Issue**: LLM forgets to add metadata columns
- **Fix**: Emphasize "CRITICAL" requirement in Step 2
- **Check**: Verify file_path and row_number columns

**Issue**: Tests don't achieve coverage target
- **Fix**: Reference "Coverage Requirements" in Step 4
- **Action**: Add tests for uncovered lines

**Issue**: argparse not configured correctly
- **Fix**: Show example from Step 3 prompt
- **Check**: Verify `--help` output matches spec

### Validation Checklist

After each step:

**Step 1:**
- [ ] Function uses only pathlib (no os module)
- [ ] Uses .as_posix() for path checking
- [ ] Returns sorted list of Path objects
- [ ] Handles permission errors gracefully

**Step 2:**
- [ ] Reads Excel with header=None
- [ ] Adds file_path and row_number columns
- [ ] Uses UUID4 for filenames
- [ ] Creates output directory if needed
- [ ] Handles empty sheets

**Step 3:**
- [ ] Argparse accepts multiple root_dirs
- [ ] --output is required argument
- [ ] Logging configured before processing
- [ ] Returns integer exit codes
- [ ] Validates inputs before processing

**Step 4:**
- [ ] Tests for both main functions exist
- [ ] Edge cases covered (empty, corrupted, missing)
- [ ] Integration test exists
- [ ] Coverage >90%
- [ ] All tests pass

## Customization Guide

### Adapting for Your Needs

**Different File Types:**
- Step 2: Change `rglob('*.xlsx')` to your extension
- Step 2: Update `pd.read_excel()` to appropriate pandas reader

**Different Folder Pattern:**
- Step 1: Change `"/SOV/"` check to your pattern
- Keep .as_posix() for cross-platform compatibility

**Different Output Format:**
- Step 2: Replace `df.to_parquet()` with your format
- Update test validation accordingly

**Additional Metadata:**
- Step 2: Add more columns in processing function
- Update tests to verify new columns

### Modifying Prompts

```markdown
# Add to Requirements section:
5. **Your New Requirement**:
   - Specific detail
   - Why it matters
   - How to implement

# Add to Common Pitfalls:
❌ **DON'T** [common mistake]

# Add to Validation Checklist:
- [ ] Your new requirement verified
```

## Performance Expectations

### Processing Speed
- Small files (<1MB): ~100ms per file
- Medium files (1-10MB): ~1s per file
- Large files (>10MB): ~10s per file

### Memory Usage
- Scales with Excel file size
- ~2x file size in memory during processing
- Released after each file

### Test Execution
- Full suite: <5 seconds
- Coverage generation: +2 seconds
- Individual test: <100ms

## Success Metrics

### Code Quality Indicators
- ✓ All functions have type hints
- ✓ All functions have docstrings
- ✓ PEP 8 compliant (run `flake8`)
- ✓ No hardcoded paths
- ✓ Proper error handling

### Functionality Indicators
- ✓ Finds all SOV folders correctly
- ✓ Processes all Excel files
- ✓ Adds metadata columns
- ✓ Creates valid Parquet files
- ✓ Handles errors gracefully

### Testing Indicators
- ✓ Coverage >90%
- ✓ All tests pass
- ✓ Edge cases covered
- ✓ Integration test passes
- ✓ Fast execution (<5s)

## Next Steps After Implementation

### 1. Documentation
```bash
# Create README.md with:
- Installation instructions
- Usage examples
- Configuration options
- Troubleshooting guide
```

### 2. Deployment
```bash
# Package for distribution
pip install setuptools wheel
python setup.py sdist bdist_wheel

# Or create Docker container
docker build -t excel-to-parquet .
```

### 3. Monitoring
```bash
# Add logging to file for production
python excel_to_parquet.py \
    /data \
    --output /output \
    --log-file /var/log/conversion.log
```

### 4. CI/CD Integration
```yaml
# .github/workflows/test.yml
name: Tests
on: [push, pull_request]
jobs:
  test:
    runs-on: ubuntu-latest
    steps:
      - uses: actions/checkout@v2
      - name: Run tests
        run: |
          pip install -r requirements.txt
          pytest --cov=excel_to_parquet
```

## Support

### Getting Help
1. Check validation checklist in prompt
2. Review "Common Pitfalls" sections
3. Run specific test to identify issue
4. Check PROMPT_ENGINEERING_STRATEGY.md for design rationale

### Reporting Issues
When something doesn't work:
1. Which step? (1, 2, 3, or 4)
2. What was expected?
3. What actually happened?
4. Error messages or logs?
5. Test results (if applicable)?

## Advanced Usage

### Parallel Processing
```python
# Modify Step 2 to use multiprocessing
from multiprocessing import Pool

def process_file_wrapper(args):
    excel_file, output_dir = args
    # Process single file
    
with Pool(processes=4) as pool:
    pool.map(process_file_wrapper, file_args)
```

### Progress Tracking
```python
# Add to Step 2
from tqdm import tqdm

for excel_file in tqdm(excel_files, desc="Processing"):
    # Process file
```

### Custom Filters
```python
# Add to Step 1
def find_sov_folders(root_dirs, pattern="/SOV/", exclude_patterns=None):
    # Add pattern parameter for flexibility
```

## FAQ

**Q: Can I use this with .xls files?**  
A: Yes, Step 2 already handles both .xlsx and .xls

**Q: What if my Excel files have headers?**  
A: Modify Step 2 to use `header=0` instead of `header=None`

**Q: How do I skip empty sheets?**  
A: Step 2 already includes this - empty sheets are logged and skipped

**Q: Can I change the UUID naming?**  
A: Yes, modify Step 2 filename generation, update tests accordingly

**Q: What Python version is required?**  
A: Python 3.8+ (uses type hints with List[], Path)

**Q: How do I add more metadata columns?**  
A: In Step 2, add `df.insert()` calls for additional columns

**Q: Can I process files in subdirectories of SOV folders?**  
A: Yes, Step 2 uses `rglob()` which is recursive

## Version History

- **v1.0**: Initial prompt set
  - 4 steps: file discovery, processing, CLI, testing
  - Target: 90%+ coverage
  - Python 3.8+ support

## License

These prompts are provided as-is for educational and commercial use.

---

**Remember**: These prompts are optimized for LLM accuracy. Follow them sequentially for best results!
