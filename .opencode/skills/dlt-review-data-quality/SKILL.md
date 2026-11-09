---
name: dlt-review-data-quality
description: 'dlt CLI/Python: Assess ingestion quality contracts, checks and observed load evidence independently. Use when reviewing dlt changes, test failures or source-to-dbt handoffs.'
---

# Review Data Quality

> **Primary tool:** dlt CLI and Python library (dltHub-only features where explicitly noted).

Inspect source grain, keys, schema/reject policies and test evidence. Check pagination completeness, failed loads, incremental boundaries and idempotency. Composite-key assertions must match their intended grain. Do not infer correctness from dlt hints or a single sample. Distinguish declared checks, executed checks and production observations. Reviewer may request fixture tests only after examining their side effects; never edit code or publish Guides. Hand transformation-level failures to analytics-engineer and report unresolved source contracts.
