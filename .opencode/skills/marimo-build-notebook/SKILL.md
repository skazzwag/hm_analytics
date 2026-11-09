---
name: marimo-build-notebook
description: 'marimo + Altair: Create, update and statically validate reproducible marimo Python notebooks with Altair charts for MotherDuck, DuckDB and approved local data. Use for substantive analysis, reports, dashboards, visualization requests or an existing analysis plan. Includes reactive cell patterns, bounded data, credential-safe runtime options and evidence handoff; not pipeline or dbt execution.'
---

# Build a marimo + Altair analysis notebook

> **Primary tool:** marimo Python notebooks and CLI, with Altair for charts.

Use marimo `.py` notebooks and Altair for every visualization. Keep the role instruction short; load only the references needed below. Follow repository permissions and the approved task scope over generic examples.

## 1. Establish the artifact and evidence

Read the specified analysis plan, existing notebook and relevant Guide/catalog evidence. An analysis plan is helpful but not mandatory: create a compact one from the known task when needed. Do not require a dlt pipeline for an ordinary warehouse question. Do not ask again whether the user wants a notebook.

Write under root `analysis/` in this project; the entire directory is intentionally Git-ignored, so never stage or commit notebooks or data snapshots. Keep valuable local work backed up through approved user-managed storage; promotion to tracked material requires a separately approved engineering change. Keep the question, actual sources, Guide IDs/versions, observation time, grain, units, timezone, parameters, exclusions, query status and limitations together. Mark hypotheses, synthetic samples and unexecuted queries explicitly. Do not invent results or business definitions. Preserve useful existing work rather than regenerating a whole notebook blindly.

## 2. Choose the data route

Read `references/connectors.md` only when selecting or changing data access.

- **Default:** approved bounded aggregate snapshot -> pandas/Arrow -> Altair -> marimo. Do not reconstruct a full dataset from a truncated MCP response.
- **Local data:** approved DuckDB processing of local files; no implicit upload.
- **Refreshable MotherDuck notebook:** explicit user-approved runtime connection via DuckDB, user-provisioned read-only authentication, approved query scope and manual execution gate. MCP exploration authorization alone is not enough.

Use MotherDuck MCP for the agent's actual warehouse discovery and exploratory queries. Never fall back to another route after a denial. Do not automatically add dlt, Ibis, VegaFusion or a marimo MCP service.

## 3. Assemble reactive cells

Read `references/notebook-patterns.md`; use the synthetic, snapshot or live-runtime templates in `assets/` as appropriate. The live template deliberately blocks until its placeholder SQL is replaced and execution is explicitly requested.

Separate imports, context, controls, data acquisition, validation, charts, selections and conclusions. Export each shared variable from one cell only. Display the chart/widget as the cell's final expression; read a widget's `.value` in a separate downstream cell. Use `mo.ui.altair_chart` when Python needs selections, not simply because every chart must be interactive.

Keep filters and aggregation in SQL, then materialize only necessary columns. Enforce the project's 5,000-row default chart budget, stop on overflow and show no-data states. Larger results need a revised plan, not automatic `disable_max_rows`. Avoid reactive re-queries on every slider or chart click; use a submitted form/manual gate and clearly display the queried parameters.

Use explicit Altair types (`:T`, `:Q`, `:N`, `:O`), informative titles/axis labels, meaningful tooltips and deliberate sorting. Reuse the project's theme if present; otherwise keep Altair's defaults. Explain denominators and null handling. Do not quietly drop anomalous rows. Keep raw identifiers out of tooltips/exports.

## 4. Validate without claiming execution

Inspect the project's existing environment/lockfile. Do not install packages without approval, edit dependency manifests from the analyst role, or use `uvx` to fetch an unpinned tool each time.

For the documented optional `analysis` dependency group, after user setup:

```bash
uv run --group analysis --frozen python .opencode/tools/notebooks/check.py analysis/example.py
uv run --group analysis --frozen marimo check analysis/example.py
```

Adapt the group flag to the real project; it is not assumed to exist. The custom check is a small AST policy check, NOT a marimo runtime, SQL validator or security sandbox. `marimo check` is also not evidence that warehouse queries succeeded. Report each check as passed, failed or not run with its actual reason.

A later separately approved runtime test must verify import compatibility, chart rendering, reactive selections if used, no-data/overflow handling, dates/timezones and actual query provenance. Do not call data correct solely because the notebook renders.

## 5. Launch/export only when authorized

After explicit launch approval, use the project's installed marimo, bind to loopback and retain authentication. Prefer lazy execution while inspecting new notebooks:

```bash
uv run --group analysis --frozen marimo edit analysis/example.py --host 127.0.0.1 --headless
```

Configure lazy execution in marimo before running a live data cell; the supplied live template also has a closed gate. Do not add `--no-token`. A server launch is not blanket authorization for new queries, uploads, app publication or HTML export. Exports may contain the full chart data, not only visible points.

## 6. Return the result and context candidates

Return notebook/plan paths, completed analysis, precise lint/runtime/visual-inspection status, limitations and a reproducible user command. Send durable discoveries with source evidence to analytics-engineer via the planner. Do not edit/publish canonical Guides or make up their version format. Follow the supplied README and .opencode/docs/warehouse-guides.md; do not create a competing Guide layout.

Reference provenance and version caveats: `references/sources.md`. The templates are examples, not statements about the user's warehouse.
