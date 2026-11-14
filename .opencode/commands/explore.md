---
description: Investigate data and produce a marimo notebook with Altair charts and an evidence-backed summary.
agent: data-analyst
---

Investigate: $ARGUMENTS

Load `motherduck-explore-data`, then `marimo-build-notebook` for substantive analysis. Use marimo `.py` notebooks and Altair for every chart. Do not ask again whether I prefer text or notebooks. Write only to root `analysis/` (entire directory is Git-ignored personal scratch). This is the lightweight investigation path: no engineering plan or code review for local notebook/plan edits. Do not stage/commit these files or edit ingestion/dbt models; use an approved engineering change to promote work.

Retrieve relevant Guides and verify catalog names before approved MotherDuck MCP queries. Use an approved bounded snapshot by default; a live notebook connection needs separate approval under `data-access.md`. Report unexecuted queries or missing dependencies honestly. Return durable Guide candidates to analytics-engineer, without publishing them.
