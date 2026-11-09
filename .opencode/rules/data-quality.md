# Data quality by pipeline layer
Data-engineer owns ingestion quality in ingestion/; analytics-engineer owns transformation quality in transformation/. Reviewer independently assesses evidence from both. Analyst investigations may reveal candidates, not silently change pipeline acceptance rules.

## Ingestion: dlt + pytest by default
Test extractors against representative fixtures, pagination/end conditions, required fields/types, cursor boundaries/timezone, merge keys, repeated-load idempotency and failed/rejected records. Configure dlt schema contracts intentionally: evolve/freeze/discard modes have different outcomes. Pydantic validation is optional when useful. Primary-key/merge hints do not establish all uniqueness/completeness assertions.
State the intended grain. For composite keys assert the entire tuple and null policy; never substitute uniqueness of the first column. Reject/quarantine/discard policies need explicit business acceptance and observable counts.
Isolate pipeline name, working/state directory and destination for tests. Core dlt testing does not require buying dltHub DQ. Existing licensed dlthub.data_quality is optional only if already approved and version-verified; do not issue licences or carry forward unverified historical bug workarounds.

## Transformation: dbt Core
Test model grain, not-null/composite keys, relationships, accepted values, join amplification, time boundaries, exclusions, null behavior and justified reconciliation tolerances. Use data_tests plus fixture-based unit tests for non-trivial SQL where the installed Core/adapter supports them. Source/load guarantees and transformed business contracts are distinct.
Use transformation-quality. Execute only through the approved dev-only runner or user/CI. Even compile/test can execute project code/queries; store_failures may write. No test is proof of production deployment or identical production data.

## Evidence
Attach exact selection, source digest, runtime target/schema, data window, command/result and limitations. Retain documented historical warehouse caveats only after current code/evidence confirms them; do not automatically promote old exclusion lists or field values into Guides. Ingestion-to-transformation contracts must name the responsible owner and what each side verifies.
