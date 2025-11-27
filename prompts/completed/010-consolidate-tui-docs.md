<objective>
Consolidate the TUI documentation files into the main README.md and remove the separate TUI doc files.

This is step 4 of the restructuring. Currently there are three separate TUI documentation files at root that should be merged into README.md for a cleaner project structure.
</objective>

<context>
Files to consolidate:
- `TUI_GUIDE.md` - Detailed usage guide for the TUI
- `TUI_IMPLEMENTATION.md` - Implementation details and architecture
- `TUI_QUICKSTART.md` - Quick start guide

Target: `README.md`

Read CLAUDE.md for project context. The README should provide a comprehensive overview that includes TUI documentation without being overwhelming.
</context>

<requirements>
1. Read all three TUI documentation files to understand their content

2. Read the current README.md to understand its structure

3. Create a consolidated TUI section in README.md that includes:
   - Quick start (essential commands to launch and use)
   - Key features and screens
   - Keyboard shortcuts (the most useful ones)
   - Implementation notes (brief, for developers)

4. The TUI section should be:
   - Concise but complete
   - Easy to scan with headers and bullet points
   - Include a screenshot reference if one exists

5. After consolidation, delete the separate TUI files:
   - `TUI_GUIDE.md`
   - `TUI_IMPLEMENTATION.md`
   - `TUI_QUICKSTART.md`
</requirements>

<constraints>
- Don't bloat the README - aim for a focused TUI section
- Prioritize user-facing information over implementation details
- Keep the README well-organized with clear section hierarchy
- Implementation details can be brief or moved to code comments
</constraints>

<implementation>
Suggested README structure for TUI section:
```markdown
## Interactive TUI

### Quick Start
[Launch command, basic navigation]

### Features
[Bullet list of main capabilities]

### Keyboard Shortcuts
[Table or compact list of key bindings]

### Screens
[Brief description of each screen]
```
</implementation>

<output>
1. Edit README.md to add consolidated TUI section
2. Delete TUI_GUIDE.md, TUI_IMPLEMENTATION.md, TUI_QUICKSTART.md using rm commands
</output>

<verification>
1. Verify README.md has proper TUI documentation
2. Verify the three TUI files are deleted
3. Check README.md renders correctly (no broken formatting)
</verification>

<success_criteria>
- README.md contains comprehensive but concise TUI documentation
- TUI_GUIDE.md, TUI_IMPLEMENTATION.md, TUI_QUICKSTART.md are deleted
- README.md is well-organized and not bloated
- All essential TUI information is preserved
</success_criteria>
