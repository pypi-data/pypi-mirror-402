"""Tests for datamart module."""

import tempfile
from pathlib import Path
import duckdb
import pytest
from jortt_report.datamart import (
    create_timesheet_view,
    create_all_views,
    get_timesheet_semantic_model,
    create_aggregation_tables,
)


def test_create_timesheet_view_with_empty_database():
    """Test creating timesheet view in an empty database."""
    with tempfile.TemporaryDirectory() as tmpdir:
        db_path = Path(tmpdir) / "test.duckdb"

        # Create empty database with schema and tables
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
        conn.close()

        # Create the view
        create_timesheet_view(db_path)

        # Verify the view exists and can be queried
        conn = duckdb.connect(str(db_path))
        result = conn.execute("SELECT * FROM raw.timesheet").fetchall()
        assert result == []  # Empty database should return empty result

        # Verify view structure
        columns = conn.execute("DESCRIBE raw.timesheet").fetchall()
        column_names = [col[0] for col in columns]
        assert "customer" in column_names
        assert "project_name" in column_names
        assert "time_registration_date" in column_names
        assert "time_registration_quantity" in column_names
        assert "value_euro" in column_names
        assert "time_registration_description" in column_names

        conn.close()


def test_create_timesheet_view_with_data():
    """Test creating timesheet view with sample data."""
    with tempfile.TemporaryDirectory() as tmpdir:
        db_path = Path(tmpdir) / "test.duckdb"

        # Create database with schema, tables, and sample data
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
            ('proj-1', 'Project Alpha', 'Customer A'),
            ('proj-2', 'Project Beta', 'Customer B')
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
            ('proj-1', '2024-01-15', 8.0, 800.0, 'Development work',
             '2024-01-15 10:00:00', '2024-01-15 10:00:00'),
            ('proj-2', '2024-01-16', 4.0, 400.0, 'Consulting',
             '2024-01-16 11:00:00', '2024-01-16 11:00:00')
        """)
        conn.close()

        # Create the view
        create_timesheet_view(db_path)

        # Verify the view returns correct data
        conn = duckdb.connect(str(db_path))
        result = conn.execute(
            "SELECT * FROM raw.timesheet ORDER BY time_registration_date"
        ).fetchall()

        assert len(result) == 2
        assert result[0][0] == "Customer A"  # customer
        assert result[0][1] == "Project Alpha"  # project_name
        assert result[0][3] == 8.0  # time_registration_quantity
        assert result[0][4] == 800.0  # value_euro

        assert result[1][0] == "Customer B"
        assert result[1][1] == "Project Beta"
        assert result[1][3] == 4.0
        assert result[1][4] == 400.0

        conn.close()


def test_create_timesheet_view_nonexistent_database():
    """Test that creating view on nonexistent database raises error."""
    with tempfile.TemporaryDirectory() as tmpdir:
        db_path = Path(tmpdir) / "nonexistent.duckdb"

        with pytest.raises(FileNotFoundError):
            create_timesheet_view(db_path)


def test_create_all_views():
    """Test creating all datamart views."""
    with tempfile.TemporaryDirectory() as tmpdir:
        db_path = Path(tmpdir) / "test.duckdb"

        # Create empty database with schema and tables
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
        conn.close()

        # Create all views
        create_all_views(db_path)

        # Verify the timesheet view exists
        conn = duckdb.connect(str(db_path))
        result = conn.execute("SELECT * FROM raw.timesheet").fetchall()
        assert result == []
        conn.close()


def test_get_timesheet_semantic_model():
    """Test getting timesheet semantic model."""
    with tempfile.TemporaryDirectory() as tmpdir:
        db_path = Path(tmpdir) / "test.duckdb"

        # Create database with schema, tables, and sample data
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
            ('proj-1', '2024-01-15', 8.0, 800.0, 'Development work',
             '2024-01-15 10:00:00', '2024-01-15 10:00:00')
        """)
        conn.close()

        # Create the timesheet view first
        create_timesheet_view(db_path)

        # Get the semantic model
        model, ibis_con, close_con = get_timesheet_semantic_model(db_path)

        try:
            # Verify we can query it by compiling to SQL
            query = model.group_by("customer").aggregate("total_hours", "total_value")

            # Use the existing ibis connection's raw DuckDB connection
            result = ibis_con.con.execute(query.compile()).fetchall()

            assert len(result) == 1
            assert result[0][0] == "Customer A"  # customer
            assert result[0][1] == 8.0  # total_hours
            assert result[0][2] == 800.0  # total_value
        finally:
            if close_con:
                ibis_con.disconnect()


def test_create_aggregation_tables():
    """Test creating aggregation tables with time-based groupings."""
    with tempfile.TemporaryDirectory() as tmpdir:
        db_path = Path(tmpdir) / "test.duckdb"

        # Create database with schema, tables, and sample data
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
            ('proj-1', 'Project Alpha', 'Customer A'),
            ('proj-2', 'Project Beta', 'Customer B')
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
             '2024-01-15 10:00:00', '2024-01-15 10:00:00'),
            ('proj-1', '2024-01-16', 6.0, 600.0, 'Dev work',
             '2024-01-16 10:00:00', '2024-01-16 10:00:00'),
            ('proj-2', '2024-01-22', 4.0, 400.0, 'Consulting',
             '2024-01-22 11:00:00', '2024-01-22 11:00:00'),
            ('proj-1', '2024-02-05', 8.0, 800.0, 'Dev work',
             '2024-02-05 10:00:00', '2024-02-05 10:00:00')
        """)
        conn.close()

        # Create the timesheet view first
        create_timesheet_view(db_path)

        # Create aggregation tables
        create_aggregation_tables(db_path)

        # Verify daily aggregation table
        conn = duckdb.connect(str(db_path))
        daily = conn.execute("""
            SELECT * FROM raw.timesheet_by_date
            ORDER BY registration_date, customer
        """).fetchall()

        assert len(daily) == 4  # 4 distinct dates
        # Calculate total hours from rows (column index depends on position)
        total_hours_daily = sum(row[3] for row in daily)  # total_hours is 4th column
        assert total_hours_daily == 26.0  # 8+6+4+8

        # Verify weekly aggregation table
        weekly = conn.execute("""
            SELECT * FROM raw.timesheet_by_week
            ORDER BY registration_week, customer
        """).fetchall()

        assert len(weekly) == 3  # 2 weeks in Jan + 1 week in Feb
        total_hours_weekly = sum(row[3] for row in weekly)
        assert total_hours_weekly == 26.0

        # Verify monthly aggregation table
        monthly = conn.execute("""
            SELECT registration_month, SUM(total_hours) as total
            FROM raw.timesheet_by_month
            GROUP BY registration_month
            ORDER BY registration_month
        """).fetchall()

        assert len(monthly) == 2  # January and February

        # Check January totals (first row)
        assert monthly[0][1] == 18.0  # 8+6+4

        # Check February totals (second row)
        assert monthly[1][1] == 8.0

        conn.close()
