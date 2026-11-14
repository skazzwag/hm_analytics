# Analysis notebooks: marimo + Altair

## Output contract

- Make substantive analysis reproducible in a marimo Python notebook under root `analysis/`; keep a concise text summary alongside it. **The entire workspace is Git-ignored** and is for personal investigation only, not production source or automatic CI input. Use Altair for all charts. A definition lookup alone need not create a notebook.
- Separate the question, provenance/Guide references, controls, data acquisition, validation, charts and conclusions into small reactive cells. Prefer one query result reused by several charts over repeated warehouse reads.
- Keep titles, units, grain, timezone, denominators, exclusions and observation time explicit. Do not present an unfinished draft as a completed analysis.

## Reactive code

Use canonical `@app.cell` structure, explicit cell dependencies and unique exported names. Underscore-prefixed temporary variables are cell-local. The generated `def _(...)` cell wrapper is an exception to the project's function-name/type/docstring rules; ordinary helper functions still follow them.

Display an Altair chart as a cell's final expression. Use `mo.ui.altair_chart(chart)` when selections need to be available to Python; read the resulting widget's `.value` in a DIFFERENT dependent cell. A plain Altair chart is valid when Python selection is unnecessary. Do not claim that only one particular variable name can render.

Use a manual form/run gate for warehouse work. Changing chart appearance or local selections must not silently re-run expensive warehouse queries. Avoid mutable global connections/caches that can leak data across sessions. Cache only approved aggregates with explicit freshness, environment and parameter keys.

## Access and privacy

Follow `data-access.md`: MCP for agent exploration; approved local snapshots by default; separately approved read-only notebook runtime for a live MotherDuck connection. Never assume MCP credentials are available in the notebook. Authentication is configured by the user outside code. No secrets in notebooks, HTML, SQL strings, metadata or stdout.

Filter and aggregate at source, then materialize a small result. The default chart-data budget is 5,000 rows, a project policy rather than a library limit. Fetch one extra row where useful to detect overflow and stop instead of silently truncating a result. A SQL LIMIT bounds returned rows, not necessarily bytes scanned or query cost. Larger datasets need an explicit plan. Never disable Altair's row limit as an automatic fix.

Do not export raw warehouse data, customer identifiers or sensitive tooltips by default. Exports can embed ALL rows supplied to a chart, including data hidden by a visible filter. A CSV transformer does not make data private. Keep real snapshots and exports in the ignored `analysis/` workspace; **do not commit notebooks, synthetic examples, data extracts or other artifacts from this directory**. To make a durable shared artifact, obtain explicit approval to move it into a separately agreed tracked location, review it for privacy and reproducibility, and use the engineering workflow. Treat local Git-ignored files as not backed up.

## Validation and execution

For an approved existing notebook session, load `marimo-pair` (official skill) to inspect kernel state and modify notebook code. A paired session **executes Python**; always obtain separate approval for execution and warehouse access. Prefer authenticated localhost sessions; never automatically use `--no-token` even if upstream documents that as a discovery shortcut. The pairing skill must not alter notebooks outside root ignored `analysis/`, install packages or export sensitive data without approval.


Use the project's approved locked environment, not `uvx` downloading a fresh marimo on every check. Run the local policy check and `marimo check`; distinguish these static checks from execution, source-data verification and visual inspection. Record missing dependencies as blocked. Do not install automatically.

Launch only when asked, bound to `127.0.0.1`, with marimo's authentication enabled. Do not use `--no-token` or expose `0.0.0.0` by default. Start in lazy/manual execution mode; separately approve real query execution and exports. Do not claim a server is running after only writing a launch command.

## Library integration

Default: approved DuckDB/MotherDuck SQL -> bounded pandas/Arrow result -> Altair -> marimo. Ibis and VegaFusion are optional, not required dependencies.

Do not copy legacy `vegafusion.runtime.set_connection(...)`, `vf.enable()` or `table://` examples into a modern environment. VegaFusion 2 removed its DuckDB SQL-connection layer; current relation support is not a guarantee that chart transformations execute in MotherDuck. `mo.ui.altair_chart` also uses marimo's own data transformer. Consult `marimo-build-notebook/references/connectors.md` before introducing another transformer or relying on direct relation support.

## Guide ownership

Read Guides; do not publish them from an analyst notebook. Return durable, evidence-backed candidates to analytics-engineer. Keep session-specific observations in the analysis, not automatically in shared warehouse context. The supplied README establishes transformation/guides/ as Git source, with CI-only publication; see .opencode/docs/warehouse-guides.md. Actual PR scripts still need inspection.
