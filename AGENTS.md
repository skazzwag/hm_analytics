# Horror Movie Analytics - Agent Instructions

## Project Context

This project analyzes the influence of violence and gore on horror movie reception. It ingests data from TMDB and OMDb APIs into a DuckDB/MotherDuck database using dlt, and uses Anthropic's API to classify violence/gore levels in movies.

**Project Structure:**
- `ingestion/`: dlt pipelines for data extraction (TMDB, OMDb, Anthropic)
- `transformation/`: dbt Core transformations (staging models, marts)
- `visualisation/`: Marimo analysis notebooks
- `.dlt/config.toml`: Non-secret pipeline configuration

## Development Environment

- **Python Version**: 3.12.10 (see `.python-version`)
- **Package Manager**: uv (use `uv run` instead of `python3` or `python`)
- **Dependencies**: dlt, dbt-duckdb, pandas, numpy, marimo, requests

## Execution Commands

- Install dependencies: `uv sync`
- Run ingestion pipeline: `uv run ingestion/run_pipeline.py`
- Run dbt commands: `uv run dbt <command>` (e.g., `uv run dbt run`)
- Run Python scripts: `uv run python <script.py>`

## Database Access

### Local Development
- Use the **DuckDB CLI** for local database operations
- Local DuckDB file: `raw.duckdb` (default destination)

### Production/Data Warehouse
- **MotherDuck** is used for production data storage
- Use the **MotherDuck MCP server** (`motherduck_*` tools) when:
  - Querying production data in MotherDuck
  - Working with data already in the warehouse
  - Accessing shared databases or cross-database queries
- Use the **dbt MCP server** (`dbt_*` tools) for dbt project operations
- Use the **dlt-workspace-mcp** server (`dlt-workspace-mcp_*` tools) for dlt pipeline operations

### When to Use Which
| Scenario | Tool/Command |
|----------|--------------|
| Local DuckDB queries | DuckDB CLI or `dbt show` |
| MotherDuck production queries | `motherduck_query` |
| dbt model development | `dbt_*` tools or `uv run dbt` |
| dlt pipeline operations | `dlt-workspace-mcp_*` tools or `uv run dlt` |
| Cross-database queries | MotherDuck MCP |

## Python Coding Style

### Function-Focused Approach
- **Prefer functions** over classes for most logic
- Use classes **only** when:
  - Improving type hints with dataclasses or TypedDict
  - Managing environment variable configurations
  - Implementing well-defined interfaces or protocols
  - When the class provides clear organizational benefits

### Type Hints
- Always use type hints for function parameters and return values
- Use `typing` module types (Iterator, Optional, etc.) where appropriate
- For data structures, prefer:
  - `dict`/`list` with type parameters for simple cases
  - `TypedDict` for structured dictionaries
  - `@dataclass` for data containers with methods

### Imports
- Group imports: standard library, third-party, local
- Use absolute imports within the project
- Example from existing code:
  ```python
  import argparse
  import logging
  import os
  from datetime import datetime, timezone
  from typing import Iterator
  
  import dlt
  import requests
  from dlt.common.typing import TDataItems
  ```

### Error Handling
- Use specific exception types where possible
- Include context in error messages
- Example pattern:
  ```python
  try:
      response = requests.get(url, params=params, timeout=30)
      response.raise_for_status()
  except requests.HTTPError as e:
      logger.error(f"API request failed for {url}: {e}")
      raise
  ```

### Logging
- Use module-level loggers: `logger = logging.getLogger(__name__)`
- Include relevant context in log messages
- Follow existing patterns: `logger.info("Running pipeline (max_pages=%d)...", max_pages)`

## Data Pipeline Conventions

### dlt Sources
- Each API has separate static and temporal sources
- Static: Weekly runs, full data refresh (merge disposition)
- Temporal: Daily runs, snapshot data (append disposition)
- Share paginated results across resources to avoid duplicate API calls

### Naming Conventions
- Source files: lowercase with underscores (e.g., `tmdb.py`, `omdb.py`)
- Resource names: lowercase with underscores (e.g., `movie_catalogue`, `movie_popularity`)
- Table names: lowercase with underscores, schema-prefixed (e.g., `raw.movie_catalogue`)
- Primary keys: Use composite keys where appropriate (e.g., `["id", "scraped_at"]`)

### Rate Limiting
- Always implement rate limiting for API calls
- Use `time.sleep()` with appropriate delays
- Example: `REQUEST_DELAY = 0.25` for TMDB (~4 req/sec)

## dbt Conventions

### Model Organization
- `staging/`: Source-aligned staging models (stg_ prefix)
- `marts/`: Business-aligned mart models (mart_ prefix)
- Use `+materialized: table` for staging, `+materialized: table` for marts

### Schema Usage
- Staging models: `staging` schema
- Mart models: `marts` schema
- Source data: `raw` schema

### Model Configuration
- Use YAML files for model documentation and tests
- Include descriptions, column metadata, and tests in model YAML files

## Environment Variables

### Required Variables
```bash
# For ingestion pipelines
SOURCES__TMDB__API_KEY
SOURCES__OMDB__API_KEY
SOURCES__ANTHROPIC__API_KEY
DESTINATION__MOTHERDUCK__CREDENTIALS

# For dbt pipelines
MOTHERDUCK_PROD_TOKEN

# For MCP assistance
HM_ANALYTICS_DBT_PROJECT_DIR
HM_ANALYTICS_DBT_PATH
```

### Configuration Files
- `.dlt/config.toml`: Non-secret dlt configuration
- `.env`: Local environment variables (loaded via direnv)
- `.envrc`: direnv configuration

## Testing Guidelines

- Add tests for new functionality
- Use existing test patterns from the codebase
- For dbt models: Add tests in YAML files alongside models
- For Python code: Add unit tests in appropriate test directories

## Documentation

- Update README.md with significant changes
- Document new data sources in their respective files
- Include docstrings for all public functions and classes
- Use Google-style docstrings (matching existing code)

## MCP Server Configuration

The project uses three MCP servers:
1. **motherduck**: Remote server for MotherDuck database access
2. **dlt-workspace-mcp**: Local server for dlt workspace operations
3. **dbt**: Local server for dbt project operations

All are configured in `opencode.json` with appropriate environment variables.
