# Adapter provenance

`analyze.mjs`, `prepare-dbt.mjs`, examples and the original helper tests are carried forward from the starter supplied earlier in this conversation, with freshness gating added to the preparation CLI. This is custom integration code, not an official Altimate release.

The native package stays pinned to `@altimateai/altimate-core@0.7.0`. It is not claimed to be the latest. API reference: AltimateAI/altimate-code `packages/opencode/src/altimate/native/altimate-core.ts` and `native/dbt/lineage.ts`.

Dependency-free tests exercise adapters with fixtures/mocks. A local native self-test and real compiled DuckDB/MotherDuck model test are still required. No native binaries, warehouse data or credentials are bundled.
