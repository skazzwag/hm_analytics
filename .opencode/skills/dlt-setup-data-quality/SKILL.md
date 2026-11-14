---
name: dlt-setup-data-quality
description: 'dlt CLI/Python: Scope ingestion data-quality work and inspect dlt contracts, fixture tests, pipeline state and load guarantees. Use for new/changed sources or ingestion defects. Data-engineer owns implementation.'
---

# Setup Data Quality

> **Primary tool:** dlt CLI and Python library (dltHub-only features where explicitly noted).

Inspect the actual source/resource, merge/incremental configuration, destination and existing tests. Establish grain, source completeness, required fields, cursor semantics and rejection policy. Read data-quality.md. Identify baseline fixtures and isolated test state. Use core dlt contracts/Pydantic/pytest by default; do not demand a dltHub licence. Inspect installed versions before suggesting optional commercial APIs. Pass a short contract/evidence brief to dlt-define-data-quality-checks; do not load prod data or change pipeline state during discovery.
