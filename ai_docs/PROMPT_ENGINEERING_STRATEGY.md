# Excel-to-Parquet Conversion: Prompt Engineering Strategy

## Overview

This document explains the prompt engineering approach used to decompose a complex Python development task into 4 manageable, optimized prompts. Each prompt is designed to maximize LLM accuracy and code quality through specific design principles.

## Why This Decomposition?

### The Challenge
The original requirement is complex:
- File system operations with specific search criteria
- Data processing with pandas and openpyxl
- CLI interface with argument parsing
- Comprehensive error handling
- Extensive test coverage

Asking an LLM to handle all of this in one prompt typically leads to:
- Missed requirements
- Inconsistent error handling
- Incomplete testing
- Quality shortcuts under cognitive load

### The Solution: 4-Step Progressive Complexity

```
Step 1: File Discovery (Focused, Well-Defined)
        ↓
Step 2: Data Processing (Complex, Isolated)
        ↓
Step 3: Integration (Orchestration Layer)
        ↓
Step 4: Quality Assurance (Comprehensive Validation)
```

## Prompt Design Principles Applied

### 1. Context Layering
Each prompt includes:
- **Full System Context**: Where this step fits in the overall pipeline
- **Specific Step Context**: What's being implemented now
- **Previous Step Context**: Dependencies and assumptions
- **Next Step Preview**: How this will be used

**Why**: LLMs perform better when they understand both the specific task AND the broader system architecture.

### 2. Explicit Constraint Enumeration

Each prompt includes:
- ✅ **Must Do** (Critical requirements)
- ❌ **Must Not Do** (Common failure modes)
- ⚠️ **Edge Cases** (Scenarios to handle)

**Example from Step 1:**
```
✅ Use ONLY pathlib (no os module)
❌ DON'T use os.walk() - requirement specifies pathlib
⚠️ Handle permission errors gracefully
```

**Why**: Makes success criteria unambiguous and prevents common mistakes.

### 3. Failure Mode Anticipation

Each prompt includes a "Common Pitfalls" section addressing:
- What developers typically get wrong
- What LLMs typically get wrong
- Platform-specific issues (Windows vs. Unix)
- Performance concerns

**Why**: Pre-emptively addressing failure modes improves first-attempt accuracy dramatically.

### 4. Progressive Validation

Each prompt includes:
- **Validation Checklist**: Must verify before moving on
- **Success Criteria**: Measurable outcomes
- **Testing Hooks**: How this will be tested later

**Why**: Encourages self-validation and creates natural checkpoints.

### 5. Example-Driven Specification

Each prompt includes:
- **Should Match** examples (positive cases)
- **Should NOT Match** examples (negative cases)
- **Code Templates** (structure guidance)
- **Usage Examples** (expected interface)

**Why**: Examples disambiguate requirements far better than prose alone.

## Step-by-Step Breakdown

### Step 1: File Discovery (`find_sov_folders`)

**Design Rationale:**
- Starts with simplest component
- Clear input/output contract
- No external dependencies (just pathlib)
- Easy to test independently

**Key Prompt Elements:**
- Explicit pathlib requirement (avoid os module confusion)
- Cross-platform path handling (.as_posix())
- Fault tolerance specification (don't crash on errors)
- Deterministic output (sorted, deduplicated)

**Why This Works:**
LLMs handle focused tasks better than complex tasks. Starting with file discovery builds a solid foundation.

### Step 2: Excel Processing (`process_excel_files`)

**Design Rationale:**
- Most complex logic isolated here
- Depends on Step 1 output (clear interface)
- All pandas/openpyxl complexity contained
- Error handling requirements explicit

**Key Prompt Elements:**
- DataFrame transformation requirements (metadata columns)
- Error recovery strategy (per-file try-catch)
- Empty data handling (skip gracefully)
- Memory efficiency considerations

**Why This Works:**
By this point, the LLM has file discovery working. Can focus entirely on data processing without worrying about file finding logic.

### Step 3: CLI Integration (`main`)

**Design Rationale:**
- Orchestrates Steps 1 & 2
- Adds user interface layer
- Handles top-level concerns (logging, validation, exit codes)
- No complex algorithms - just wiring

**Key Prompt Elements:**
- argparse patterns (required vs. optional arguments)
- Logging configuration before processing
- Exit code conventions (0=success, 1=user error, etc.)
- Graceful degradation (KeyboardInterrupt handling)

**Why This Works:**
With core logic complete, integration is straightforward. LLM can focus on user experience and error communication.

### Step 4: Comprehensive Testing

**Design Rationale:**
- Validates all previous work
- 100% coverage goal drives thoroughness
- Edge cases from previous prompts become test cases
- Integration tests verify end-to-end behavior

**Key Prompt Elements:**
- Specific test case enumeration (what to test)
- Mocking strategies (how to test)
- Fixture patterns (test data creation)
- Coverage measurement (validation)

**Why This Works:**
Testing comes last but uses accumulated knowledge from all previous steps. Each edge case mentioned earlier gets a test.

## Prompt Engineering Techniques Used

### 1. Structured Requirements

```markdown
### Detailed Implementation Requirements

1. **Input Handling**:
   - Specific requirement
   - Another requirement
   
2. **Search Logic**:
   - How to implement
   - What to avoid
```

**Impact**: Organized information is processed more accurately by LLMs.

### 2. Success Criteria Lists

```markdown
Your implementation must:
- ✅ Criterion 1
- ✅ Criterion 2
- ✅ Criterion 3
```

**Impact**: Creates clear checkpoints for validation.

### 3. Negative Examples

```markdown
❌ **DON'T** use os.walk()
❌ **DON'T** assume headers
❌ **DON'T** crash on errors
```

**Impact**: Explicitly prevents common mistakes.

### 4. Template Code

```python
def function_name(args) -> return_type:
    """Docstring template..."""
    # TODO: Step 1
    # TODO: Step 2
    pass
```

**Impact**: Provides structure while leaving implementation open.

### 5. Validation Checklists

```markdown
- [ ] Requirement met
- [ ] Edge case handled
- [ ] Test written
```

**Impact**: Encourages completeness checking.

## Integration Between Steps

### Data Flow
```
Step 1 Output: List[Path]
       ↓
Step 2 Input: List[Path], output_dir
       ↓
Step 3: Orchestrates 1 & 2
       ↓
Step 4: Tests 1, 2, 3 + integration
```

### Context Preservation

Each prompt references:
- What came before (completed work)
- What comes after (future integration)
- How pieces fit together (system architecture)

**Example from Step 2:**
```markdown
## Full System Context
1. **[Completed]** Find folders → produces List[Path]
2. **[THIS STEP]** Process Excel files
3. **[Future]** Wire up CLI
```

## Optimization for LLM Strengths

### Pattern Recognition
- Repeated structure across prompts
- Consistent terminology
- Similar validation checklists

### Disambiguation
- Examples for ambiguous requirements
- Multiple phrasings of critical points
- Visual separators (═══, ───)

### Cognitive Load Management
- One major task per step
- Progressive complexity
- Clear boundaries

## Quality Assurance Through Prompt Design

### Built-in Validation

Each prompt forces validation through:
1. Explicit success criteria
2. Validation checklists
3. Test previews
4. Common pitfall warnings

### Testability First

Design decisions driven by testability:
- Pure functions (no hidden state)
- Dependency injection (mockable)
- Error handling (testable paths)

### Documentation Requirements

Every prompt requires:
- Docstrings explaining "why"
- Type hints for clarity
- Inline comments for complex logic
- Usage examples

## Measuring Success

### Accuracy Metrics
- First-attempt success rate
- Edge cases handled without revision
- Test coverage achieved
- Code quality (PEP 8 compliance)

### Efficiency Metrics
- Time to complete each step
- Number of revisions needed
- Integration issues encountered

### Quality Metrics
- Error handling completeness
- Performance characteristics
- Maintainability score

## Lessons for Future Prompt Engineering

### What Worked Well

1. **Progressive Complexity**: Starting simple builds confidence
2. **Explicit Negative Examples**: "Don't do X" prevents mistakes
3. **Template Code**: Structure without over-specification
4. **Context Layering**: System view + specific task
5. **Validation Checklists**: Force thoroughness

### What to Improve

1. **More Visual Diagrams**: File structure, data flow
2. **Performance Budgets**: Explicit time/memory constraints
3. **Security Considerations**: Input validation, path traversal
4. **Accessibility**: Logging for different user needs

### Reusable Patterns

```markdown
## [Step N]: [Component Name]

### Context
- System overview
- This step's role
- Dependencies

### Requirements
- Detailed specifications
- Success criteria
- Edge cases

### Common Pitfalls
- ❌ Don't do X
- ❌ Don't do Y

### Validation
- [ ] Checklist item
- [ ] Checklist item

### Output Format
- What to deliver
- How to structure it
```

## Conclusion

This 4-step decomposition demonstrates key prompt engineering principles:

1. **Decompose by Complexity**: Isolate hard problems
2. **Provide Context**: System-level + task-level
3. **Anticipate Failure**: Address common mistakes explicitly
4. **Enable Validation**: Checklists and success criteria
5. **Use Examples**: Show, don't just tell

The result: Higher accuracy, better code quality, and more maintainable outputs from LLMs.

## Using These Prompts

### Sequential Execution
```bash
# Step 1: Implement file discovery
[Use Step 1 prompt] → Validate → Commit

# Step 2: Implement Excel processing  
[Use Step 2 prompt] → Validate → Commit

# Step 3: Implement CLI and main
[Use Step 3 prompt] → Validate → Commit

# Step 4: Implement tests
[Use Step 4 prompt] → Run coverage → Commit
```

### Iterative Refinement
- Each step builds on validated previous work
- Can revisit earlier steps if integration reveals issues
- Tests in Step 4 validate entire pipeline

### Customization
- Adapt validation criteria to your needs
- Add domain-specific requirements
- Modify code patterns to match your style
