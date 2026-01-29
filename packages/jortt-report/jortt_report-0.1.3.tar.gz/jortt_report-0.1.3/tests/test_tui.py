"""Tests for TUI module."""

import tempfile
from pathlib import Path
from datetime import date
import duckdb
from jortt_report.tui import TimesheetApp


def test_tui_app_initialization():
    """Test that the TUI app can be initialized."""
    app = TimesheetApp()
    assert app is not None
    assert app.week_offset == 0
    assert app.month_offset == 0
    assert app.week_metric == "hours"
    assert app.month_metric == "hours"


def test_get_target_week_current():
    """Test getting the current week."""
    app = TimesheetApp()
    week, year = app.get_target_week()
    today = date.today()
    expected_week = today.isocalendar().week
    expected_year = today.year
    assert week == expected_week
    assert year == expected_year


def test_get_target_week_offset():
    """Test getting a previous week with offset."""
    app = TimesheetApp()
    app.week_offset = -1
    week, year = app.get_target_week()
    # Just verify it returns valid values
    assert isinstance(week, int)
    assert isinstance(year, int)
    assert 1 <= week <= 53
    assert year > 0


def test_get_target_month_current():
    """Test getting the current month."""
    app = TimesheetApp()
    month, year = app.get_target_month()
    today = date.today()
    assert month == today.month
    assert year == today.year


def test_get_target_month_offset():
    """Test getting a previous month with offset."""
    app = TimesheetApp()
    app.month_offset = -1
    month, year = app.get_target_month()
    # Just verify it returns valid values
    assert isinstance(month, int)
    assert isinstance(year, int)
    assert 1 <= month <= 12
    assert year > 0


def test_get_target_month_year_boundaries():
    """Test month offset across year boundaries."""
    app = TimesheetApp()

    # Test going back 13 months
    app.month_offset = -13
    month, year = app.get_target_month()
    today = date.today()

    # Should be one year ago, one month back
    expected_year = today.year - 1
    expected_month = today.month - 1
    if expected_month < 1:
        expected_month = 12
        expected_year -= 1

    assert month == expected_month
    assert year == expected_year


def test_get_timesheet_data_no_database():
    """Test loading timesheet data when database doesn't exist."""
    with tempfile.TemporaryDirectory() as tmpdir:
        app = TimesheetApp()
        app.database_path = str(Path(tmpdir) / "nonexistent.duckdb")

        df = app.get_timesheet_data()
        assert df.is_empty()


def test_get_timesheet_data_empty_database():
    """Test loading timesheet data from empty database."""
    with tempfile.TemporaryDirectory() as tmpdir:
        db_path = Path(tmpdir) / "test.duckdb"

        # Create empty database with schema and view
        conn = duckdb.connect(str(db_path))
        conn.execute("CREATE SCHEMA raw")
        conn.execute("""
            CREATE TABLE raw.projects (
                aggregate_id VARCHAR,
                name VARCHAR,
                customer_record__customer_name VARCHAR
            )
        """)
        conn.execute("""
            CREATE TABLE raw.project_line_items (
                project_id VARCHAR,
                date DATE,
                quantity DOUBLE,
                total_amount__value DOUBLE,
                description VARCHAR,
                created_at TIMESTAMP,
                updated_at TIMESTAMP
            )
        """)
        conn.execute("""
            CREATE VIEW raw.timesheet AS
            SELECT
                p.customer_record__customer_name AS customer,
                p.name AS project_name,
                i.date AS time_registration_date,
                i.quantity AS time_registration_quantity,
                i.total_amount__value AS value_euro,
                i.description AS time_registration_description,
                i.created_at,
                i.updated_at
            FROM
                raw.project_line_items AS i
                LEFT JOIN raw.projects AS p ON p.aggregate_id = i.project_id
        """)
        conn.close()

        # Test loading
        app = TimesheetApp()
        app.database_path = str(db_path)

        df = app.get_timesheet_data()
        assert df.is_empty()


def test_get_timesheet_data_with_data():
    """Test loading timesheet data with actual data."""
    with tempfile.TemporaryDirectory() as tmpdir:
        db_path = Path(tmpdir) / "test.duckdb"

        # Create database with sample data
        conn = duckdb.connect(str(db_path))
        conn.execute("CREATE SCHEMA raw")
        conn.execute("""
            CREATE TABLE raw.projects (
                aggregate_id VARCHAR,
                name VARCHAR,
                customer_record__customer_name VARCHAR
            )
        """)
        conn.execute("""
            INSERT INTO raw.projects VALUES
            ('proj-1', 'Project Alpha', 'Customer A')
        """)

        conn.execute("""
            CREATE TABLE raw.project_line_items (
                project_id VARCHAR,
                date DATE,
                quantity DOUBLE,
                total_amount__value DOUBLE,
                description VARCHAR,
                created_at TIMESTAMP,
                updated_at TIMESTAMP
            )
        """)
        conn.execute("""
            INSERT INTO raw.project_line_items VALUES
            ('proj-1', '2024-01-15', 8.0, 800.0, 'Dev work',
             '2024-01-15 10:00:00', '2024-01-15 10:00:00')
        """)

        conn.execute("""
            CREATE VIEW raw.timesheet AS
            SELECT
                p.customer_record__customer_name AS customer,
                p.name AS project_name,
                i.date AS time_registration_date,
                i.quantity AS time_registration_quantity,
                i.total_amount__value AS value_euro,
                i.description AS time_registration_description,
                i.created_at,
                i.updated_at
            FROM
                raw.project_line_items AS i
                LEFT JOIN raw.projects AS p ON p.aggregate_id = i.project_id
        """)
        conn.close()

        # Test loading
        app = TimesheetApp()
        app.database_path = str(db_path)

        df = app.get_timesheet_data()
        assert not df.is_empty()
        assert len(df) == 1
        assert df["customer"][0] == "Customer A"
        assert df["project_name"][0] == "Project Alpha"
        assert df["time_registration_quantity"][0] == 8.0
        assert df["value_euro"][0] == 800.0
