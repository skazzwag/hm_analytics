---
name: dagster-repo-structure
description: 'Dagster + dg CLI: Change Dagster defs, jobs and schedules.'
---

# Dagster

> **Primary tool:** Dagster definitions and dg CLI (development-only execution when approved).

Read `.opencode/rules/dagster.md`.

## Checklist

1. New dlt loads get a folder under `ingestion/defs/` with `defs.yaml` and `loads.py`, matching existing sources. The extractor itself belongs under `ingestion/sources/api/<name>/` (or `sql_schema/` / `blob_storage/` / `database/`). Read `.opencode/rules/repo-structure.md`.
2. Wire the source in `ingestion/sources/` and `ingestion/glossary.py` / runners if the load is SQL or blob.
3. Local check the user can run: `uv run dg check defs`. Docker: `make serve`. Lightweight: `make dev`.
4. Do not run dbt through Dagster in this setup; eligible roles use the dev-only runner. Orchestrator execution needs a separate reviewed operational policy.
5. Never put secrets in defs. Inherit env.

Do not execute dbt through Dagster during agent work; eligible roles use only the approved dev runner. Production orchestration remains CI/operator-controlled.
