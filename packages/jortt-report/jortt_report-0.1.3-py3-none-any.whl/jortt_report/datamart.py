"""Datamart views for Jortt data."""

import duckdb
import ibis
from pathlib import Path
from boring_semantic_layer import to_semantic_table


def create_timesheet_view(database_path: str | Path) -> None:
    """Create the timesheet view in the database.

    This view combines project line items with project information to create
    a comprehensive timesheet with customer, project, and time registration details.

    Args:
        database_path: Path to the DuckDB database file
    """
    db_path = Path(database_path) if isinstance(database_path, str) else database_path

    if not db_path.exists():
        raise FileNotFoundError(f"Database not found at: {db_path}")

    # Connect to the database
    conn = duckdb.connect(str(db_path))

    try:
        # Create the timesheet view
        conn.execute("""
            CREATE OR REPLACE VIEW raw.timesheet AS
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
            ORDER BY
                time_registration_date,
                customer
        """)

        print("✓ Created view: raw.timesheet")

    finally:
        conn.close()


def get_timesheet_semantic_model(database_path: str | Path, con=None):
    """Get the timesheet semantic model with dimensions and measures.

    This creates a semantic layer on top of the timesheet view with:
    - Dimensions: customer, project_name, date-based groupings
    - Measures: sum of hours and value, count of registrations

    Args:
        database_path: Path to the DuckDB database file
        con: Optional ibis connection to reuse. If not provided, creates a new connection.

    Returns:
        tuple: (SemanticModel, connection) - Configured semantic model and the connection used
    """
    db_path = Path(database_path) if isinstance(database_path, str) else database_path

    if not db_path.exists():
        raise FileNotFoundError(f"Database not found at: {db_path}")

    # Connect to DuckDB using ibis if connection not provided
    close_con = False
    if con is None:
        con = ibis.duckdb.connect(str(db_path), read_only=True)
        close_con = True

    # Load the timesheet view as an ibis table
    timesheet_tbl = con.table("timesheet", database="raw")

    # Create semantic model with dimensions and measures
    timesheet_model = (
        to_semantic_table(timesheet_tbl, name="timesheet")
        .with_dimensions(
            customer=lambda t: t.customer,
            project_name=lambda t: t.project_name,
            registration_date=lambda t: t.time_registration_date,
            registration_week=lambda t: t.time_registration_date.truncate("week"),
            registration_month=lambda t: t.time_registration_date.truncate("month"),
            registration_year=lambda t: t.time_registration_date.truncate("year"),
        )
        .with_measures(
            total_hours=lambda t: t.time_registration_quantity.sum(),
            total_value=lambda t: t.value_euro.sum(),
            registration_count=lambda t: t.time_registration_date.count(),
            avg_hours=lambda t: t.time_registration_quantity.mean(),
            avg_value=lambda t: t.value_euro.mean(),
        )
    )

    return timesheet_model, con, close_con


def create_aggregation_tables(database_path: str | Path) -> None:
    """Create aggregation tables for timesheet data.

    Creates three materialized tables:
    - timesheet_by_date: Daily aggregations per project
    - timesheet_by_week: Weekly aggregations per project
    - timesheet_by_month: Monthly aggregations per project

    Args:
        database_path: Path to the DuckDB database file
    """
    db_path = Path(database_path) if isinstance(database_path, str) else database_path

    if not db_path.exists():
        raise FileNotFoundError(f"Database not found at: {db_path}")

    # Connect to DuckDB using ibis (for semantic model)
    ibis_con = ibis.duckdb.connect(str(db_path))

    # Get the semantic model using the same connection
    timesheet_model, _, _ = get_timesheet_semantic_model(db_path, con=ibis_con)

    # Get the raw DuckDB connection from ibis for DDL operations
    raw_conn = ibis_con.con

    try:
        # Daily aggregation by project
        daily_agg = (
            timesheet_model.group_by("customer", "project_name", "registration_date")
            .aggregate(
                "total_hours",
                "total_value",
                "registration_count",
                "avg_hours",
                "avg_value",
            )
            .order_by("registration_date", "customer")
        )

        # Create table from the aggregation
        raw_conn.execute("DROP TABLE IF EXISTS raw.timesheet_by_date")
        raw_conn.execute(f"CREATE TABLE raw.timesheet_by_date AS {daily_agg.compile()}")
        print("✓ Created table: raw.timesheet_by_date")

        # Weekly aggregation by project
        weekly_agg = (
            timesheet_model.group_by("customer", "project_name", "registration_week")
            .aggregate(
                "total_hours",
                "total_value",
                "registration_count",
                "avg_hours",
                "avg_value",
            )
            .order_by("registration_week", "customer")
        )

        raw_conn.execute("DROP TABLE IF EXISTS raw.timesheet_by_week")
        raw_conn.execute(
            f"CREATE TABLE raw.timesheet_by_week AS {weekly_agg.compile()}"
        )
        print("✓ Created table: raw.timesheet_by_week")

        # Monthly aggregation by project
        monthly_agg = (
            timesheet_model.group_by("customer", "project_name", "registration_month")
            .aggregate(
                "total_hours",
                "total_value",
                "registration_count",
                "avg_hours",
                "avg_value",
            )
            .order_by("registration_month", "customer")
        )

        raw_conn.execute("DROP TABLE IF EXISTS raw.timesheet_by_month")
        raw_conn.execute(
            f"CREATE TABLE raw.timesheet_by_month AS {monthly_agg.compile()}"
        )
        print("✓ Created table: raw.timesheet_by_month")

    finally:
        ibis_con.disconnect()


def create_all_views(database_path: str | Path) -> None:
    """Create all datamart views and aggregation tables in the database.

    Args:
        database_path: Path to the DuckDB database file
    """
    create_timesheet_view(database_path)
    create_aggregation_tables(database_path)
