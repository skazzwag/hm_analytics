---
name: dlt-toolkit-dispatch
description: 'dlt CLI/Python: Helps users figure out what they can build with dlt and which workflow to start. MUST use this skill when the user asks questions like ''what can you do'', ''how do I build a pipeline'', ''how do I make reports'', ''how do I deploy'', ''what are toolkits'', ''what''s available'', ''I''m new to dlt'', ''where do I start'', or seems confused about what to do next after initial setup. Also use when the user asks broad capability questions about data engineering with dlt. Do NOT use when the user has a specific task in progress like debugging a pipeline, validating data, or adding endpoints.'
---

# Route dlt and orchestration work to installed skills

> **Primary tool:** dlt CLI and Python library (dltHub-only features where explicitly noted).

Inspect the repository's `.opencode/skills/` and `AGENTS.md` for the active skills and owner. Do not query a dlt MCP or require dltHub AI toolkit discovery or installation. Use the available skills, local project code, and official documentation. Do not run code, install toolkits, or enable additional MCP servers merely to answer a capability question.

| Intent | Skill / owner |
|---|---|
| Find connector or source | `dlt-find-source` / data-engineer |
| REST API ingestion | `dlt-create-rest-api-pipeline` / data-engineer |
| SQL ingestion | `dlt-create-sql-database-pipeline` / data-engineer |
| Azure Blob/filesystem ingestion | `dlt-create-filesystem-pipeline` / data-engineer |
| Incremental and state handling | `dlt-add-incremental-loading`, `dlt-debug-pipeline` / data-engineer |
| Ingestion quality | `dlt-setup-data-quality` and matching ingestion-quality skill / data-engineer |
| Dagster orchestration | `dagster-repo-structure` / data-engineer |
| dbt transformation | one installed Altimate `dbt-*` skill + dbt standards / analytics-engineer |
| Investigation/notebooks | `motherduck-explore-data`, `marimo-build-notebook` / data-analyst |

Explain the proposed path and any missing local dependencies. Prefer the core `uv run dlt` CLI for approved diagnostic work. For Azure production runs, local dlt pipeline directories do not automatically contain the container's trace/state; use read-only Azure Blob metadata, isolated state sync when approved, and Azure CLI logs. Do not treat MotherDuck as the dlt state store.
