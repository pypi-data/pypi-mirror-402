"""DLT pipeline for ingesting Jortt API data into local DuckDB."""

import dlt
from dlt.sources.rest_api import rest_api_source
from dlt.destinations.exceptions import DestinationConnectionError
from dlt.pipeline.exceptions import PipelineStepFailed
from pathlib import Path
from datetime import datetime
import duckdb


def get_jortt_config(access_token: str) -> dict:
    """Get the declarative REST API configuration for Jortt API.

    Args:
        access_token: OAuth access token for Jortt API

    Returns:
        Configuration dictionary for dlt rest_api_source
    """
    return {
        "client": {
            "base_url": "https://api.jortt.nl",
            "auth": {
                "type": "bearer",
                "token": access_token,
            },
            "paginator": {
                "type": "json_link",
                "next_url_path": "_links.next.href",
            },
        },
        "resource_defaults": {
            "write_disposition": "replace",
            "primary_key": "aggregate_id",
        },
        "resources": [
            {
                "name": "customers",
                "primary_key": "id",
                "endpoint": {
                    "path": "customers",
                    "data_selector": "data",
                },
                "columns": {
                    "date_of_birth": {"data_type": "date"},
                    "payment_term": {"data_type": "bigint"},
                    "default_discount_percentage": {"data_type": "bigint"},
                },
            },
            {
                "name": "projects",
                "endpoint": {
                    "path": "projects",
                    "params": {
                        "per_page": 100,
                    },
                    "data_selector": "data",
                },
                "columns": {
                    "default_hourly_rate__value": {"data_type": "double"},
                    "minutes_this_month": {"data_type": "bigint"},
                    "total_minutes": {"data_type": "bigint"},
                    "total_value__value": {"data_type": "double"},
                    "customer_record__payment_term": {"data_type": "bigint"},
                    "customer_record__default_discount_percentage": {
                        "data_type": "bigint"
                    },
                },
            },
            {
                "name": "project_line_items",
                "write_disposition": "replace",
                "primary_key": None,
                "endpoint": {
                    "path": "projects/{aggregate_id}/line_items",
                    "params": {
                        "aggregate_id": {
                            "type": "resolve",
                            "resource": "projects",
                            "field": "aggregate_id",
                        },
                    },
                    "data_selector": "data",
                },
                "columns": {
                    "date": {"data_type": "date"},
                    "quantity": {"data_type": "double"},
                    "amount__value": {"data_type": "double"},
                    "total_amount__value": {"data_type": "double"},
                },
            },
        ],
    }


def backup_database(database_path: str) -> str:
    """Backup the database file to the backup folder with a timestamp prefix.

    Args:
        database_path: Path to the database file to backup

    Returns:
        Path to the backup file
    """
    db_path = Path(database_path)

    if not db_path.exists():
        return None

    # Get project root (parent of the database file)
    project_root = db_path.parent
    backup_dir = project_root / "backup"

    # Create backup directory if it doesn't exist
    backup_dir.mkdir(exist_ok=True)

    # Create backup filename with timestamp prefix
    timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
    backup_filename = f"{timestamp}_{db_path.name}"
    backup_path = backup_dir / backup_filename

    # Move the file to backup using Path.rename()
    db_path.rename(backup_path)
    print(f"✓ Backed up database to: {backup_path}")

    return str(backup_path)


def run_pipeline(
    jortt_access_token: str = None,
    database_path: str = "jortt.duckdb",
) -> None:
    """Run the Jortt to local DuckDB pipeline.

    Args:
        jortt_access_token: Jortt API access token
        database_path: Path to local DuckDB database file (default: jortt.duckdb)
    """
    # Get the REST API configuration
    config = get_jortt_config(jortt_access_token)

    # Create the REST API source
    source = rest_api_source(config)

    try:
        # Create the pipeline with local DuckDB destination
        pipeline = dlt.pipeline(
            pipeline_name="jortt_to_duckdb",
            destination=dlt.destinations.duckdb(database_path),
            dataset_name="raw",  # Schema name within the database
            progress=dlt.progress.tqdm(colour="yellow"),
        )

        # Run the pipeline
        load_info = pipeline.run(source)

        # Print the load info
        print(
            "\n✓ Pipeline completed successfully!\n"
            f"Database: {database_path}\n"
            "Schema: raw\n"
            f"Loaded {len(load_info.loads_ids)} load(s)\n"
            "\nLoad details:"
        )
        print(load_info)

    except (duckdb.IOException, DestinationConnectionError, PipelineStepFailed) as e:
        # Check if the error is related to IO/lock issues
        error_msg = str(e)
        if "IO Error" in error_msg or "Could not set lock" in error_msg:
            print(
                "\n⚠ DuckDB IO Error detected\n"
                "Attempting to recover by backing up and recreating the database..."
            )

            # Backup the corrupted/locked database
            backup_path = backup_database(database_path)

            if backup_path:
                print(f"Creating new database at: {database_path}")

                # Retry the pipeline with a fresh database
                pipeline = dlt.pipeline(
                    pipeline_name="jortt_to_duckdb",
                    destination=dlt.destinations.duckdb(database_path),
                    dataset_name="raw",
                )

                load_info = pipeline.run(source)

                print(
                    "\n✓ Pipeline completed successfully after recovery!\n"
                    f"Database: {database_path}\n"
                    "Schema: raw\n"
                    f"Loaded {len(load_info.loads_ids)} load(s)\n"
                    "\nLoad details:"
                )
                print(load_info)
            else:
                raise Exception("Failed to backup database for recovery")
        else:
            # Re-raise if it's not an IO/lock error
            raise
