# dlt workflows

This repo already has pipelines under `ingestion/`. Prefer extending those over scaffolding a greenfield `dlt init` unless the user wants a new source. Place new extractors in the existing `ingestion/sources/` layout (see `.opencode/rules/repo-structure.md`).

Always: `uv run`, `--non-interactive` on dlt CLI, cwd = repo root. Use dlt CLI and repository skills; no dlt MCP is configured. Never read `*.secrets.toml`. Never print secrets. Use `dlt-setup-secrets` and tell the user to edit secret files.

## REST API

Start with `dlt-find-source`. Then `dlt-create-rest-api-pipeline` → `dlt-debug-pipeline` → `dlt-validate-data`. Harden with `dlt-adjust-endpoint`, incremental loading, `dlt-new-endpoint`. Existing API sources: `ingestion/sources/api/` (coiote, github, hubspot, jira, sonarqube).

## SQL database

Start with `dlt-find-source`. Then `dlt-create-sql-database-pipeline` → `dlt-debug-pipeline` → `dlt-validate-data`. Harden with `dlt-adjust-table`, `dlt-add-table`. Existing SQL schemas: `ingestion/sources/sql_schema/` (`fido1`, `fido_way`, `gis_service`, `relay`). Clean up throwaway explore scripts after the pipeline works.

## Filesystem

Start with `dlt-create-filesystem-pipeline`. Incremental: `dlt-add-incremental-loading`. Existing blob→Glacier: `ingestion/sources/blob_storage/`.

## Workspace

On a new session, check `uv`, the venv, and `uv run dlt --version`. Use only non-sensitive configuration metadata; secret-reading tools are denied. The user edits credentials. Do not write Python that opens secret files; use `dlt.secrets["key"]`.

## After ingest

Hand analysis to `data-analyst` (`motherduck-explore-data` / `marimo-build-notebook`). Hand dbt modeling to `analytics-engineer`. This warehouse uses dbt in `transformation/`, not a dlt CDM, unless the user explicitly asks for the annotate → ontology → CDM toolkit path.

## Diagnose Azure Blob ingestion using CLIs

This stack loads dlt data to Azure Blob Storage; MotherDuck reads downstream files. Do **not** claim that querying MotherDuck system tables retrieves dlt execution state. Use `uv run dlt pipeline --list-pipelines`, `uv run dlt pipeline <pipeline> info`, `trace`, `failed-jobs`, or `schema` for an existing local working directory. For a container-only pipeline, local state/trace may not exist. The filesystem destination can persist state and schemas to Azure Blob; any `pipeline sync` must be separately approved, use a scratch `--pipelines-dir`, and use a scoped read-only Azure identity. `sync` replaces *local* state; it does not recover container-local failed job packages or logs. Read Azure Container Apps logs for runtime failure and Azure Blob metadata for files actually loaded. Never run production backfills, remote reset/drop or privileged token reads as diagnostics.

See official dlt CLI and filesystem documentation: https://dlthub.com/docs/reference/command-line-interface and https://dlthub.com/docs/dlt-ecosystem/destinations/filesystem.
