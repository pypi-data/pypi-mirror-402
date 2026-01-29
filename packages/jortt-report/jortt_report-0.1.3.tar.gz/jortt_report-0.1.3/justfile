default: load report

# ingest data from jortt API (full load)
load:
    uv run python -m jortt_report

# launch terminal UI
report:
    uv run jortt-report

# analyze using DuckDB CLI
duck:
    duckdb jortt.duckdb