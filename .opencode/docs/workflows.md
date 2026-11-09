# Workflow map

## Choose the path

**Lightweight personal investigation:** Ask a question or use `/explore` or `/notebook` directly with `data-analyst`. The custom default `product-owner` may delegate a bounded exploratory task immediately. Analyst files stay in fully Git-ignored root `analysis/`; no engineering plan, implementation approval or automatic reviewer pass merely to edit those local files. MotherDuck query approvals, live notebook execution/export approval and data-privacy rules still apply independently. Return a compact answer and optional evidence-backed Guide candidate; do not mutate tracked models/Guides. A read-only definition lookup may not need any notebook at all.

**Tracked engineering change:** Use `product-owner` to gather repository/Guide/catalog and official docs context, ask permission for read-only SQL if needed, define a bounded plan, obtain implementation approval, route specialists and independently review the change. This is also the path for *promoting* notebook work into a tracked deliverable. Stock Plan remains available; data-architect handles substantive design/ADRs.

## Engineering and data quality

Data-engineer owns ingestion/dlt quality and Dagster orchestration. Analytics-engineer owns dbt/transformation quality, Altimate deterministic SQL/column lineage and Git Guide edits. Analyst writes only root ignored `analysis/`. No agent has prod credentials or performs deployment. dbt runtime uses the disabled-by-default, approved dev-only runner; independent reviewer can request verification but cannot edit source.

## Verification

Reviewer reads the exact revision and separately requests approved dev runner/local checks where available. Fixes go to the original specialist, then stop; final revision is not automatically re-reviewed. Targeted recheck needs approval. Source editing, dev verification, production deployment and Guide publication are separate states. Review is for tracked engineering edits, not ordinary local investigation.

## Guides

Read the supplied README in docs/reference/. Use existing transformation/guides/ metadata/validator. Draft -> existing validation -> PR -> main CI -> observed publication. No local Guide publication or deletion. UUID write-back and first-sync inventory remain explicit operator requirements. Ignored analyst context-candidate files are not authoritative and cannot be CI input; analytics-engineer must review and copy verified durable definitions into canonical tracked Guides.

## Migration

Merge `.gitignore.snippet` into repository-root `.gitignore` (especially `/analysis/`); run `mkdir -p analysis` on fresh checkouts. Copy the new `.opencode/agents/product-owner.md` and **delete the obsolete `.opencode/agents/data-orchestrator.md` and `.opencode/agents/data-plan.md`** after checking for local edits. The even older `.opencode/agents/plan.md` override should also be absent to preserve stock Plan. Review REMOVALS.txt for earlier provisional Guide files. Move actual marimo notebooks to ignored root `analysis/` only after checking imports/paths; do not bulk-move dbt SQL analysis files. Do not overwrite your real repo README/Makefile/CI or canonical Guide files.

**General programming:** Switch to OpenCode's built-in `build` primary agent with Tab. `plan` is also available for read-only planning. Outside this project configuration, the normal OpenCode default is unaffected. Inside this repository both built-ins still see project instructions and shared permissions; they do not bypass the dev-only dbt boundary.

**Data ingestion diagnostics:** dlt skills plus `uv run dlt` CLI for local state/trace; Azure Blob filesystem metadata/state and Azure Container Apps logs require separate read-only scope and approvals. The only configured MCP is MotherDuck for downstream warehouse context.


## Specialist skill availability

All nine official specialist skills (seven Altimate dbt, `marimo-pair`, and the complete `dagster-expert`) are bundled under `.opencode/skills/`, with upstream reference files and project-specific approval policy. Run `python .opencode/tools/skills/install_official.py --status` to verify file presence; no installation or extra MCP is required. Skills never grant permission to run unapproved CLIs, access warehouse data, launch Dagster or execute a live notebook kernel. The only MCP is MotherDuck.
