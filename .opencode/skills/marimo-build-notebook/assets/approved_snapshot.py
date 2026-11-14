"""Template for a user-approved aggregate CSV; no warehouse connection."""

import marimo

app = marimo.App(width="medium")


@app.cell
def _():
    from pathlib import Path
    import altair as alt
    import marimo as mo
    import pandas as pd
    return Path, alt, mo, pd


@app.cell
def _(Path, mo):
    snapshot_path = Path(__file__).resolve().parent / ".data" / "chart_data.csv"
    mo.md("""
    # Approved aggregate snapshot

    **Template:** replace this text with the actual question, source, Guide
    references, grain, units, timezone, filters, source-data freshness and export
    observation time. A local file is not proof that the warehouse is current.
    Required columns: `period`, `metric_value`, `series`.
    Keep real data in the ignored `.data` directory; no automatic downloads.
    """)
    return (snapshot_path,)


@app.cell
def _(mo, pd, snapshot_path):
    mo.stop(not snapshot_path.is_file(), mo.md("Blocked: supply the approved aggregate CSV."))
    snapshot_data = pd.read_csv(
        snapshot_path,
        usecols=["period", "metric_value", "series"],
        nrows=5001,
    )
    mo.stop(len(snapshot_data) > 5000, mo.md("Blocked: chart budget exceeded; aggregate further or approve a larger plan."))
    mo.stop(snapshot_data.empty, mo.md("No rows: verify scope and exclusions before interpreting this result."))
    mo.stop(snapshot_data.isna().any().any(), mo.md("Blocked: nulls need an explicit analytical handling rule."))
    snapshot_data["period"] = pd.to_datetime(snapshot_data["period"], errors="raise")
    snapshot_data["metric_value"] = pd.to_numeric(snapshot_data["metric_value"], errors="raise")
    return (snapshot_data,)


@app.cell
def _(alt, mo, snapshot_data):
    _chart = alt.Chart(snapshot_data).mark_line(point=True).encode(
        x=alt.X("period:T", title="Period (verify timezone)"),
        y=alt.Y("metric_value:Q", title="Metric (replace with verified units)"),
        color=alt.Color("series:N", title="Series"),
        tooltip=["period:T", "series:N", "metric_value:Q"],
    ).properties(title="Approved snapshot: replace with the analytical question", height=320)
    snapshot_chart = mo.ui.altair_chart(_chart)
    snapshot_chart
    return (snapshot_chart,)


@app.cell
def _(mo, snapshot_chart):
    mo.ui.table(snapshot_chart.value)
    return


if __name__ == "__main__":
    app.run()
