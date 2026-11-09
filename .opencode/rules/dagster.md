# Dagster

Project lives in `ingestion/`. Entry: `definitions.py` loads `ingestion/defs/`.

| Path | Role |
|------|------|
| `ingestion/defs/dbt/` | `dagster_dbt.DbtProjectComponent` → `transformation/` |
| `ingestion/defs/{github,hubspot,jira,sonarqube,partner_api}/` | Per-source dlt load components (`defs.yaml`, `loads.py`) |
| `ingestion/defs/schedules.py` | Warehouse chain: SQL → dbt → partner API |
| `ingestion/defs/microsoft_teams.py` | Alerting |
| `ingestion/dockerfiles/` | User-code and webserver images |

Warehouse chain job names include `coiote_ingestion_job`, `sql_ingestion_job`, `dbt_ops_job`, `dbt_job`, `dbt_partner_api_tests_job`, `partner_api_job`.

Local: `make serve` (Docker), `make dev` / `dg dev` (lightweight), `uv run dg check defs`. Tests: `ingestion/tests/`. Config: `.dagster_home/`.

Agents must not run dbt through Dagster jobs in this setup. Write defs and tell the user how to run them. Operating the orchestrator is a separate workflow that requires an explicit policy change, not a workaround for the direct-dbt prohibition.

Do not execute dbt through Dagster during agent work; eligible roles use only the approved dev runner. Production orchestration remains CI/operator-controlled.


Official `dagster-expert` is available on demand for `dg` CLI, assets, components, sensors and testing. `dagster-repo-structure` remains the project-specific source of naming and path conventions. `dg check defs` reads/imports project definitions; `dg launch` runs actual resources and may write storage, call APIs or invoke dbt. Do not launch pipeline runs without an approved isolated development identity, destination, dlt state and selected asset/job scope. Never bypass the dbt runner or production credential boundary through Dagster.

## External Dagster reference policy

The bundled `dagster-expert` is the complete official Dagster CLI and architecture skill, with upstream references. Dagster Plus MCP alternatives mentioned in those references **do not apply**: do not connect or invoke additional MCP services. Use `dg` for local CLI discovery/validation and `dg api` only when separately approved with narrowly scoped development credentials. Read-only commands may import and execute project code, so inspect context and obtain permission before running. No `dg launch`, asset materialization, backfill, Dagster Plus remote runs or secret retrieval without explicit approval and verified isolated development destinations and dlt state. Do not invoke dbt through Dagster.
