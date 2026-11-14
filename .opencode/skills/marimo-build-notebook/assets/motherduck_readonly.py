"""Guarded live-runtime template, not a configured production notebook.

User-provisioned read-only MotherDuck authorization is required. The local flag
and form prevent accidental execution but are not a security sandbox.
"""

import marimo

app = marimo.App(width="medium")


@app.cell
def _():
    from datetime import date, datetime, timezone
    import altair as alt
    import duckdb
    import marimo as mo
    return alt, date, datetime, duckdb, mo, timezone


@app.cell
def _(mo):
    runtime_scope_approved = False
    approved_database = "__REPLACE_WITH_DATABASE__"
    query_sql = """
    SELECT
        date_trunc('month', events.event_at) AS period,
        count(*) AS metric_value
    FROM __REPLACE_WITH_VERIFIED_RELATION__ AS events
    WHERE events.event_at >= ? AND events.event_at < ?
    GROUP BY 1
    ORDER BY 1
    LIMIT 5001
    """
    mo.md("""
    # Live MotherDuck analysis: blocked template

    Replace the database/relation/column placeholders and document the actual
    question, Guide references, grain, timezone and exclusions. Change the local
    approval flag only after real user approval of this runtime and query scope.
    The user configures read-only authentication outside this notebook. Do not
    paste a token here. MCP authentication is not inherited by Python.
    """)
    return approved_database, query_sql, runtime_scope_approved


@app.cell
def _(date, mo):
    query_controls = mo.ui.dictionary({
        "start": mo.ui.date(value=date(2026, 1, 1), label="Start (inclusive)"),
        "end": mo.ui.date(value=date(2026, 2, 1), label="End (exclusive)"),
    }).form(submit_button_label="Run approved read-only query")
    query_controls
    return (query_controls,)


@app.cell
def _(approved_database, datetime, duckdb, mo, query_controls, query_sql, runtime_scope_approved, timezone):
    mo.stop(not runtime_scope_approved, mo.md("Blocked: separate notebook-runtime approval is required."))
    mo.stop("__REPLACE_" in approved_database or "__REPLACE_" in query_sql, mo.md("Blocked: verify and replace the database, relation and column names."))
    mo.stop(query_controls.value is None, mo.md("Submit the form to execute the approved query."))
    _start = query_controls.value["start"]
    _end = query_controls.value["end"]
    mo.stop(_start is None or _end is None, mo.md("Choose both dates."))
    mo.stop(_start >= _end, mo.md("End must be later than start."))
    with duckdb.connect(f"md:{approved_database}") as _connection:
        warehouse_chart_data = _connection.execute(query_sql, [_start, _end]).fetchdf()
    observed_at = datetime.now(timezone.utc).isoformat()
    queried_parameters = f"{_start} <= event_at < {_end}"
    mo.stop(len(warehouse_chart_data) > 5000, mo.md("Blocked: more than 5,000 chart rows; revise aggregation or scope."))
    mo.stop(warehouse_chart_data.empty, mo.md("No rows for the submitted scope; do not infer absence of the phenomenon."))
    return observed_at, queried_parameters, warehouse_chart_data


@app.cell
def _(alt, mo, observed_at, queried_parameters, warehouse_chart_data):
    _chart = alt.Chart(warehouse_chart_data).mark_line(point=True).encode(
        x=alt.X("period:T", title="Month (verify source timezone)"),
        y=alt.Y("metric_value:Q", title="Verified event count", scale=alt.Scale(zero=True)),
        tooltip=["period:T", "metric_value:Q"],
    ).properties(title="Event count for the submitted period", height=320)
    warehouse_chart = mo.ui.altair_chart(_chart)
    mo.vstack([
        mo.md(f"Observed at `{observed_at}`. Submitted parameters: `{queried_parameters}`."),
        warehouse_chart,
    ])
    return (warehouse_chart,)


@app.cell
def _(mo, warehouse_chart):
    mo.ui.table(warehouse_chart.value)
    return


if __name__ == "__main__":
    app.run()
