"""Synthetic marimo/Altair acceptance notebook; no warehouse data or connections."""

import marimo

app = marimo.App(width="medium")


@app.cell
def _():
    import altair as alt
    import marimo as mo
    import pandas as pd
    return alt, mo, pd


@app.cell
def _(mo):
    mo.md("""
    # Synthetic Altair acceptance check

    These six rows are invented fixtures, not Fido/MotherDuck observations.
    Use this notebook to test rendering and chart selections before connecting
    a real data source. Metric: synthetic event count; grain: month and series.
    """)
    return


@app.cell
def _(pd):
    chart_data = pd.DataFrame({
        "period": pd.to_datetime([
            "2026-01-01", "2026-02-01", "2026-03-01",
            "2026-01-01", "2026-02-01", "2026-03-01",
        ]),
        "metric_value": [12, 18, 16, 8, 11, 14],
        "series": ["Fixture A"] * 3 + ["Fixture B"] * 3,
    })
    return (chart_data,)


@app.cell
def _(alt, chart_data, mo):
    _chart = (
        alt.Chart(chart_data)
        .mark_line(point=True)
        .encode(
            x=alt.X("period:T", title="Month (synthetic calendar date)"),
            y=alt.Y("metric_value:Q", title="Synthetic events", scale=alt.Scale(zero=True)),
            color=alt.Color("series:N", title="Fixture series"),
            tooltip=["period:T", "series:N", "metric_value:Q"],
        )
        .properties(title="Synthetic monthly events", height=320)
    )
    selected_chart = mo.ui.altair_chart(_chart)
    selected_chart
    return (selected_chart,)


@app.cell
def _(mo, selected_chart):
    mo.vstack([
        mo.md("## Local chart selection\nSelection happens on this tiny fixture, not in a warehouse."),
        mo.ui.table(selected_chart.value),
    ])
    return


if __name__ == "__main__":
    app.run()
