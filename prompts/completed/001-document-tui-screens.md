<objective>
Document the TUI (Text User Interface) implementation for the Excel-to-Parquet converter.

Create comprehensive documentation of all TUI screens, their workflow, and user interactions. This will be used as source material for the README.md file.
</objective>

<context>
This project has a Textual-based TUI in `tui.py` with styling in `tui.tcss`. The TUI provides an interactive alternative to the CLI for users who prefer a graphical interface.

Read these files to understand the implementation:
- @tui.py - Main TUI application with all screens
- @tui.tcss - CSS styling for the TUI
</context>

<requirements>
Document each screen with:
1. **Screen name and purpose** - What the screen does
2. **Components** - Input fields, buttons, tables, progress bars
3. **User workflow** - Step-by-step what the user does
4. **Key bindings** - Keyboard shortcuts available
5. **Data flow** - What data enters/exits the screen
6. **Error handling** - How errors are displayed to users

Screens to document:
- MainMenu (navigation hub)
- ScanScreen (file discovery)
- FileBrowserScreen (view discovered files)
- ConversionScreen (convert to Parquet)
- ResultsScreen (view and preview results)

Include ASCII mockups showing the layout of each screen.
</requirements>

<output>
Save documentation to: `./prompts/completed/001-tui-documentation.md`

Structure the output as:
```markdown
# TUI Documentation

## Overview
[Brief intro to the TUI]

## Screen Flow Diagram
[ASCII diagram showing navigation between screens]

## Screens

### MainMenu
[Details...]

### ScanScreen
[Details with ASCII mockup...]

[etc. for each screen]

## State Management
[How data flows between screens via app state]

## Keyboard Shortcuts Reference
[Complete table of all bindings]
```
</output>

<verification>
Before completing, verify:
- All 5 screens are documented
- Each screen has an ASCII mockup
- All keyboard bindings are listed
- Data flow between screens is explained
- The documentation could help a new user understand the TUI completely
</verification>
