# Reactive notebook patterns

## Contents

1. Cell structure
2. Data and visualizations
3. Query gates
4. Evidence and testing
5. Templates

## 1. Cell structure

Keep a normal marimo Python file with `import marimo`, `app = marimo.App(...)`, decorated cells and the `if __name__ == "__main__": app.run()` entrypoint. Let marimo maintain cell signatures and returns when possible. Each public name is defined in only one cell; names prefixed with `_` are local to that cell. The generated function name `_` is permitted here even though ordinary project functions use descriptive names.

```python
@app.cell
def _():
    import altair as alt
    import marimo as mo
    import pandas as pd
    return alt, mo, pd
```

Put imports needed by downstream cells in returns. Avoid hidden mutable state and long cells mixing authentication, query execution, plotting and commentary. Do not introduce a dlt pipeline when data already lives in a dbt model or approved file.

## 2. Data and visualizations

Keep separate query, validation, chart and interpretation cells. Do not silently remove nulls, outliers or duplicate keys. Explain any intentional exclusions or sampling in the notebook. Handle empty results, divide-by-zero and overflow before plotting.

A regular Altair object can be displayed as a cell's final expression. A chart is not required to have a particular variable name. For a Python-reactive selection:

```python
@app.cell
def _(alt, chart_data, mo):
    _chart = alt.Chart(chart_data).mark_bar().encode(
        x=alt.X("category:N", sort="-y", title="Category"),
        y=alt.Y("metric_value:Q", title="Verified metric (units)"),
        tooltip=["category:N", "metric_value:Q"],
    ).properties(title="A question-specific title")
    selected_chart = mo.ui.altair_chart(_chart)
    selected_chart
    return (selected_chart,)


@app.cell
def _(mo, selected_chart):
    mo.ui.table(selected_chart.value)
    return
```

Read `selected_chart.value` in a DIFFERENT cell from widget creation. The frontend selection filters the chart data; it is not proof that a query was pushed down to MotherDuck. Do not connect chart selection directly to an expensive warehouse re-query without an explicit submitted control.

Use typed encodings and readable labels. Prefer Altair's normal styling or an existing project theme. Use titles and tooltips to identify units, aggregation and time semantics. Avoid default sum/average choices that conflict with Guide definitions. A bar chart's zero baseline should not be removed simply to exaggerate a difference.

## 3. Query gates

A live notebook must stop before creating a MotherDuck connection unless the requested runtime route is approved AND the form has been submitted. A Boolean flag is a usability gate, not a permission system. Use a read-only identity and inspect the actual queries.

Use a form to collect multiple parameters before one execution. Keep the queried parameters and observation time with the resulting data so changed-but-unsubmitted controls cannot mislabel old results. Parameterize values with the DuckDB driver rather than interpolating user text into SQL. Identifiers cannot be bound as values: choose verified identifiers from code or an explicit allowlist.

A default chart-data budget of 5,000 rows is project policy. Fetch 5,001 rows to detect overflow, then stop or redesign; do not lop off the final row and present the rest as complete. LIMIT only restricts results, not necessarily scan cost. Aggregation/filtering happens in SQL before `.fetchdf()` or Arrow conversion. Do not accumulate connection objects in caches or reuse a closed connection through a lazy relation.

## 4. Evidence and testing

Include: question, source environment/relations, actual Guide IDs/versions when available, model/source revision when known, metric grain, units, timezone, filters, observation timestamp and limitations. A timestamp is not itself proof of freshness; distinguish query time from the latest source-data time.

Validate separately: syntax/policy, marimo graph/lint, installed-library compatibility, actual data execution, chart rendering, interaction and semantic correctness. A static pass is not a warehouse validation. `mo.md` explanation cells are valid; do not remove conclusions based on the old claim that every footer is an empty-cell error.

For runtime acceptance, test no data, null values, overflow and selections in the installed marimo version. Retain token authentication on loopback launches. Export only after permission and inspect whether raw/hidden chart data is included.

## 5. Templates

- `../assets/synthetic_demo.py`: tiny, self-contained synthetic data for installation/interaction acceptance; no warehouse access.
- `../assets/approved_snapshot.py`: approved `.data/chart_data.csv`, bounded load, explicit no-data/overflow handling. Required columns: `period`, `metric_value`, `series`. The author must update the generic labels/semantics to the actual question.
- `../assets/motherduck_readonly.py`: live runtime skeleton; deliberately stops until scope approval, verified database/relation/column edits and form submission. It is not ready to query the user's warehouse as delivered.

Copy only the appropriate template into `analysis/` and customize it; do not execute templates merely to inspect them. Do not infer production semantics from these generic examples.
