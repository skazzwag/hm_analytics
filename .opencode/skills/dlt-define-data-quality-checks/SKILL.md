---
name: dlt-define-data-quality-checks
description: 'dlt CLI/Python: Define ingestion checks for dlt extraction, schema, keys, completeness and incremental behavior. Use after discovering the source contract; do not implement dbt business tests here.'
---

# Define Data Quality Checks

> **Primary tool:** dlt CLI and Python library (dltHub-only features where explicitly noted).

Separate extractor fixtures, row/schema validation and destination load invariants. Specify failing examples, severity and behavior on invalid records. Use dlt schema_contract only for the intended schema policy; add pytest/queries for properties it does not check. Assert composite-key tuples, null semantics, cursor equality/late arrival and replay behavior explicitly. Do not collapse a multi-column key into one column or silently discard rows. Put code under ingestion/; propose cross-layer business checks to analytics-engineer. Never silently install/activate licensed dlthub.data_quality.
