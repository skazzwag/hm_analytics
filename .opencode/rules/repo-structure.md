# Repo structure

Load this when adding a source, Dagster def, or dbt model so new files match the existing layout.

```text
ingestion/
  sources/
    api/                      # REST — one folder per source
      coiote/                 # config, client, resources, main
      github/                 # main + queries/*.graphql
      hubspot/
      jira/
      sonarqube/
    sql_schema/               # MySQL — one module per schema
      fido1.py
      fido_way.py
      gis_service.py
      relay.py
    blob_storage/             # Azure blob → Glacier
      mappings.py
    database/motherduck/      # reverse ETL read from MotherDuck
  defs/                       # Dagster components
    dbt/
    github/  hubspot/  jira/  sonarqube/
    partner_api/              # reverse ETL write
    schedules.py
  runners.py  glossary.py  connections.py  definitions.py
  dockerfiles/  tests/

transformation/models/
  0_sources/                  # source YAML + freshness; no SQL
  1_staging/                  # stg_{source}__{entity} — clean one source
  2_intermediate/             # int_{logical_name} — business logic, multi-source joins
  3_domain/                   # dmn_{entity} — clean business entities
  4_presentation/             # prs_{logical_name} — analysis-ready reuse layer
  5_activation/               # act_{logical_name} — reverse ETL from prs_
  6_access/                   # mart copies (prod_edge, prod_operations)
  marts/validation/
  utils/

partner_api/                  # OpenAPI spec (not pipeline code)
infrastructure/motherduck/    # warehouse SQL — propose only
documentation/                # ADRs under documentation/adr/
.github/workflows/
```

## Conventions

- New REST source: `ingestion/sources/api/<name>/` plus `ingestion/defs/<name>/` (`defs.yaml`, `loads.py`) if Dagster should run it. Mirror github/hubspot/jira/sonarqube.
- New SQL schema: add a module under `ingestion/sources/sql_schema/` and wire it in `glossary.py` / runners. Do not invent a second SQL layout.
- Reverse ETL stays in `sources/database/motherduck/` (read) and `defs/partner_api/` (write).
- Do not create a top-level `pipelines/` directory.

## Integration and analyst paths
- analysis/: **fully Git-ignored personal analyst workspace**, with marimo notebooks, exploration plans, limited extracts and context candidates; not inside dbt. This workspace is not repository source or CI input.
- transformation/guides/: canonical guide.md + guide.metadata.json, per supplied README; existing validate.sh/sync.sh are CI implementation, not replaced here.
- Skills, agents, commands and rule files live in this repository under `.opencode/` (agents/, commands/, skills/, rules/), discovered by OpenCode at project level; they apply only inside this repository.
- .opencode/tools/altimate/: deterministic adapter/artifact/freshness tooling.
- .opencode/tools/dbt/: opt-in dev-only runner and tests; not a security sandbox.
- .analysis/: ignored dbt/Altimate evidence; distinct from the also-ignored personal analyst workspace in analysis/.
