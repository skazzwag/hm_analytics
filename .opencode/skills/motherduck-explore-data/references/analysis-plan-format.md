# Analysis plan checklist

This is a lightweight handoff between `motherduck-explore-data` and `marimo-build-notebook`, not a mechanically parsed format. Adapt existing repo conventions; keep the information below. Store under `analysis/<slug>_analysis_plan.md`.

## Question and status

Question, intended audience, scope, requested outputs, and status: planned / investigated / blocked / executed. State which notebooks or queries were actually run. Distinguish live observations from hypotheses and synthetic fixtures.

## Evidence and semantics

- Actual warehouse environment and fully qualified relations, or approved local file provenance.
- Relevant Guide IDs and versions, plus source/model revision when known; do not fabricate missing values.
- Grain, metric definitions, units, timezone, date range, exclusions, denominators and join cardinality.
- Observation timestamp, query identifiers when available, evidence paths, unresolved conflicts and known limitations.

## Runtime/data mode

Choose `approved-snapshot`, `approved-local-duckdb`, or `live-motherduck-pending-approval` / `live-motherduck-approved`. Record snapshot freshness/hash when available and the exact approved live query scope. Never record tokens. MCP authentication is not runtime authentication. A receipt is not proof of consent: the approval must actually exist.

## Findings and questions

Record each question with observed answer or blocker, minimal supporting aggregates and caveats. Do not paste broad result dumps. Use separate context candidates for durable Guide knowledge and keep canonical publication with analytics-engineer.

## Chart specifications

For each chart record: question, chart type, SQL/parameters, exact output columns/types, grain, row budget, overflow policy, sampling (if any), Altair code, labels/tooltips, selections and no-data behavior. Use `sql` and `python` fenced blocks. Explicitly label unexecuted SQL.

Example with synthetic/placeholder identifiers only:

```sql
SELECT
    date_trunc('month', event_at) AS period,
    count(*) AS metric_value
FROM __REPLACE_WITH_VERIFIED_RELATION__ AS events
WHERE events.event_at >= ? AND events.event_at < ?
GROUP BY 1
ORDER BY 1
LIMIT 5001
```

```python
alt.Chart(chart_data).mark_line(point=True).encode(
    x=alt.X("period:T", title="Month (verified timezone)"),
    y=alt.Y("metric_value:Q", title="Events"),
    tooltip=[alt.Tooltip("period:T", title="Month"), alt.Tooltip("metric_value:Q", title="Events")],
).properties(title="Verified event count by month")
```

`LIMIT 5001` is overflow detection for a 5,000-row chart budget, not permission to silently drop the final row. Replace placeholder names and verify the definition before execution. LIMIT is not a query-cost guarantee.

## Validation and next action

Record separately: policy check, `marimo check`, runtime query test, chart rendering/selection test, semantic review and data-export approval. Values are passed / failed / not run with reason; do not collapse them into an unexplained green status.
