"""Terminal UI for Jortt timesheet reporting using Textual."""

import asyncio
import os
from datetime import date, timedelta
from pathlib import Path
from typing import Literal

import duckdb
import polars as pl
from textual.app import App, ComposeResult
from textual.containers import Horizontal, Vertical
from textual.widgets import Button, DataTable, Footer, Header, Static, Switch


class TimesheetApp(App):
    """Textual app for Jortt timesheet reporting."""

    CSS = """
    $accent: #3399CC;
    $warning: #3399CC;

    Screen {
        background: $surface;
    }

    * {
        scrollbar-color: #3399CC;
        scrollbar-color-hover: #5ab3e6;
        scrollbar-color-active: #2080b3;
    }

    #reports-container {
        height: 1fr;
        margin: 1;
    }

    .report-panel {
        height: 1fr;
        border: solid #3399CC;
        padding: 1;
        margin-bottom: 1;
    }

    .report-header {
        height: auto;
        margin-bottom: 1;
    }

    .report-controls {
        height: auto;
        margin-bottom: 1;
    }

    Button {
        margin: 0 1;
    }

    Button.-primary {
        background: #3399CC;
        color: white;
    }

    Button.-primary:hover {
        background: #5ab3e6;
    }

    Button.-primary:focus {
        background: #2080b3;
    }

    DataTable {
        height: 1fr;
        width: 100%;
    }

    .status {
        margin: 0 1;
    }

    Footer {
        background: $panel;
    }

    Footer > .footer--key {
        color: #3399CC;
    }

    Footer > .footer--highlight-key {
        color: #3399CC;
    }

    FooterKey {
        color: #3399CC;
        background: $panel;
    }
    """

    BINDINGS = [
        ("q", "quit", "quit"),
        ("r", "run_pipeline", "refresh data"),
        ("m", "toggle_metric", "toggle metric"),
        ("left", "prev_week", "previous week"),
        ("right", "next_week", "next week"),
        ("shift+left", "prev_month", "previous month"),
        ("shift+right", "next_month", "next month"),
    ]

    def __init__(self):
        super().__init__()
        self.project_root = Path(__file__).parent.parent
        self.database_path = os.getenv(
            "DATABASE_PATH", str(self.project_root / "jortt.duckdb")
        )
        # Track current period offsets (0 = current, -1 = previous, etc.)
        self.week_offset = 0
        self.month_offset = 0
        # Track metric toggles
        self.week_metric: Literal["hours", "value"] = "hours"
        self.month_metric: Literal["hours", "value"] = "hours"

    def compose(self) -> ComposeResult:
        """Create child widgets for the app."""
        yield Header()

        # Reports section
        with Vertical(id="reports-container"):
            # Weekly report panel
            with Vertical(classes="report-panel", id="weekly-panel"):
                yield Static("Weekly Report (Hours)", classes="report-header", id="weekly-header")
                with Horizontal(classes="report-controls"):
                    yield Button("←", id="week-prev")
                    yield Button("→", id="week-next")
                    yield Static("Current Week", id="week-title")
                    yield Static("Show: ", markup=False)
                    yield Switch(value=True, id="week-metric-toggle")
                    yield Static("Hours", id="week-metric-label")
                yield DataTable(id="weekly-table")

            # Monthly report panel
            with Vertical(classes="report-panel", id="monthly-panel"):
                yield Static("Monthly Report (Hours)", classes="report-header", id="monthly-header")
                with Horizontal(classes="report-controls"):
                    yield Button("←", id="month-prev")
                    yield Button("→", id="month-next")
                    yield Static("Current Month", id="month-title")
                    yield Static("Show: ", markup=False)
                    yield Switch(value=True, id="month-metric-toggle")
                    yield Static("Hours", id="month-metric-label")
                yield DataTable(id="monthly-table")

        yield Footer()

    def on_mount(self) -> None:
        """Set up the app after mounting."""
        # Run pipeline at startup to ensure fresh data
        self.notify("⏳ Starting pipeline...", severity="information", timeout=3)
        self.run_worker(self._startup_pipeline_worker, exclusive=True)

    async def _startup_pipeline_worker(self) -> None:
        """Worker method to run the pipeline at startup and then load reports."""
        try:
            process = await asyncio.create_subprocess_exec(
                "uv",
                "run",
                "python",
                "-m",
                "jortt_report",
                cwd=self.project_root,
                stdout=asyncio.subprocess.PIPE,
                stderr=asyncio.subprocess.PIPE,
            )

            try:
                stdout, stderr = await asyncio.wait_for(
                    process.communicate(), timeout=300  # 5 minute timeout
                )
            except asyncio.TimeoutError:
                process.kill()
                await process.wait()
                self.notify(
                    "✗ Pipeline timed out after 5 minutes", severity="error", timeout=5
                )
                return

            if process.returncode == 0:
                self.notify("✓ Pipeline completed successfully", timeout=3)
                # Load reports with fresh data
                self.refresh_weekly_report()
                self.refresh_monthly_report()
                self.notify("Reports loaded", timeout=2)
            else:
                error_msg = stderr.decode()[:200] if stderr else "Unknown error"
                self.notify(
                    f"✗ Pipeline failed: {error_msg}", severity="error", timeout=10
                )
                # Still try to load any existing data
                self.refresh_weekly_report()
                self.refresh_monthly_report()
        except Exception as e:
            self.notify(
                f"✗ Error running pipeline: {str(e)[:100]}", severity="error", timeout=5
            )
            # Still try to load any existing data
            self.refresh_weekly_report()
            self.refresh_monthly_report()

    def action_run_pipeline(self) -> None:
        """Action to run the pipeline via key binding."""
        self.run_pipeline()

    def action_toggle_metric(self) -> None:
        """Toggle between hours and euros for both reports."""
        # Toggle both metrics
        self.week_metric = "value" if self.week_metric == "hours" else "hours"
        self.month_metric = "value" if self.month_metric == "hours" else "hours"

        # Update the switches to match
        week_switch = self.query_one("#week-metric-toggle", Switch)
        month_switch = self.query_one("#month-metric-toggle", Switch)
        week_switch.value = self.week_metric == "hours"
        month_switch.value = self.month_metric == "hours"

        # Update the labels
        week_label = self.query_one("#week-metric-label", Static)
        month_label = self.query_one("#month-metric-label", Static)
        new_label = "Hours" if self.week_metric == "hours" else "Value (€)"
        week_label.update(new_label)
        month_label.update(new_label)

        # Update the headers
        weekly_header = self.query_one("#weekly-header", Static)
        monthly_header = self.query_one("#monthly-header", Static)
        header_suffix = "Hours" if self.week_metric == "hours" else "Euros"
        weekly_header.update(f"Weekly Report ({header_suffix})")
        monthly_header.update(f"Monthly Report ({header_suffix})")

        # Refresh both reports
        self.refresh_weekly_report()
        self.refresh_monthly_report()

    def action_prev_week(self) -> None:
        """Navigate to the previous week."""
        self.week_offset -= 1
        self.refresh_weekly_report()

    def action_next_week(self) -> None:
        """Navigate to the next week."""
        self.week_offset += 1
        self.refresh_weekly_report()

    def action_prev_month(self) -> None:
        """Navigate to the previous month."""
        self.month_offset -= 1
        self.refresh_monthly_report()

    def action_next_month(self) -> None:
        """Navigate to the next month."""
        self.month_offset += 1
        self.refresh_monthly_report()

    def on_button_pressed(self, event: Button.Pressed) -> None:
        """Handle button presses."""
        if event.button.id == "week-prev":
            self.week_offset -= 1
            self.refresh_weekly_report()
        elif event.button.id == "week-next":
            self.week_offset += 1
            self.refresh_weekly_report()
        elif event.button.id == "month-prev":
            self.month_offset -= 1
            self.refresh_monthly_report()
        elif event.button.id == "month-next":
            self.month_offset += 1
            self.refresh_monthly_report()

    def on_switch_changed(self, event: Switch.Changed) -> None:
        """Handle metric toggle switches."""
        if event.switch.id == "week-metric-toggle":
            self.week_metric = "hours" if event.value else "value"
            label = self.query_one("#week-metric-label", Static)
            label.update("Hours" if event.value else "Value (€)")
            header = self.query_one("#weekly-header", Static)
            header.update(f"Weekly Report ({'Hours' if event.value else 'Euros'})")
            self.refresh_weekly_report()
        elif event.switch.id == "month-metric-toggle":
            self.month_metric = "hours" if event.value else "value"
            label = self.query_one("#month-metric-label", Static)
            label.update("Hours" if event.value else "Value (€)")
            header = self.query_one("#monthly-header", Static)
            header.update(f"Monthly Report ({'Hours' if event.value else 'Euros'})")
            self.refresh_monthly_report()

    def run_pipeline(self) -> None:
        """Run the data ingestion pipeline."""
        self.notify("⏳ Starting pipeline...", severity="information")
        self.run_worker(self._run_pipeline_worker, exclusive=True)

    async def _run_pipeline_worker(self) -> None:
        """Worker method to run the pipeline in the background."""
        try:
            process = await asyncio.create_subprocess_exec(
                "uv",
                "run",
                "python",
                "-m",
                "jortt_report",
                cwd=self.project_root,
                stdout=asyncio.subprocess.PIPE,
                stderr=asyncio.subprocess.PIPE,
            )

            try:
                stdout, stderr = await asyncio.wait_for(
                    process.communicate(), timeout=300  # 5 minute timeout
                )
            except asyncio.TimeoutError:
                process.kill()
                await process.wait()
                self.notify(
                    "✗ Pipeline timed out after 5 minutes", severity="error", timeout=5
                )
                return

            if process.returncode == 0:
                self.notify("✓ Pipeline completed successfully", timeout=5)
                # Refresh both reports with latest data
                self.week_offset = 0
                self.month_offset = 0
                self.refresh_weekly_report()
                self.refresh_monthly_report()
            else:
                error_msg = stderr.decode()[:200] if stderr else "Unknown error"
                self.notify(
                    f"✗ Pipeline failed: {error_msg}", severity="error", timeout=10
                )
        except Exception as e:
            self.notify(
                f"✗ Error running pipeline: {str(e)[:100]}", severity="error", timeout=5
            )

    def get_timesheet_data(self) -> pl.DataFrame:
        """Load timesheet data from DuckDB."""
        if not Path(self.database_path).exists():
            self.notify(
                f"Database not found: {self.database_path}",
                severity="warning",
                timeout=5,
            )
            return pl.DataFrame()

        conn = duckdb.connect(str(self.database_path), read_only=True)
        try:
            # Fetch as arrow table and convert to polars to avoid pandas dependency
            result = conn.execute("SELECT * FROM raw.timesheet").fetch_arrow_table()
            df = pl.from_arrow(result)
            if len(df) == 0:
                self.notify("No data in timesheet view", severity="warning", timeout=3)
            return df
        except Exception as e:
            self.notify(f"Error loading data: {str(e)}", severity="error", timeout=5)
            return pl.DataFrame()
        finally:
            conn.close()

    def get_target_week(self) -> tuple[int, int]:
        """Get the target week number and year based on offset."""
        target_date = date.today() + timedelta(weeks=self.week_offset)
        iso_calendar = target_date.isocalendar()
        return iso_calendar.week, iso_calendar.year

    def get_target_month(self) -> tuple[int, int]:
        """Get the target month and year based on offset."""
        today = date.today()
        # Calculate target month by adding offset
        month = today.month + self.month_offset
        year = today.year

        # Handle year boundaries
        while month < 1:
            month += 12
            year -= 1
        while month > 12:
            month -= 12
            year += 1

        return month, year

    def refresh_weekly_report(self) -> None:
        """Refresh the weekly report table."""
        try:
            df = self.get_timesheet_data()
            table = self.query_one("#weekly-table", DataTable)
            title = self.query_one("#week-title", Static)

            table.clear(columns=True)

            if df.is_empty():
                title.update("No data available")
                table.add_column("Status")
                table.add_row("No data in database")
                return

            week_number, year = self.get_target_week()
            title.update(f"Week {week_number}, {year}")

            # Filter data for the target week
            filtered = df.filter(
                (pl.col("time_registration_date").dt.week() == week_number)
                & (pl.col("time_registration_date").dt.year() == year)
            )

            if filtered.is_empty():
                table.add_column("Project")
                table.add_row(f"No data for week {week_number}, {year}")
                return
        except Exception as e:
            self.notify(f"Error refreshing weekly report: {str(e)}", severity="error")
            return

        # Create pivot table
        metric_col = (
            "time_registration_quantity"
            if self.week_metric == "hours"
            else "value_euro"
        )

        pivot = (
            filtered.select(
                pl.concat_str(
                    [
                        pl.col("project_name"),
                        pl.col("customer").fill_null(pl.lit("Intern")),
                    ],
                    separator=" | ",
                ).alias("project"),
                pl.col("time_registration_date"),
                pl.col(metric_col),
            )
            .pivot(
                index="project",
                on="time_registration_date",
                values=metric_col,
                aggregate_function="sum",
            )
            .with_columns(pl.sum_horizontal(pl.all().exclude("project")).alias("TOTAL"))
        )

        # Add columns to table
        table.add_column("Project", key="project")
        for col in pivot.columns[1:]:  # Skip project column
            if col == "TOTAL":
                table.add_column(col, key=col)
            else:
                table.add_column(str(col), key=col)

        # Add rows
        row_count = 0
        for row in pivot.iter_rows():
            formatted_row = [str(row[0])]  # Project name
            for val in row[1:]:
                if val is None:
                    formatted_row.append("")
                elif self.week_metric == "hours":
                    formatted_row.append(f"{val:.1f}")
                else:
                    formatted_row.append(f"€{val:.2f}")
            table.add_row(*formatted_row)
            row_count += 1

        # Add total row
        totals = ["TOTAL"]
        for col in pivot.columns[1:]:
            if col != "project":
                total = pivot[col].sum()
                if total is None:
                    totals.append("")
                elif self.week_metric == "hours":
                    totals.append(f"{total:.1f}")
                else:
                    totals.append(f"€{total:.2f}")
        table.add_row(*totals)

    def refresh_monthly_report(self) -> None:
        """Refresh the monthly report table."""
        try:
            df = self.get_timesheet_data()
            table = self.query_one("#monthly-table", DataTable)
            title = self.query_one("#month-title", Static)

            table.clear(columns=True)

            if df.is_empty():
                title.update("No data available")
                table.add_column("Status")
                table.add_row("No data in database")
                return
        except Exception as e:
            self.notify(f"Error refreshing monthly report: {str(e)}", severity="error")
            return

        target_month, target_year = self.get_target_month()
        month_names = [
            "Jan",
            "Feb",
            "Mar",
            "Apr",
            "May",
            "Jun",
            "Jul",
            "Aug",
            "Sep",
            "Oct",
            "Nov",
            "Dec",
        ]
        title.update(f"{month_names[target_month - 1]} {target_year}")

        # Filter data for the target month
        filtered = df.filter(
            (pl.col("time_registration_date").dt.month() == target_month)
            & (pl.col("time_registration_date").dt.year() == target_year)
        )

        if filtered.is_empty():
            table.add_column("Project")
            table.add_row("No data for this month")
            return

        # Create aggregation by project
        metric_col = (
            "time_registration_quantity"
            if self.month_metric == "hours"
            else "value_euro"
        )

        summary = (
            filtered.select(
                pl.concat_str(
                    [
                        pl.col("project_name"),
                        pl.col("customer").fill_null(pl.lit("Intern")),
                    ],
                    separator=" | ",
                ).alias("project"),
                pl.col(metric_col),
            )
            .group_by("project")
            .agg(
                pl.col(metric_col).sum().alias("total"),
                pl.col(metric_col).count().alias("entries"),
            )
            .sort("project")
        )

        # Add columns
        table.add_column("Project", key="project")
        table.add_column("Total", key="total")
        table.add_column("Entries", key="entries")

        # Add rows
        row_count = 0
        for row in summary.iter_rows():
            project = str(row[0])
            total = row[1]
            entries = row[2]

            if self.month_metric == "hours":
                formatted_total = f"{total:.1f}"
            else:
                formatted_total = f"€{total:.2f}"

            table.add_row(project, formatted_total, str(entries))
            row_count += 1

        # Add total row
        total_sum = summary["total"].sum()
        total_entries = summary["entries"].sum()
        if self.month_metric == "hours":
            formatted_sum = f"{total_sum:.1f}"
        else:
            formatted_sum = f"€{total_sum:.2f}"
        table.add_row("TOTAL", formatted_sum, str(total_entries))


def run_tui() -> None:
    """Run the Textual TUI app."""
    app = TimesheetApp()
    app.run()


if __name__ == "__main__":
    run_tui()
