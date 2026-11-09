---
name: transformation-quality
description: Design and verify dbt Core transformation data tests and unit fixtures. Use for model grain, joins, nulls, keys, time boundaries, reconciliation and regression checks. Analytics-engineer authors; reviewer verifies.
---

# Transformation quality

> **Primary tool:** dbt Core — data tests and unit fixtures via the approved dev runner.

Read data-quality.md, dbt-standards.md and dbt-execution.md under .opencode/rules/.
Establish the intended grain, business rule, valid exclusions and observed data window. Distinguish source/load guarantees from dbt outputs. Add data_tests for keys/nulls/relationships/accepted values and singular SQL assertions for join amplification/reconciliation. Use installed-version-supported dbt unit tests for derived logic with boundary/null/duplicate fixtures. Do not introduce an external DQ service by default.
Preserve composite keys and explicit tolerances. Test changes in timezone, late arrival, incremental behavior and historical exclusions; do not encode a guessed business definition just because current SQL behaves that way.
Inspect custom macros/hooks, database routing and Python models before any runtime. Test/build/compile are not security classifications. Use only the user-enabled dev runner, normal per-command approvals and a bounded selection. Never invoke raw dbt, MCP or altimate-dbt. In reviewer mode no source edits; use reviewer actor/session and test exact revision. If safe runtime is absent, return source tests prepared and runtime blocked.
Compare results to the acceptance criteria, including counts/reconciliation where approved. Record target/schema, selection, source digest and artifacts. Use Altimate as separate static SQL/column-lineage evidence, not a substitute for these tests. Check Guide impact; analytics-engineer updates canonical Git files only. Return actual execution statuses and remaining limitations.
