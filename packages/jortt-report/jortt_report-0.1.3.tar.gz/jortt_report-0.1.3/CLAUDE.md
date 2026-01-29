# CLAUDE.md

This file provides guidance to Claude Code (claude.ai/code) when working with code in this repository.

## Project overview

Jortt API → dlt pipeline → DuckDB → Textual TUI

## Development conventions

- Use dlt pipeline as much as possible with the least amount of vanilla Python
- Use Textual TUI for the terminal-based interface with DuckDB and Polars for data operations


# jortt-report - Development Guide

## CRITICAL: Git Branch Management for AI Assistants

**⚠️ NEVER change git branches, pull, or create new branches without explicit user permission.**

- ✅ **ALWAYS ask before** `git checkout <branch>`
- ✅ **ALWAYS ask before** `git pull` or `git fetch` followed by merge/rebase
- ✅ **ALWAYS ask before** creating new branches
- ✅ **Stay on the branch the user checked out** unless they explicitly ask you to switch
- ❌ **NEVER run `git checkout` on your own**
- ❌ **NEVER run `git pull` on your own**
- ❌ **NEVER create branches autonomously**
- ❌ **NEVER switch branches when starting a new task** - the user has already set up the branch

**If you need to work on a different branch**, ask the user first:
- "Should I switch to branch X to work on this?"
- "Should I create a new branch for this feature?"

**When the user says a PR is merged**, do NOT automatically checkout main and pull. Wait for explicit instructions.

## CRITICAL: Personal Data Protection

**⚠️ NEVER include user's personal data in code, comments, or documentation.**

This is a personal finance application. Users may share screenshots or logs containing real financial data (account names, transaction details, merchant names, etc.) when debugging issues.

- ❌ **NEVER copy personal data** from screenshots/logs into code comments
- ❌ **NEVER use real account names, card numbers, or transaction details** as examples
- ✅ **Use generic examples** like "Account Name", "Example Merchant", etc.
- ✅ **If you need to reference data formats**, use clearly fake data

## Project Overview

jortt-report is a data pipeline and reporting application for Jortt, a book-keeping app. It ingests data using dlt with the Jortt API https://developer.jortt.nl/#jortt-api as the source and DuckDB as the destination. The database is queried using a Textual TUI (Terminal User Interface) for interactive timesheet reporting.

### What Was Built

A complete Python data pipeline that:
1. Authenticates with the Jortt API using OAuth 2.0 Client Credentials
2. Extracts project data from the Jortt API with automatic pagination
3. Loads the data into DuckDB using dlt
4. Creates a semantic layer using boring-semantic-layer for easy querying
5. Generates pre-aggregated tables for common reporting needs
6. Provides an interactive Textual TUI for terminal-based visualization

### Key Features

#### ✓ OAuth 2.0 Authentication
- Automatic token fetching using client credentials
- Standalone auth script for testing (`python -m jortt_report.auth`)
- Supports all Jortt API scopes
- Tokens expire after 2 hours (7200 seconds), automatically refreshed

#### ✓ Data Extraction & Loading
- RESTful API client with pagination support
- Handles Jortt API response structures with error handling and retry logic
- Loads data to DuckDB using dlt with automatic database and schema creation
- Maintains data lineage with dlt metadata tables
- Replace write disposition for full refreshes each run

#### ✓ Semantic Layer & Aggregations
- **Semantic Model** ([jortt_report/datamart.py](jortt_report/datamart.py)) built with boring-semantic-layer
  - **Dimensions**: customer, project_name, registration_date, registration_week, registration_month, registration_year
  - **Measures**: total_hours, total_value, registration_count, avg_hours, avg_value
- **Pre-aggregated Tables**:
  - `raw.timesheet_by_date`: Daily aggregations per project
  - `raw.timesheet_by_week`: Weekly aggregations per project
  - `raw.timesheet_by_month`: Monthly aggregations per project
- Uses ibis with DuckDB backend (no pandas dependency)
- Automatically created after pipeline runs

#### ✓ Textual TUI
- **Terminal UI** ([jortt_report/tui.py](jortt_report/tui.py)): Rich terminal-based interface
  - **Async pipeline execution**: Run data refresh without blocking the UI
  - **Weekly & monthly reports**: Side-by-side timesheet views
  - **Keyboard navigation**: Arrow keys to navigate weeks (left/right), Shift+arrows for months
  - **Metric toggle**: Switch between hours and euros display with 'm' key
  - **Custom theme**: Blue (#3399CC) color scheme for borders, buttons, and scrollbars
  - **Instant notifications**: Non-blocking status updates for pipeline execution
  - Uses DuckDB with Arrow for zero-copy data transfer to Polars
  - Run with: `uv run jortt-report` or install globally with `uvx jortt-report`

### Data Architecture

```
Jortt API → dlt pipeline → DuckDB → Semantic Layer → Aggregation Tables → Textual TUI
```

**Database**: `jortt.duckdb` (or custom via `DATABASE_PATH` env var)
**Schema**: `raw`
**Main Tables**:
- `raw.projects`: Project metadata
- `raw.project_line_items`: Time registration line items
- `raw.customers`: Customer information

**Views**:
- `raw.timesheet`: Unified view joining projects and line items

**Aggregation Tables**:
- `raw.timesheet_by_date`: Daily aggregations
- `raw.timesheet_by_week`: Weekly aggregations
- `raw.timesheet_by_month`: Monthly aggregations

### Technologies Used

- **Python 3.13**
- **dlt**: Data loading framework with declarative REST API source
- **DuckDB**: Embedded analytics database
- **boring-semantic-layer**: Lightweight semantic layer built on ibis
- **ibis**: Database abstraction layer
- **textual**: Terminal UI framework for building rich TUIs
- **polars**: Fast DataFrame library for data manipulation
- **uv**: Fast Python package manager
- **requests**: HTTP client for OAuth
- **python-dotenv**: Environment variable management


## Quick Start

```bash
# First time setup
uv sync

# Run the pipeline (ingests data from Jortt API)
uv run python -m jortt_report

# Launch the Textual TUI (terminal-based)
uv run jortt-report

# Or install globally and run from anywhere
uvx jortt-report

# Run all tests
uv run pytest -v

# Run tests with coverage
uv run pytest --cov --cov-report=html

# Run specific test file
uv run pytest tests/test_datamart.py -v

# Test OAuth authentication
uv run python -m jortt_report.auth
```

### Environment Variables

Create a `.env` file in the project root:

```bash
JORTT_CLIENT_ID=your_client_id
JORTT_CLIENT_SECRET=your_client_secret
DATABASE_PATH=jortt.duckdb  # Optional, defaults to jortt.duckdb in project root
```

## Development Setup

### Using uv (REQUIRED)

**IMPORTANT**: This project uses **uv** exclusively for all development workflows. Always use `uv run` for executing scripts. Never use pip, pipenv, poetry, or other package managers.

**CRITICAL FOR AI ASSISTANTS (Claude Code, etc.)**:
- ❌ **NEVER run `pip install` or `uv pip install` to modify the user's environment**
- ❌ **NEVER run `uv tool install` for project dependencies**
- ✅ All dependencies MUST be declared in `pyproject.toml` and installed via `uv sync`
- ✅ Use `uv run <command>` to run tools in the project's virtual environment
- 💡 This ensures **reproducibility** - anyone can clone the repo and run `uv sync` to get the exact same environment

```bash
# Install uv if not already installed
curl -LsSf https://astral.sh/uv/install.sh | sh

# FIRST TIME SETUP: Sync dependencies (includes dev dependencies for testing)
uv sync

# This creates a virtual environment and installs all dependencies
# You MUST run this before running tests or the TUI for the first time

# After sync, run the TUI
uv run jortt-report

# Run tests (ALWAYS before committing)
uv run pytest

# Run tests with coverage
uv run pytest --cov --cov-report=html

# View coverage report
open htmlcov/index.html
```

**If you get `ModuleNotFoundError`**: Run `uv sync` first!

### Test-Driven Development (CRITICAL)

**This project handles financial data. We cannot afford slip-ups.**

**MANDATORY WORKFLOW**:
1. **Write tests first** for any new feature or bug fix
2. **Run tests** - verify they fail as expected
3. **Implement** the feature/fix
4. **Run tests again** - verify all tests pass
5. **Check coverage** - ensure new code is tested
6. **Only commit when tests are green**

**Before EVERY commit**:
```bash
# Run full test suite
uv run pytest -v

# Run type checker
uv run pyright jortt-report/

# Check coverage
uv run pytest --cov --cov-report=term-missing

# Check markdown formatting (if docs changed)
markdownlint --config .markdownlint.json README.md 'docs/**/*.md'
.github/scripts/check-arrow-lists.sh
```

**All tests must pass, type checking must be clean, and markdown must be properly formatted before committing.** No exceptions.

### Project Structure

**IMPORTANT**: All Python source code must be in the `jortt_report/` package. No Python files should live at the top level.

```
jortt-report/
├── jortt_report/                  # Main package (ALL code goes here)
│   ├── __init__.py              # Package initialization
│   ├── __main__.py              # CLI entry point - runs pipeline
│   ├── tui.py                   # Textual terminal UI (command: jortt-report)
│   ├── auth.py                  # OAuth 2.0 authorization for Jortt API
│   ├── pipeline.py              # dlt pipeline definition
│   └── datamart.py              # Semantic layer & aggregation tables
├── tests/                       # Test suite
│   ├── test_datamart.py         # Tests for semantic layer
│   ├── test_tui.py              # Tests for TUI
│   └── conftest.py              # Test fixtures (if needed)
├── backup/                      # Folder for older DuckDB files
├── .env                         # Credentials (not in git)
├── .gitignore                   # Git ignore rules
├── pyproject.toml               # Project metadata and dependencies
├── README.md                    # User documentation
└── CLAUDE.md                    # This file - development guide
```

**File Organization Rules**:
- ✅ All business logic in `jortt_report/` package
- ✅ All tests in `tests/` directory
- ✅ Entry point via `python -m jortt_report` (configured in `__main__.py`)
- ❌ No `.py` files at top level
- ❌ No duplicate files between top-level and package

### Module Descriptions

- **`auth.py`**: OAuth 2.0 client credentials flow for Jortt API authentication
- **`pipeline.py`**:
  - Declarative REST API configuration using dlt's rest_api_source
  - Automatic pagination handling
  - Database backup and recovery on IO errors
  - Ingests: customers, projects, project_line_items
- **`datamart.py`**:
  - `create_timesheet_view()`: Creates unified timesheet view
  - `get_timesheet_semantic_model()`: Returns boring-semantic-layer SemanticModel with dimensions and measures
  - `create_aggregation_tables()`: Generates pre-aggregated tables for daily, weekly, monthly reporting
  - `create_all_views()`: Orchestrates all view and table creation
- **`tui.py`**: Textual terminal UI with:
  - Async pipeline execution with real-time status
  - Weekly and monthly reports side-by-side
  - Keyboard navigation (arrows for weeks, Shift+arrows for months)
  - Metric toggle ('m' key to switch between hours and euros)
  - Custom blue color theme (#3399CC)
  - Uses Arrow for zero-copy data transfer from DuckDB to Polars

## Testing Strategy

**IMPORTANT**: All business logic must be tested before running against real data.

### Testing Architecture

1. **Temporary Test Databases**: Tests use `tempfile.TemporaryDirectory()` to create isolated test databases that are automatically cleaned up after each test.

2. **Test Fixtures**: Tests create their own sample data in-memory to avoid dependencies on external APIs or real data.

3. **Separation of Concerns**:
   - `datamart.py`: Pure database operations - testable with temporary DuckDB instances
   - `pipeline.py`: dlt pipeline with declarative configuration - integration tests would use mock API
   - `auth.py`: OAuth flow - unit testable with mocked requests

### What We Test

- ✅ **Semantic Layer**: Model creation, dimension/measure definitions, query compilation
- ✅ **View Creation**: Timesheet view creation with proper schema
- ✅ **Aggregation Tables**: Daily, weekly, monthly aggregations with correct calculations
- ✅ **Time-based Grouping**: Date truncation for week/month boundaries
- ✅ **Data Integrity**: Proper joins, null handling, aggregation accuracy
- ✅ **Edge Cases**: Empty databases, missing data, connection management

### Running Tests

**ALWAYS use `uv run` for running tests:**

```bash
# Run all tests (run before EVERY commit)
uv run pytest -v

# Run with coverage report
uv run pytest --cov --cov-report=html --cov-report=term-missing

# Run specific test file
uv run pytest tests/test_state.py -v

# Run tests matching a pattern
uv run pytest -k "test_undo" -v

# Run and stop on first failure
uv run pytest -x

# Run and show local variables on failure
uv run pytest -l
```

### Coverage Requirements

**Business Logic Coverage Target: >90%**

Core modules (`datamart.py`, `pipeline.py`, `auth.py`) must maintain high coverage.

**Current Coverage**:
- `datamart.py`: 100% (6 tests covering all functions)

View coverage report:
```bash
uv run pytest --cov --cov-report=html
open htmlcov/index.html
```

### Test-Driven Development Workflow

1. Write tests first for new features
2. Run tests to verify they fail
3. Implement the feature
4. Run tests to verify they pass
5. Refactor while keeping tests green

### Testing Best Practices

- **No pandas/numpy in tests**: Use DuckDB's native `.fetchall()` for assertions to avoid extra dependencies
- **Connection management**: Always close connections in `finally` blocks or use context managers
- **Avoid DuckDB conflicts**: Don't create multiple connections with different configurations to the same database
- **Use ibis connection's raw DuckDB connection**: Access via `ibis_con.con` for DDL operations

## Code Quality Checks

**CRITICAL**: All code quality checks MUST pass before committing. This ensures consistent code quality and prevents regressions.

### Required Checks (run before EVERY commit)

```bash
# 1. Run full test suite
uv run pytest -v

# 2. Type checking (pyright)
uv run pyright jortt-report/

# 3. Code formatting (ruff format)
uv run ruff format --check jortt-report/ tests/

# 4. Linting (ruff check)
uv run ruff check jortt-report/ tests/

# 5. Markdown formatting (if docs changed)
markdownlint --config .markdownlint.json README.md 'docs/**/*.md'
.github/scripts/check-arrow-lists.sh
```

**All checks must pass with zero errors** before creating a commit or release.

**Note:** Markdown checks (5) only need to run if you've modified documentation files (README.md or docs/).

### Auto-Fixing Issues

```bash
# Auto-format code
uv run ruff format jortt-report/ tests/

# Auto-fix linting issues
uv run ruff check --fix jortt-report/ tests/
```

### Configuration

- `pyproject.toml` contains configuration for ruff and pyright
- Line length: 100 characters
- Target Python version: 3.13

## Code Style

- **Use type hints** for all function signatures
- **No inline imports**: All imports must be at the top of the file, not inside functions/methods
  - Inline imports are slower (import happens on every call)
  - Harder to see dependencies at a glance
  - Exception: Circular import issues (rare)
- **PEP-8 implicit line continuation**: Use implicit line continuation inside parentheses for multi-line strings
  - ✅ Good: `print("Line 1\n" "Line 2\n" "Line 3")`
  - ✅ Good: Use parentheses for natural line breaks in long statements
  - ❌ Bad: Multiple print statements for related output
  - ❌ Bad: Backslash (`\`) for line continuation (use parentheses instead)
  - This keeps output atomic and improves readability
- **Document complex logic** with comments explaining "why", not "what"
- **Keep functions focused** - Single responsibility, easy to test
- **Use meaningful variable names** - Prefer clarity over brevity


## Common Tasks

### Adding a New API Endpoint to Pipeline

1. Update `pipeline.py` declarative configuration:
   ```python
   "resources": [
       {
           "name": "invoices",
           "endpoint": {
               "path": "invoices",
               "params": {"per_page": 100},
               "data_selector": "data",
           },
       }
   ]
   ```
2. Run pipeline to test: `uv run python -m jortt_report`
3. Verify data in DuckDB: `duckdb jortt.duckdb`

### Adding New Aggregation Tables

1. Update `datamart.py` `get_timesheet_semantic_model()` to add dimensions/measures
2. Update `create_aggregation_tables()` to generate new tables
3. Write tests in `tests/test_datamart.py`
4. Run tests: `uv run pytest tests/test_datamart.py -v`

### Updating Dependencies

```bash
# Add new dependency to pyproject.toml manually, then:
uv sync

# Or add directly
uv add package-name

# Update all dependencies
uv lock --upgrade
uv sync
```

## Git Workflow

**CRITICAL**: Never commit without running all code quality checks first!

**IMPORTANT**: When working with Claude Code or AI assistants:
- ✅ AI can create commits locally
- ❌ AI must NEVER push to git without explicit user permission
- ❌ AI must NEVER create new branches unless explicitly asked by the user
- ❌ AI must NEVER amend commits unless explicitly asked by the user
- 💡 User should review commits before pushing

```bash
# MANDATORY: Run all code quality checks before committing
uv run pytest -v                          # All tests must pass
uv run pyright jortt-report/                 # Type checking must be clean
uv run ruff format --check jortt-report/ tests/  # Code must be formatted
uv run ruff check jortt-report/ tests/       # Linting must pass

# Only if ALL checks pass, then commit
git add -A
git commit -m "Descriptive commit message"

# WAIT for user approval before pushing
# git push origin main

# Use conventional commit format
# feat: New feature
# fix: Bug fix
# test: Adding tests
# refactor: Code refactoring
# docs: Documentation updates
```

**Pre-commit Checklist** (ALL must pass):
- [ ] All tests pass (`uv run pytest -v`)
- [ ] Type checking passes (`uv run pyright jortt-report/`)
- [ ] Code formatting passes (`uv run ruff format --check jortt-report/ tests/`)
- [ ] Linting passes (`uv run ruff check jortt-report/ tests/`)
- [ ] Markdown formatting passes (if docs changed):
  - `markdownlint --config .markdownlint.json README.md 'docs/**/*.md'`
  - `.github/scripts/check-arrow-lists.sh`
- [ ] Coverage hasn't decreased
- [ ] No debug print statements left in code
- [ ] Updated tests for any changed behavior
- [ ] Ran with real test data if changing API logic

## Implementation History

### Session: Semantic Layer & Aggregation Tables (2026-01-14)

**Objective**: Create aggregation tables using boring-semantic-layer for timesheet reporting.

**What was built**:

1. **Semantic Layer Integration** ([jortt_report/datamart.py](jortt_report/datamart.py))
   - Created `get_timesheet_semantic_model()` function using boring-semantic-layer
   - Defined 6 dimensions: customer, project_name, registration_date/week/month/year
   - Defined 5 measures: total_hours, total_value, registration_count, avg_hours, avg_value
   - Uses ibis with DuckDB backend (avoiding pandas dependency)
   - Connection management to avoid DuckDB multi-connection conflicts

2. **Aggregation Tables** ([jortt_report/datamart.py](jortt_report/datamart.py))
   - `create_aggregation_tables()` function generates three materialized tables:
     - `raw.timesheet_by_date`: Daily aggregations per customer/project
     - `raw.timesheet_by_week`: Weekly aggregations per customer/project
     - `raw.timesheet_by_month`: Monthly aggregations per customer/project
   - All tables include all measures (total_hours, total_value, registration_count, avg_hours, avg_value)
   - Compiled from semantic layer expressions to optimized SQL

3. **Pipeline Integration** ([jortt_report/__main__.py](jortt_report/__main__.py))
   - Modified to call `create_all_views()` after pipeline completion
   - Automatically creates view and aggregation tables on every run

4. **Comprehensive Testing** ([tests/test_datamart.py](tests/test_datamart.py))
   - 6 tests covering all functionality
   - Tests verify semantic model creation and querying
   - Tests validate aggregation table creation with sample data
   - Tests check aggregations across different time periods
   - All tests use DuckDB directly (no pandas) for assertions
   - All tests pass ✓

**Key decisions**:
- Used ibis with DuckDB backend instead of pandas to avoid extra dependencies
- Managed connection lifecycle carefully to avoid DuckDB's "different configuration" error
- Followed boring-semantic-layer patterns from official test examples
- Used `.compile()` to generate SQL from semantic layer for table materialization

**Testing approach**:
- Added pytest and pytest-cov as dev dependencies
- Tests use temporary databases to avoid side effects
- Tests execute compiled SQL directly using DuckDB connections
- No pandas/numpy dependencies in test assertions

**Resources used**:
- [boring-semantic-layer GitHub](https://github.com/boringdata/boring-semantic-layer)
- [boring-semantic-layer real-world scenarios tests](https://github.com/boringdata/boring-semantic-layer/blob/main/boring_semantic_layer/tests/test_real_world_scenarios.py)
- boring-semantic-layer follows patterns inspired by [Malloy](https://github.com/malloydata/malloy)

**Extensibility**:
The semantic model can be easily extended to add:
- More dimensions (e.g., year, quarter, day of week)
- More measures (e.g., median hours, max/min values)
- Additional aggregation tables (e.g., by customer only, by year)
- Joins to other tables (e.g., customers for additional attributes)

### Initial Build Session

**Objective**: Build complete Jortt API → DuckDB pipeline.

This project was vibe-coded with Claude Code. It took about half an hour with ~5 corrections to steer in the right direction (e.g., to use dlt's declarative API). Total Claude token cost: ~$3.

**What was built**:
- OAuth 2.0 client credentials authentication
- dlt pipeline with declarative REST API configuration
- DuckDB database creation and loading
- Automatic pagination handling for Jortt API
- Error handling and database backup/recovery
- Successfully tested and ingested 3 project records

**Next Steps / Future Extensibility**:

The pipeline can be easily extended to ingest other Jortt API resources:
- **Invoices**: `/invoices` endpoint
- **Invoice line items**: `/invoices/{id}/line_items`
- **Organizations**: `/organizations` endpoint
- **Reports**: Various reporting endpoints

Simply add new resource configurations to `pipeline.py` following the existing patterns in the declarative REST API config.

### Session: TUI Improvements & UX Polish (2026-01-14)

**Objective**: Enhance the Textual TUI with better UX, keyboard navigation, theming, and async operations.

**What was built**:

1. **Color Scheme Customization** ([jortt_report/tui.py](jortt_report/tui.py))
   - Changed primary color from orange to blue (#3399CC)
   - Updated panel borders, scrollbars, and buttons
   - Note: Footer key colors remain orange (Textual limitation - hardcoded in Footer widget)

2. **Keyboard Navigation Enhancements**
   - Added arrow key bindings for week navigation (left/right)
   - Added Shift+arrow keys for month navigation (Shift+left/right on macOS)
   - Added 'm' key to toggle between hours and euros metrics
   - All navigation actions work without blocking the UI

3. **Notification System Improvements**
   - Removed notifications from repetitive actions (navigation, metric toggle)
   - Kept notifications for important events (pipeline start/completion, errors)
   - Fixed notification stacking issue during rapid key presses
   - Added immediate "⏳ Starting pipeline..." notification

4. **Async Pipeline Execution** ([jortt_report/tui.py](jortt_report/tui.py))
   - Converted pipeline execution to async worker using `run_worker()`
   - Replaced blocking `subprocess.run()` with `asyncio.create_subprocess_exec()`
   - Pipeline now runs in background without freezing the UI
   - Notification appears instantly when 'r' is pressed
   - Proper timeout handling with async/await
   - `exclusive=True` prevents multiple pipelines from running simultaneously

5. **Dynamic Header Updates**
   - Weekly/monthly report headers show current metric: "(Hours)" or "(Euros)"
   - Headers update automatically when toggling metrics or using switches

**Key technical decisions**:
- Used `asyncio` for non-blocking subprocess execution
- Used `run_worker()` with `exclusive=True` for background tasks
- Removed unused `subprocess` import after async migration
- Notification strategy: only show for significant events, not repetitive actions

**UX improvements**:
- ⚡ Instant feedback when starting pipeline (no delay)
- 🎨 Consistent blue color theme throughout the app
- ⌨️ Intuitive keyboard shortcuts for all actions
- 🔕 Reduced notification noise during navigation
- 📊 Clear visual indication of current metric in headers

**Testing**:
- All 15 tests pass (9 TUI tests + 6 datamart tests)
- No breaking changes to existing functionality
- Async operations properly tested
