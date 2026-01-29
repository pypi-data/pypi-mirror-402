# Changelog

All notable changes to this project will be documented in this file.

The format is based on [Keep a Changelog](https://keepachangelog.com/en/1.0.0/),
and this project adheres to [Semantic Versioning](https://semver.org/spec/v2.0.0.html).

## [0.1.0] - 2026-01-14

### Added
- Initial release of jortt-report (formerly jortt-duck)
- Terminal-based timesheet reporting with Textual TUI
- Async pipeline execution for non-blocking data refresh
- Keyboard navigation: arrow keys for weeks, Shift+arrows for months
- Metric toggle: 'm' key to switch between hours and euros
- Custom blue color theme (#3399CC)
- Weekly and monthly report views side-by-side
- OAuth 2.0 authentication with Jortt API
- DLT pipeline with declarative REST API configuration
- DuckDB backend with semantic layer using boring-semantic-layer
- Pre-aggregated tables for fast reporting (daily, weekly, monthly)
- Zero-copy data transfer from DuckDB to Polars via PyArrow
- Comprehensive test suite with 15 tests
- Global installation support via `uvx jortt-report`

### Changed
- Renamed project from `jortt-duck` to `jortt-report` for clarity
- Renamed command from `jortt-tui` to `jortt-report`
- Removed unused dependencies (marimo, black, great-tables, tqdm, pyzmq)
- Optimized notification system to prevent stacking during rapid actions

### Technical Details
- Python 3.11+ required
- Technologies: dlt, DuckDB, Textual, Polars, PyArrow, boring-semantic-layer
- License: GPL-3.0-or-later

[0.1.0]: https://github.com/dkapitan/jortt-report/releases/tag/v0.1.0
