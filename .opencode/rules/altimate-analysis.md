# Altimate analysis boundaries
Load altimate-sql-analysis. Altimate remains deterministic and on-demand: no second agent or new MCP.
Use compiled SQL and matching manifest/catalog from the approved dev runner or traceable user/CI. Default runner paths are .analysis/dbt/<actor>/<session>/target/. Source edits invalidate earlier evidence. Review profile/target/schema provenance, variables/macros and live schema; local freshness checks are not signed attestation.
When missing/stale, eligible roles may request the dev runner. If its boundary is not enabled, request user/CI artifacts. Never bypass with raw dbt or simulate mappings.
Exit 0 is static evidence, not deployment/business equivalence; findings, unsupported constructs and empty/unresolved mappings remain explicit. Use model graph only for downstream candidates then compute consumer column mappings. Filters/grain/row loss need transformation DQ tests.
