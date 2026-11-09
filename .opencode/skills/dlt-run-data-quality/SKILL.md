---
name: dlt-run-data-quality
description: 'dlt CLI/Python: Run approved ingestion quality tests with isolated dlt state and non-production destinations. Use for fixture checks or explicitly scoped development load verification.'
---

# Run Data Quality

> **Primary tool:** dlt CLI and Python library (dltHub-only features where explicitly noted).

Review tests and imported fixtures for external side effects. Run approved fixture-only pytest first. Before any real pipeline extraction/load, require non-production source/destination credentials, unique pipeline name/state directory, resource selection, row/time bounds and cost approval. A different pipeline name alone does not isolate a shared production destination. Do not reset prod state, invoke warehouse chain jobs, bypass dbt policy or run backfills. Record exact commands, fixture/source revision and counts/rejects. Missing safe runtime is blocked, not passed.
