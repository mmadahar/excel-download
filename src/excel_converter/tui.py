#!/usr/bin/env python3
"""
Excel-to-Parquet TUI (Text User Interface)

Interactive dashboard for the Excel-to-Parquet conversion tool.
Allows users to scan directories, view discovered files, convert to Parquet,
and inspect results.

Usage:
    uv run python tui.py
"""

from datetime import datetime
from pathlib import Path

import polars as pl
from textual import work
from textual.app import App, ComposeResult
from textual.binding import Binding
from textual.containers import Container, Horizontal, Vertical, VerticalScroll
from textual.screen import Screen
from textual.widgets import (
    Button,
    Checkbox,
    DataTable,
    Footer,
    Header,
    Input,
    Label,
    ListItem,
    ListView,
    ProgressBar,
    Static,
)

# Import functions from cli module
from .cli import (
    FILES_CSV,
    find_sov_folders,
    get_processed_file_paths,
    load_or_scan_files,
    process_excel_files,
    scan_for_excel_files,
)


class MainMenu(Screen):
    """Main menu screen with navigation options."""

    BINDINGS = [
        Binding("q", "quit", "Quit"),
        Binding("1", "scan", "Scan"),
        Binding("2", "browse", "Browse"),
        Binding("3", "convert", "Convert"),
        Binding("4", "results", "Results"),
    ]

    def compose(self) -> ComposeResult:
        yield Header()
        yield Container(
            Static("Excel-to-Parquet Converter", id="title"),
            Static("", id="spacer1"),
            Button("[1] Scan Directories", id="btn-scan", variant="primary"),
            Button("[2] View Discovered Files", id="btn-browse", variant="default"),
            Button("[3] Convert to Parquet", id="btn-convert", variant="success"),
            Button("[4] View Results", id="btn-results", variant="default"),
            Static("", id="spacer2"),
            Button("[Q] Exit", id="btn-exit", variant="error"),
            id="menu-container",
        )
        yield Footer()

    def on_button_pressed(self, event: Button.Pressed) -> None:
        button_id = event.button.id
        if button_id == "btn-scan":
            self.app.push_screen(ScanScreen())
        elif button_id == "btn-browse":
            self.app.push_screen(FileBrowserScreen())
        elif button_id == "btn-convert":
            self.app.push_screen(ConversionScreen())
        elif button_id == "btn-results":
            self.app.push_screen(ResultsScreen())
        elif button_id == "btn-exit":
            self.app.exit()

    def action_quit(self) -> None:
        self.app.exit()

    def action_scan(self) -> None:
        self.app.push_screen(ScanScreen())

    def action_browse(self) -> None:
        self.app.push_screen(FileBrowserScreen())

    def action_convert(self) -> None:
        self.app.push_screen(ConversionScreen())

    def action_results(self) -> None:
        self.app.push_screen(ResultsScreen())


class ScanScreen(Screen):
    """Screen for scanning directories for Excel files."""

    BINDINGS = [
        Binding("escape", "go_back", "Back"),
        Binding("enter", "start_scan", "Start Scan"),
    ]

    def compose(self) -> ComposeResult:
        yield Header()
        yield Container(
            Static("Scan for Excel Files", id="screen-title"),
            Static(""),
            Label("Add Directory:"),
            Horizontal(
                Input(
                    placeholder="Enter directory path (e.g., ./data/test_excel)",
                    id="dir-input",
                ),
                Button("Add", id="btn-add-dir", variant="default"),
                Button("Load from Excel", id="btn-load-excel", variant="default"),
                id="input-row",
            ),
            Static(""),
            Label("Directories to scan:"),
            VerticalScroll(
                id="dir-list-container",
            ),
            Horizontal(
                Button("Select All", id="btn-select-all", variant="default"),
                Button("Deselect All", id="btn-deselect-all", variant="default"),
                Button("Remove Selected", id="btn-remove", variant="default"),
                Button("Clear All", id="btn-clear", variant="error"),
                id="dir-controls",
            ),
            Static(""),
            Horizontal(
                Checkbox("Force Rescan", id="rescan-checkbox"),
                id="checkbox-row",
            ),
            Static(""),
            Horizontal(
                Button("Start Scan", id="btn-start", variant="primary"),
                Button("Back", id="btn-back", variant="default"),
                id="button-row",
            ),
            Static(""),
            ProgressBar(id="scan-progress", show_eta=False),
            Static("", id="status-label"),
            Static("", id="results-summary"),
            id="scan-container",
        )
        yield Footer()

    def on_mount(self) -> None:
        self.query_one("#scan-progress", ProgressBar).update(total=100, progress=0)
        # Initialize app state for scan directories if not exists
        if not hasattr(self.app, "scan_directories"):
            self.app.scan_directories = []
        # Load existing directories from app state
        self._load_directories_from_state()

    def _load_directories_from_state(self) -> None:
        """Load directories from app state into UI."""
        if hasattr(self.app, "scan_directories"):
            for directory in self.app.scan_directories:
                self._add_directory_to_list(directory)

    def _add_directory_to_list(self, directory: str, checked: bool = True) -> None:
        """Add a directory to the list with a checkbox."""
        dir_container = self.query_one("#dir-list-container", VerticalScroll)
        # Generate unique ID for this checkbox
        index = len([w for w in dir_container.children if isinstance(w, Checkbox)])
        checkbox = Checkbox(directory, id=f"dir-check-{index}", value=checked)
        dir_container.mount(checkbox)

    def add_directory(self) -> None:
        """Add directory from input field to the list."""
        dir_input = self.query_one("#dir-input", Input)
        directory = dir_input.value.strip()

        if not directory:
            self.query_one("#status-label", Static).update(
                "Error: Please enter a directory path"
            )
            return

        path = Path(directory)
        if not path.exists():
            self.query_one("#status-label", Static).update(
                f"Error: Directory does not exist: {directory}"
            )
            return

        if not path.is_dir():
            self.query_one("#status-label", Static).update(
                f"Error: Path is not a directory: {directory}"
            )
            return

        # Check if directory is already in list
        existing_dirs = self.get_all_directories()
        if str(path.resolve()) in existing_dirs:
            self.query_one("#status-label", Static).update(
                f"Directory already added: {directory}"
            )
            return

        # Add to list (auto-selected)
        self._add_directory_to_list(str(path.resolve()), checked=True)

        # Clear input
        dir_input.value = ""
        self.query_one("#status-label", Static).update(f"Added directory: {directory}")

        # Update app state
        if not hasattr(self.app, "scan_directories"):
            self.app.scan_directories = []
        self.app.scan_directories = self.get_all_directories()

    def load_from_excel(self) -> None:
        """Load directory list from Excel file."""
        # Create input prompt for Excel file path
        dir_input = self.query_one("#dir-input", Input)
        excel_path_str = dir_input.value.strip()

        if not excel_path_str:
            self.query_one("#status-label", Static).update(
                "Error: Please enter path to Excel file"
            )
            return

        excel_path = Path(excel_path_str)
        if not excel_path.exists():
            self.query_one("#status-label", Static).update(
                f"Error: Excel file does not exist: {excel_path_str}"
            )
            return

        try:
            # Read Excel file - first column only
            df = pl.read_excel(excel_path, has_header=False)

            if df.is_empty():
                self.query_one("#status-label", Static).update(
                    "Error: Excel file is empty"
                )
                return

            # Get first column
            directories = df.get_column("column_1").to_list()

            # Skip header if first row looks like a header
            if directories and isinstance(directories[0], str):
                first_value = directories[0].lower()
                if any(
                    keyword in first_value
                    for keyword in ["path", "folder", "directory"]
                ):
                    directories = directories[1:]

            # Filter out empty/null values
            directories = [d for d in directories if d and str(d).strip()]

            # Validate and add directories
            valid_count = 0
            invalid_count = 0
            existing_dirs = self.get_all_directories()

            for directory in directories:
                dir_str = str(directory).strip()
                dir_path = Path(dir_str)

                # Check if directory exists
                if not dir_path.exists() or not dir_path.is_dir():
                    invalid_count += 1
                    continue

                # Check if already in list
                resolved_path = str(dir_path.resolve())
                if resolved_path in existing_dirs:
                    continue

                # Add to list (auto-selected)
                self._add_directory_to_list(resolved_path, checked=True)
                existing_dirs.add(resolved_path)
                valid_count += 1

            # Clear input
            dir_input.value = ""

            # Show summary
            summary = f"Loaded {valid_count} valid directory(ies)"
            if invalid_count > 0:
                summary += f", skipped {invalid_count} invalid path(s)"
            self.query_one("#status-label", Static).update(summary)

            # Update app state
            if not hasattr(self.app, "scan_directories"):
                self.app.scan_directories = []
            self.app.scan_directories = self.get_all_directories()

        except Exception as e:
            self.query_one("#status-label", Static).update(
                f"Error loading Excel file: {e}"
            )

    def get_all_directories(self) -> set:
        """Get set of all directories in the list."""
        dir_container = self.query_one("#dir-list-container", VerticalScroll)
        directories = set()
        for checkbox in dir_container.query(Checkbox):
            if checkbox.id and checkbox.id.startswith("dir-check-"):
                directories.add(checkbox.label.plain)
        return directories

    def get_selected_directories(self) -> list:
        """Get list of selected (checked) directories."""
        dir_container = self.query_one("#dir-list-container", VerticalScroll)
        selected = []
        for checkbox in dir_container.query(Checkbox):
            if checkbox.id and checkbox.id.startswith("dir-check-") and checkbox.value:
                selected.append(checkbox.label.plain)
        return selected

    def select_all(self) -> None:
        """Check all directory checkboxes."""
        dir_container = self.query_one("#dir-list-container", VerticalScroll)
        for checkbox in dir_container.query(Checkbox):
            if checkbox.id and checkbox.id.startswith("dir-check-"):
                checkbox.value = True
        self.query_one("#status-label", Static).update("All directories selected")

    def deselect_all(self) -> None:
        """Uncheck all directory checkboxes."""
        dir_container = self.query_one("#dir-list-container", VerticalScroll)
        for checkbox in dir_container.query(Checkbox):
            if checkbox.id and checkbox.id.startswith("dir-check-"):
                checkbox.value = False
        self.query_one("#status-label", Static).update("All directories deselected")

    def remove_selected(self) -> None:
        """Remove checked directories from the list."""
        dir_container = self.query_one("#dir-list-container", VerticalScroll)
        checkboxes_to_remove = []

        for checkbox in dir_container.query(Checkbox):
            if checkbox.id and checkbox.id.startswith("dir-check-") and checkbox.value:
                checkboxes_to_remove.append(checkbox)

        removed_count = len(checkboxes_to_remove)
        for checkbox in checkboxes_to_remove:
            checkbox.remove()

        self.query_one("#status-label", Static).update(
            f"Removed {removed_count} directory(ies)"
        )

        # Update app state
        if not hasattr(self.app, "scan_directories"):
            self.app.scan_directories = []
        self.app.scan_directories = list(self.get_all_directories())

    def clear_directories(self) -> None:
        """Clear all directories from the list."""
        dir_container = self.query_one("#dir-list-container", VerticalScroll)
        checkboxes = list(dir_container.query(Checkbox))

        for checkbox in checkboxes:
            if checkbox.id and checkbox.id.startswith("dir-check-"):
                checkbox.remove()

        self.query_one("#status-label", Static).update("All directories cleared")

        # Update app state
        if not hasattr(self.app, "scan_directories"):
            self.app.scan_directories = []
        self.app.scan_directories = []

    def on_button_pressed(self, event: Button.Pressed) -> None:
        if event.button.id == "btn-add-dir":
            self.add_directory()
        elif event.button.id == "btn-load-excel":
            self.load_from_excel()
        elif event.button.id == "btn-select-all":
            self.select_all()
        elif event.button.id == "btn-deselect-all":
            self.deselect_all()
        elif event.button.id == "btn-remove":
            self.remove_selected()
        elif event.button.id == "btn-clear":
            self.clear_directories()
        elif event.button.id == "btn-start":
            self.action_start_scan()
        elif event.button.id == "btn-back":
            self.app.pop_screen()

    def action_go_back(self) -> None:
        self.app.pop_screen()

    def action_start_scan(self) -> None:
        rescan_checkbox = self.query_one("#rescan-checkbox", Checkbox)

        # Get selected directories
        selected_dirs = self.get_selected_directories()

        if not selected_dirs:
            self.query_one("#status-label", Static).update(
                "Error: No directories selected. Please add and select directories to scan."
            )
            return

        rescan = rescan_checkbox.value
        self.run_scan(selected_dirs, rescan)

    @work(thread=True)
    def run_scan(self, directories: list, rescan: bool) -> None:
        """Run the scan in a background thread with detailed progress tracking."""
        total_dirs = len(directories)
        all_files = []

        try:
            # Process each directory with progress tracking
            for idx, directory in enumerate(directories, 1):
                self.app.call_from_thread(
                    self._update_status,
                    f"Scanning directory {idx} of {total_dirs}: {Path(directory).name}",
                )
                self.app.call_from_thread(
                    self._update_progress_detailed, total_dirs, idx - 1
                )

                # Scan this directory
                df = load_or_scan_files([directory], rescan)
                all_files.append(df)

                # Show running total
                total_files_so_far = sum(len(df) for df in all_files)
                self.app.call_from_thread(
                    self._update_status,
                    f"Scanning directory {idx} of {total_dirs}: {Path(directory).name} - {total_files_so_far} files found so far",
                )

            # Complete progress
            self.app.call_from_thread(
                self._update_progress_detailed, total_dirs, total_dirs
            )

            # Combine all dataframes
            if all_files:
                combined_df = pl.concat(all_files)
            else:
                combined_df = pl.DataFrame(
                    schema={
                        "file_path": pl.Utf8,
                        "extension": pl.Utf8,
                        "discovered_at": pl.Utf8,
                    }
                )

            # Generate summary
            if len(combined_df) == 0:
                summary = "No Excel files found."
            else:
                ext_counts = combined_df.group_by("extension").count()
                summary_lines = [f"Found {len(combined_df)} Excel file(s):"]
                for row in ext_counts.iter_rows(named=True):
                    summary_lines.append(f"  {row['extension']}: {row['count']}")
                summary = "\n".join(summary_lines)

            self.app.call_from_thread(self._update_status, "Scan complete!")
            self.app.call_from_thread(self._update_results, summary)

            # Store in app state
            self.app.discovered_files = combined_df

        except Exception as e:
            self.app.call_from_thread(self._update_status, f"Error: {e}")
            self.app.call_from_thread(self._update_progress_detailed, 100, 0)

    def _update_status(self, message: str) -> None:
        self.query_one("#status-label", Static).update(message)

    def _update_progress(self, value: int) -> None:
        self.query_one("#scan-progress", ProgressBar).update(progress=value)

    def _update_progress_detailed(self, total: int, progress: int) -> None:
        """Update progress bar with actual counts."""
        self.query_one("#scan-progress", ProgressBar).update(
            total=total, progress=progress
        )

    def _update_results(self, summary: str) -> None:
        self.query_one("#results-summary", Static).update(summary)


class FileBrowserScreen(Screen):
    """Screen for browsing discovered Excel files."""

    BINDINGS = [
        Binding("escape", "go_back", "Back"),
        Binding("r", "refresh", "Refresh"),
    ]

    def compose(self) -> ComposeResult:
        yield Header()
        yield Container(
            Static("Discovered Excel Files", id="screen-title"),
            Static("", id="file-count"),
            DataTable(id="files-table"),
            Static(""),
            Horizontal(
                Button("Refresh", id="btn-refresh", variant="default"),
                Button("Back", id="btn-back", variant="default"),
                id="button-row",
            ),
            id="browser-container",
        )
        yield Footer()

    def on_mount(self) -> None:
        self.load_files()

    def load_files(self) -> None:
        """Load files from CSV or app state."""
        table = self.query_one("#files-table", DataTable)
        table.clear(columns=True)

        # Add columns
        table.add_columns("Filename", "Extension", "Path", "Discovered")

        # Try to load from app state or CSV
        df = getattr(self.app, "discovered_files", None)

        if df is None and FILES_CSV.exists():
            try:
                df = pl.read_csv(FILES_CSV)
                self.app.discovered_files = df
            except Exception:
                pass

        if df is None or len(df) == 0:
            self.query_one("#file-count", Static).update(
                "No files discovered. Run a scan first."
            )
            return

        self.query_one("#file-count", Static).update(f"Total: {len(df)} file(s)")

        # Add rows
        for row in df.iter_rows(named=True):
            file_path = Path(row["file_path"])
            table.add_row(
                file_path.name,
                row["extension"],
                str(file_path.parent),
                row["discovered_at"][:19] if row.get("discovered_at") else "",
            )

    def on_button_pressed(self, event: Button.Pressed) -> None:
        if event.button.id == "btn-refresh":
            self.load_files()
        elif event.button.id == "btn-back":
            self.app.pop_screen()

    def action_go_back(self) -> None:
        self.app.pop_screen()

    def action_refresh(self) -> None:
        self.load_files()


class ConversionScreen(Screen):
    """Screen for converting Excel files to Parquet."""

    BINDINGS = [
        Binding("escape", "go_back", "Back"),
        Binding("enter", "start_convert", "Convert"),
    ]

    def compose(self) -> ComposeResult:
        yield Header()
        yield Container(
            Static("Convert to Parquet", id="screen-title"),
            Static(""),
            Label("Output Directory:"),
            Input(
                placeholder="Enter output directory (e.g., ./data/output)",
                id="output-input",
                value="./data/output",
            ),
            Static(""),
            Horizontal(
                Button("Start Conversion", id="btn-convert", variant="success"),
                Button("Back", id="btn-back", variant="default"),
                id="button-row",
            ),
            Static(""),
            ProgressBar(id="convert-progress", show_eta=False),
            Static("", id="status-label"),
            VerticalScroll(
                Static("", id="log-output"),
                id="log-scroll",
            ),
            id="convert-container",
        )
        yield Footer()

    def on_mount(self) -> None:
        self.query_one("#convert-progress", ProgressBar).update(total=100, progress=0)
        self._log_lines = []  # Reset log lines on mount

    def on_button_pressed(self, event: Button.Pressed) -> None:
        if event.button.id == "btn-convert":
            self.action_start_convert()
        elif event.button.id == "btn-back":
            self.app.pop_screen()

    def action_go_back(self) -> None:
        self.app.pop_screen()

    def action_start_convert(self) -> None:
        output_input = self.query_one("#output-input", Input)
        output_dir = output_input.value.strip()

        if not output_dir:
            self.query_one("#status-label", Static).update(
                "Error: Please enter an output directory"
            )
            return

        # Check if files.csv exists
        if not FILES_CSV.exists():
            self.query_one("#status-label", Static).update(
                "Error: No files discovered. Run a scan first."
            )
            return

        self.run_conversion(output_dir)

    @work(thread=True)
    def run_conversion(self, output_dir: str) -> None:
        """Run conversion in a background thread with detailed progress tracking."""
        self.app.call_from_thread(self._update_status, "Starting conversion...")
        self.app.call_from_thread(self._append_log, f"Output directory: {output_dir}")

        try:
            output_path = Path(output_dir)
            output_path.mkdir(parents=True, exist_ok=True)

            # Load files
            if not FILES_CSV.exists():
                self.app.call_from_thread(
                    self._update_status, "Error: No files discovered. Run a scan first."
                )
                return

            df = pl.read_csv(FILES_CSV)
            total_files = len(df)

            if total_files == 0:
                self.app.call_from_thread(self._update_status, "No files to convert.")
                return

            self.app.call_from_thread(
                self._append_log, f"Total files discovered: {total_files}"
            )

            # Get already processed files
            processed_paths = get_processed_file_paths(output_path)
            self.app.call_from_thread(
                self._append_log, f"Already processed: {len(processed_paths)} file(s)"
            )

            # Filter files to process
            files_to_process = []
            for row in df.iter_rows(named=True):
                file_path_str = row["file_path"]
                file_path = Path(file_path_str)

                # Skip if already processed
                if file_path_str in processed_paths:
                    continue

                # Verify file still exists
                if not file_path.exists():
                    continue

                files_to_process.append(file_path)

            if not files_to_process:
                self.app.call_from_thread(
                    self._update_status, "All files already processed or missing."
                )
                self.app.call_from_thread(
                    self._append_log, "Nothing to do - all files already converted."
                )
                return

            total_to_process = len(files_to_process)
            self.app.call_from_thread(
                self._append_log, f"Processing {total_to_process} file(s)..."
            )

            # Process each file with detailed progress tracking
            total_sheets = 0
            total_rows = 0

            for idx, file_path in enumerate(files_to_process, 1):
                # Update status with current file
                self.app.call_from_thread(
                    self._update_status,
                    f"Converting file {idx} of {total_to_process}: {file_path.name}",
                )
                self.app.call_from_thread(
                    self._update_progress_detailed, total_to_process, idx - 1
                )

                try:
                    # Process this file
                    from .cli import get_engine_for_extension

                    engine = get_engine_for_extension(file_path)
                    sheets_dict = pl.read_excel(
                        source=file_path,
                        sheet_id=0,
                        engine=engine,
                        has_header=False,
                        raise_if_empty=False,
                    )

                    file_sheets = len(sheets_dict)
                    file_rows = 0

                    # Process each sheet
                    for sheet_idx, (sheet_name, sheet_df) in enumerate(
                        sheets_dict.items(), 1
                    ):
                        if sheet_df.is_empty():
                            continue

                        self.app.call_from_thread(
                            self._update_status,
                            f"Converting file {idx} of {total_to_process}: {file_path.name} - Sheet {sheet_idx} of {file_sheets}",
                        )

                        # Transform sheet to long format
                        import uuid

                        df_with_row = sheet_df.with_row_index(name="row")
                        value_columns = [
                            col for col in df_with_row.columns if col != "row"
                        ]

                        unpivoted = df_with_row.unpivot(
                            on=value_columns,
                            index="row",
                            variable_name="column",
                            value_name="value",
                        )

                        result = unpivoted.select(
                            [
                                pl.lit(str(file_path)).alias("file_path"),
                                pl.lit(file_path.name).alias("file_name"),
                                pl.lit(sheet_name).alias("worksheet"),
                                pl.col("row"),
                                pl.col("column")
                                .str.replace("column_", "")
                                .cast(pl.Int64)
                                .alias("column"),
                                pl.col("value").cast(pl.Utf8).alias("value"),
                            ]
                        )

                        # Save to Parquet
                        output_filename = f"{uuid.uuid4()}.parquet"
                        output_file_path = output_path / output_filename
                        result.write_parquet(output_file_path)

                        file_rows += len(result)
                        total_sheets += 1
                        total_rows += len(result)

                    # Log completion of this file
                    self.app.call_from_thread(
                        self._append_log,
                        f"Completed {file_path.name}: {file_sheets} sheet(s), {file_rows} row(s)",
                    )

                except Exception as e:
                    self.app.call_from_thread(
                        self._append_log, f"Error processing {file_path.name}: {e}"
                    )

            # Complete progress
            self.app.call_from_thread(
                self._update_progress_detailed, total_to_process, total_to_process
            )

            self.app.call_from_thread(self._update_status, "Conversion complete!")
            self.app.call_from_thread(
                self._append_log,
                f"Total: {total_sheets} sheet(s) converted, {total_rows} row(s) written",
            )

            # Count output files
            parquet_files = list(output_path.glob("*.parquet"))
            self.app.call_from_thread(
                self._append_log, f"Total Parquet files: {len(parquet_files)}"
            )

            # Store output dir in app state
            self.app.output_dir = output_path

        except Exception as e:
            self.app.call_from_thread(self._update_status, f"Error: {e}")
            self.app.call_from_thread(self._append_log, f"Error: {e}")

    def _update_status(self, message: str) -> None:
        self.query_one("#status-label", Static).update(message)

    def _update_progress(self, value: int) -> None:
        self.query_one("#convert-progress", ProgressBar).update(progress=value)

    def _update_progress_detailed(self, total: int, progress: int) -> None:
        """Update progress bar with actual counts."""
        self.query_one("#convert-progress", ProgressBar).update(
            total=total, progress=progress
        )

    def _append_log(self, message: str) -> None:
        log_widget = self.query_one("#log-output", Static)
        timestamp = datetime.now().strftime("%H:%M:%S")
        # Get current content from the log lines stored on self
        if not hasattr(self, "_log_lines"):
            self._log_lines = []
        self._log_lines.append(f"[{timestamp}] {message}")
        log_widget.update("\n".join(self._log_lines))


class ResultsScreen(Screen):
    """Screen for viewing conversion results and Parquet file metadata."""

    BINDINGS = [
        Binding("escape", "go_back", "Back"),
        Binding("r", "refresh", "Refresh"),
    ]

    def compose(self) -> ComposeResult:
        yield Header()
        yield Container(
            Static("Conversion Results", id="screen-title"),
            Label("Output Directory:"),
            Input(
                placeholder="Enter output directory to inspect",
                id="output-input",
                value="./data/output",
            ),
            Horizontal(
                Button("Load Results", id="btn-load", variant="primary"),
                Button("Back", id="btn-back", variant="default"),
                id="button-row",
            ),
            Static("", id="summary-label"),
            DataTable(id="results-table"),
            Static(""),
            Static("Preview (first 10 rows of selected file):", id="preview-title"),
            DataTable(id="preview-table"),
            id="results-container",
        )
        yield Footer()

    def on_mount(self) -> None:
        results_table = self.query_one("#results-table", DataTable)
        results_table.add_columns("Filename", "Size (KB)", "Rows", "Source File")

        preview_table = self.query_one("#preview-table", DataTable)
        preview_table.add_columns("file_path", "worksheet", "row", "column", "value")

        # Try to load from app state
        output_dir = getattr(self.app, "output_dir", None)
        if output_dir:
            self.query_one("#output-input", Input).value = str(output_dir)
            self.load_results(str(output_dir))

    def on_button_pressed(self, event: Button.Pressed) -> None:
        if event.button.id == "btn-load":
            output_dir = self.query_one("#output-input", Input).value.strip()
            if output_dir:
                self.load_results(output_dir)
        elif event.button.id == "btn-back":
            self.app.pop_screen()

    def on_data_table_row_selected(self, event: DataTable.RowSelected) -> None:
        """When a row is selected, show preview of that Parquet file."""
        if event.data_table.id != "results-table":
            return

        # Get the filename from the selected row
        row_key = event.row_key
        table = self.query_one("#results-table", DataTable)
        row_data = table.get_row(row_key)

        if row_data:
            filename = row_data[0]
            output_dir = self.query_one("#output-input", Input).value.strip()
            parquet_path = Path(output_dir) / filename
            self.show_preview(parquet_path)

    def load_results(self, output_dir: str) -> None:
        """Load Parquet files from output directory."""
        results_table = self.query_one("#results-table", DataTable)
        results_table.clear()

        output_path = Path(output_dir)
        if not output_path.exists():
            self.query_one("#summary-label", Static).update(
                f"Directory not found: {output_dir}"
            )
            return

        parquet_files = list(output_path.glob("*.parquet"))

        if not parquet_files:
            self.query_one("#summary-label", Static).update("No Parquet files found.")
            return

        self.query_one("#summary-label", Static).update(
            f"Found {len(parquet_files)} Parquet file(s)"
        )

        for pq_file in sorted(parquet_files)[:50]:  # Limit to 50 files
            try:
                # Get file size
                size_kb = pq_file.stat().st_size / 1024

                # Read metadata
                df = pl.read_parquet(pq_file)
                row_count = len(df)

                # Get source file name
                source_file = ""
                if "file_name" in df.columns and len(df) > 0:
                    source_file = df["file_name"][0]

                results_table.add_row(
                    pq_file.name,
                    f"{size_kb:.1f}",
                    str(row_count),
                    source_file,
                )
            except Exception as e:
                results_table.add_row(pq_file.name, "?", "Error", str(e)[:30])

    def show_preview(self, parquet_path: Path) -> None:
        """Show preview of Parquet file contents."""
        preview_table = self.query_one("#preview-table", DataTable)
        preview_table.clear()

        try:
            df = pl.read_parquet(parquet_path)

            # Show first 10 rows
            for row in df.head(10).iter_rows(named=True):
                preview_table.add_row(
                    str(row.get("file_path", ""))[:40],
                    str(row.get("worksheet", "")),
                    str(row.get("row", "")),
                    str(row.get("column", "")),
                    str(row.get("value", ""))[:30],
                )
        except Exception as e:
            self.query_one("#preview-title", Static).update(f"Preview error: {e}")

    def action_go_back(self) -> None:
        self.app.pop_screen()

    def action_refresh(self) -> None:
        output_dir = self.query_one("#output-input", Input).value.strip()
        if output_dir:
            self.load_results(output_dir)


class ExcelConverterApp(App):
    """Main TUI application for Excel-to-Parquet conversion."""

    CSS = """
    #title {
        text-align: center;
        text-style: bold;
        color: $accent;
        padding: 1 0;
        width: 100%;
    }

    #screen-title {
        text-align: center;
        text-style: bold;
        color: $accent;
        padding: 1 0;
        margin-bottom: 1;
    }

    #menu-container {
        align: center middle;
        width: 100%;
        height: 100%;
    }

    #menu-container Button {
        width: 40;
        margin: 1 0;
    }

    #scan-container, #browser-container, #convert-container, #results-container {
        padding: 1 2;
    }

    #button-row {
        margin-top: 1;
        height: auto;
    }

    #button-row Button {
        margin-right: 2;
    }

    #input-row {
        height: auto;
        margin-bottom: 1;
    }

    #input-row Input {
        width: 1fr;
        margin-right: 1;
        margin-bottom: 0;
    }

    #input-row Button {
        margin-right: 1;
    }

    #dir-list-container {
        height: 10;
        border: solid $primary;
        margin: 1 0;
        padding: 1;
    }

    #dir-controls {
        height: auto;
        margin-bottom: 1;
    }

    #dir-controls Button {
        margin-right: 1;
    }

    #checkbox-row {
        height: auto;
    }

    Input {
        width: 100%;
        margin-bottom: 1;
    }

    DataTable {
        height: auto;
        max-height: 15;
        margin: 1 0;
    }

    #log-scroll {
        height: 10;
        border: solid $primary;
        margin-top: 1;
    }

    #results-summary {
        margin-top: 1;
    }

    ProgressBar {
        width: 100%;
        padding: 1 0;
    }

    #preview-table {
        max-height: 12;
    }

    #spacer1, #spacer2 {
        height: 1;
    }
    """

    TITLE = "Excel-to-Parquet Converter"
    BINDINGS = [
        Binding("q", "quit", "Quit", show=True),
    ]

    def __init__(self):
        super().__init__()
        self.discovered_files = None
        self.output_dir = None

    def on_mount(self) -> None:
        self.push_screen(MainMenu())


def main():
    """Entry point for the TUI application."""
    app = ExcelConverterApp()
    app.run()


if __name__ == "__main__":
    main()
