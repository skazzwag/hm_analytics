# Fido data platform

Stack: dlt ingestion, dbt Core, DuckDB/MotherDuck, Dagster, Partner API reverse ETL. Existing repository descriptions are context, not proof of current warehouse semantics.

## Ownership
| Area | Paths | Owner |
|---|---|---|
| Ingestion, ingestion DQ, Dagster, reverse ETL, CI | ingestion/, partner_api/, .github/ | data-engineer |
| dbt, transformation DQ, deterministic SQL/column lineage | transformation/ | analytics-engineer |
| Canonical Guide content/metadata | transformation/guides/ | analytics-engineer |
| Guide deploy scripts / workflow | transformation/guides/*.sh, .github/workflows/ | data-engineer, explicit task only |
| Personal exploratory marimo/Altair workspace (entire directory Git-ignored) | root analysis/ | data-analyst |
| ADRs and cross-cutting design | documentation/ | data-architect |
| Independent source review + approved dev verification | current revision and isolated evidence | reviewer |

No new top-level pipelines/ tree. Root `analysis/` is a **fully Git-ignored personal workspace**, not a tracked product or dbt's `transformation/analysis/` SQL folder. No agent stages, commits or force-adds its contents. `.analysis/` separately holds generated engineering evidence. Git ignore is not a data-security control or backup.

## Permission boundaries
- `product-owner` is this repository's default primary agent. Keep OpenCode's built-in **Build** and **Plan** agents (switch with Tab); the project's `AGENTS.md` and permission controls continue to apply while using Build inside this repository. Keep `data-architect` separate. Product-owner coordinates but cannot approve work on the user's behalf. Route bounded **investigations** straight to data-analyst in ignored `analysis/` without a formal plan/review loop. Tracked engineering changes need a plan, implementation approval, independent review and truthful post-fix status. Query/runtime/export approvals apply in either path.
- Production credentials exist only in protected CI. The user provisions a separate dev identity with writes limited to its own dev databases and read-only approved prod shares. Different tokens for the same prod identity do not provide this separation.
- Direct dbt, dbt MCP, altimate-dbt and indirect orchestration/Python execution are denied. Analytics-engineer/reviewer may request `python .opencode/tools/dbt/run.py ...` only after the user verifies and enables the dev boundary. A wrapper is not a security sandbox. Never self-enable policy or retrieve prod secrets.
- Altimate remains an on-demand deterministic dependency, not a second agent. Missing native compatibility/artifacts means inconclusive, never invented lineage.
- MotherDuck is the only configured MCP. Use skills plus approved CLIs for dlt/Dagster/dbt/Altimate; do not add other MCP services. Ingestion state is in local dlt working directories or Azure Blob filesystem destination, not MotherDuck system tables. For Azure Container Apps execution use approved Azure CLI logs.
- Before warehouse SQL read relevant Guides and confirm live catalog objects. MCP read queries need approval; metadata can be read. No MCP warehouse or Guide writes. Separate approved notebook runtime and dev dbt runner are narrow exceptions, not alternate routes for denied actions.
- Guides are Git-authored under transformation/guides/. Existing PR validation and main-branch CI own publication and managed deletion. No agent publishes, deletes, changes remote Guide access, runs guides-push or sync.sh. Never invent Guide UUIDs or alter the supplied source/version convention.
- No force push, production deployment, secret reads or broad credential access. Read restrictions and shell patterns are not OS isolation. Do not use build/general/another agent to bypass these rules.

## Development conventions
Python: NumPy docstrings and type hints, typed collections, functions over classes, `uv` and pytest; no leading `_` on ordinary functions. Canonical generated marimo cell wrappers are excepted; read full Python rules before editing Python.

SQL: 4 spaces; YAML: 2 spaces. No one-letter aliases, no `USING`, qualify join columns, last CTE `final`. No `SELECT *` except staging/mart copies. Model YAML owns column docs and `data_tests:`; `datadictionary.yml` is not canonical.

Layers: `0_sources` YAML -> `1_staging` (`stg_{source}__{entity}`) -> `2_intermediate` (`int_`) -> `3_domain` (`dmn_`) -> `4_presentation` (`prs_`) -> `5_activation` (`act_`) -> `6_access`. Presentation is the reuse layer; activation does not repeat joins.

## Workflow and context
Choose the least-heavy path: investigations / marimo scratch work -> `data-analyst` -> concise findings (no routine engineering plan/reviewer); tracked engineering work -> `product-owner` -> approved plan -> bounded specialists -> reviewer -> required fixes -> stop. Do not auto-review again. Report whether FINAL source was verified; targeted follow-up needs approval. Promotion from ignored analysis to tracked work explicitly enters the engineering path.
Record source revision/digest, dataset/target, Guide UUID/external_id where available, evidence paths and blockers. Keep source prepared, static checked, dev-runtime verified, final revision reviewed, deployed and Guide published as separate statuses. Dev success is not prod deployment.
After modeling/DQ work, analytics-engineer checks Guide impact or states no durable context change. Other roles propose evidence-backed changes. Preserve the source README's root topic, share URL references, committed IDs and Git SHA external_id; do not introduce per-Guide review.json/evidence.md or private publication defaults.

## Progressive context
Read only applicable files under .opencode/rules/: python-style, sql-style, dbt-standards, repo-structure, dlt-workflows, dagster, data-quality, data-access, dbt-execution, altimate-analysis, warehouse-guides, context-handoff, notebooks.
For dbt, read `.opencode/rules/dbt-standards.md` and load one relevant `dbt-*` Altimate skill; preserve the project-specific layers, macros, tests and styles in the rule file. Use ingestion quality skills in data-engineer, transformation-quality in analytics-engineer, and motherduck-explore-data/marimo-build-notebook in data-analyst. Subagents share evidence pointers, not full catalogs/transcripts. Use marimo for substantive analysis and Altair for every chart with the duckdb python API as the data wrangling tool.

The seven Altimate dbt skills, marimo-pair and the **complete** Dagster `dagster-expert` (173 supporting references) are bundled in `.opencode/skills/`. `dagster-repo-structure` remains the project-specific guidance. Do not use Dagster MCP mentioned by generic upstream documents; MotherDuck is the only MCP, and execution requires the documented approvals. These specialist skills are loaded only when relevant. Skills are tool instructions, not permission to execute; all production/dbt/notebook/Guide safety restrictions apply. Use `python .opencode/tools/skills/install_official.py --status` to verify availability.
