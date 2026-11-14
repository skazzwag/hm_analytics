# Analyst notebooks: setup and acceptance

This update strengthens the EXISTING `marimo-build-notebook` and `motherduck-explore-data` skills. It adds no MCP server, second agent runtime or automatic startup process. The main analyst prompt carries the defaults; detailed notebook/connector guidance is loaded on demand.

## 1. Merge the notebook changes and ignore the personal workspace

Merge `.gitignore.snippet` into the **real repository-root `.gitignore`**, including the anchored `/analysis/` rule. This ignores the *entire* workspace, not only data extracts. To verify in your own repository after merging:

```bash
git check-ignore analysis/notebooks/example.py analysis/context-candidates/example.md
```

Run `mkdir -p analysis` on each fresh checkout (Git does not restore ignored folders). The archive includes a convenience `analysis/README.md` for local use; it will also be ignored. No notebooks in `analysis/` should be staged/committed. These local files are not backed up by Git. A notebook you intentionally want to share needs a separate reviewed promotion outside `analysis/`.

**If you already tracked analyst files before adding the ignore rule:** check `git ls-files -- analysis/`. `.gitignore` does not untrack existing files. Review those files, then explicitly remove them only from the Git index, not your local disk, using `git rm -r --cached -- analysis/`, and commit that change. Do not automatically rewrite Git history; if sensitive data was committed, handle exposure and rotation separately.

Guide source is transformation/guides/ under the supplied README; existing CI alone publishes. See .opencode/docs/warehouse-guides.md.

Data-analyst's edit permission remains restricted to `analysis/**`. It cannot change dependencies or canonical Guide files. Global bash approvals, the analyst dbt prohibition and Altimate non-agent workflow are preserved; only eligible engineering/reviewer roles may request the opt-in dev runner.

## 2. Use the existing project environment

Inspect the real `pyproject.toml` and lockfile first. Reuse the repository's current dependency-group conventions. The examples need marimo, Altair, DuckDB and pandas; marimo's SQL extra adds its SQL-editor dependencies. A possible new group, ONLY after your approval and when the repo has no preferred equivalent:

```bash
uv add --group analysis 'marimo[sql]' altair duckdb pandas
uv sync --group analysis
```

These commands modify/sync your environment and are for the user or approved owner, not automatic analyst behavior. Commit reviewed manifest/lockfile changes. No exact package versions are asserted by this overlay because your repo's dependency files were not accessible. Do not add VegaFusion or Ibis merely to obtain Altair charts.

## 3. Test without warehouse access first

```bash
mkdir -p analysis
cp .opencode/skills/marimo-build-notebook/assets/synthetic_demo.py analysis/notebook_smoke.py

uv run --group analysis --frozen python .opencode/tools/notebooks/check.py analysis/notebook_smoke.py
uv run --group analysis --frozen marimo check analysis/notebook_smoke.py
```

After authorizing a local server launch:

```bash
uv run --group analysis --frozen marimo edit analysis/notebook_smoke.py --host 127.0.0.1 --headless
```

Open the local URL printed by marimo. Keep its authentication token private. Confirm that both synthetic series render, chart selection updates the downstream table, and no warehouse connection occurs. Close the server when done. Do not export the demo as if it were a warehouse result.

Use the group name actually chosen in step 2; omit/change `--group analysis` when reusing another environment. Static checks do not require executing the notebook. Do not say rendering was tested until you have seen it in your installed version.

## 4. Choose real-data mode deliberately

**Approved snapshot:** copy `approved_snapshot.py`, customize question/semantics, and place only an approved aggregate extract at its `.data/chart_data.csv` path. Required columns are documented in the template; adapt them to the actual question. Keep the query, scope, snapshot hash when available, source-data freshness and actual Guide references in the analysis plan. Do not manufacture a CSV from a truncated MCP response.

**Refreshable live notebook:** copy `motherduck_readonly.py`. Replace its verified database/relation/column placeholders, inspect the SQL and permissions, and obtain separate runtime approval. The user configures authentication with a read-only MotherDuck identity outside notebook source/chat. Leave the gate closed until the scope is approved. Submit the form to run; changing chart selections should not requery the warehouse.

MCP remains the agent's exploration route. A declined query cannot be executed through the notebook instead. A direct runtime connection also does not automatically fetch Guides: their selected, actual references/semantics must be recorded during analysis.

## 5. Analyst acceptance prompt

> Use the data-analyst role. Read the applicable notebook skills. Create a marimo notebook with Altair charts under analysis for the approved question, using an approved bounded snapshot. Include actual source/Guide provenance and material limitations. Do not execute dbt, install dependencies, launch a server, connect directly to MotherDuck or publish any Guide. Report static validation separately from runtime and visual testing. Return durable context candidates to analytics-engineer.

For approved live runtime, explicitly state that additional scope; do not infer it from a request for charts.

## 6. Why not the old DuckDB connector recipe?

VegaFusion 2 removed the DuckDB SQL-connection layer and `vf.enable()` even though old integration pages remain available. DuckDB relations can be supplied as inline data in supported versions, but that does not establish MotherDuck execution of chart transforms. The default here is SQL aggregation -> bounded dataframe -> Altair -> marimo. `mo.ui.altair_chart` supplies Python-reactive selections and its own data transformer. See the skill's `references/connectors.md` and `references/sources.md` for the distinction.

## Validation limits

The supplied checker is dependency-free AST/policy validation, not a complete marimo linter, data verifier, SQL sandbox or secret scanner. The preceding notebook package could not install its runtime dependencies because of package-network DNS failure. This update does not establish runtime installation or rendering compatibility either. No live warehouse queries, notebook rendering or Guide operations were tested here. Run the checks above in your own locked environment before relying on a real notebook.


## Interactive notebook pairing

The complete official `marimo-pair` skill is already bundled under `.opencode/skills/marimo-pair/`, including its reference pages and execution/discovery scripts; **do not reinstall it**. It requires `bash`, `curl`, `jq` and a running authenticated marimo session. The analyst may use it **only with explicit execution approval** in root ignored `analysis/`; generated notebooks do not require a live kernel. Do not launch `--no-token` or expose network listeners for convenience. See `.opencode/docs/setup-official-skills.md`.
