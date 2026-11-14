# dbt standards

Load this file when writing or reviewing models under `transformation/`. Runtime uses only the approved dev-only runner; read dbt-execution.md.

## Layers and names

| Layer | Folder | Name | Meaning |
|-------|--------|------|---------|
| Sources | `0_sources/` | source YAML only | Source definitions and freshness. No SQL models. |
| Staging | `1_staging/` | `stg_{source}__{entity}` | Raw cleaning and standardization from one source. |
| Intermediate | `2_intermediate/` | `int_{logical_name}` | Business logic and multi-source joins. |
| Domain | `3_domain/` | `dmn_{entity}` | Clean business entities (waypoint, branch, DMA, …). |
| Presentation | `4_presentation/` | `prs_{logical_name}` | Analysis-ready tables. Reuse layer for activation and reports. |
| Activation | `5_activation/` | `act_{logical_name}` | Reverse ETL / activation. Select from presentation; do not re-join sources. |
| Access / marts | `6_access/` | `acc_` / mart copies | Copies into other MotherDuck DBs (`prod_edge/`, `prod_operations/`). |

YAML: `_{layer_name}.yml` or source-specific names. Every model has YAML in the same directory. Document every column: `name`, `data_type`, `description`. Keep descriptions in the model YAML. Do not treat `datadictionary.yml` as canonical.

## Macros

- Surrogate keys: `dbt_utils.generate_surrogate_key([...])`.
- Cleaning: `{{ clean(field) }}`. User text: `{{ clean_free_text(field) }}`. Units: `{{ convert_units(value, 'in', 'out') }}`. Never hand-roll these.
- Document every macro in `macros/_macros.yml`.
- Do not override `generate_schema_name` per model. Prod uses custom schemas (`dbt_stg`, `dbt_int`, `dbt_dmn`, `dbt_prs`, `dbt_act`); dev/QA ignore custom schemas.

## Tests

- Use `data_tests:` (not `tests:`).
- PKs: `not_null` + `unique`, or `dbt_utils.unique_combination_of_columns`.
- FKs: `relationships` to the parent, with `where` when needed for performance.
- Prefer `dbt_utils` over `dbt_expectations`.
- Unit tests: `unit_test__{model_name}.yml` next to the model.

## Design

- Activation and reporting consume presentation models. Do not re-implement joins in `act_` models.
- Seeds: set `+column_types` in `dbt_project.yml` when DuckDB infers badly.
- Snapshots with `strategy='check'` and `check_cols='all'`: renaming a column invalidates all history. Warn before renaming.
- Current override rows: `dbt_valid_to is null`.
- Prod schemas: `1_staging` → `dbt_stg`, `2_intermediate` → `dbt_int`, `3_domain` → `dbt_dmn`, `4_presentation` → `dbt_prs`, `5_activation` → `dbt_act`, `6_test` → `dbt_prod`, seeds → `dbt_seed`. Do not manage `elementary` or `dbt_test__audit`.
- Data marts: `select *` from `prod_analytics` / `dev_analytics` into other DBs; copied YAML uses `acc_` prefix. Never create or delete MotherDuck infrastructure.

## Fido Plus

Sponsors: Microsoft, Meta, Coca Cola Foundation. Key models: `stg_fido_plus_config`, `prs_fido_plus_waypoints`. `config_complete` gates active periods. `override_end_date` is point-in-time. SCD: `qualify row_number() over (partition by waypoint_id, reporting_period_name order by valid_from desc)`.

## Refactors

Update YAML tests, downstream column refs, data dictionary if still used, and snapshot implications. Investigate test failures via compiled SQL under `target/compiled/` and `dbt_test__audit` — use the approved dev runner or traceable user/CI evidence.

## Deterministic evidence and durable context

Select exactly one installed tool-prefixed Altimate skill (`dbt-creating-dbt-models`, `dbt-debugging-dbt-errors`, `dbt-testing-dbt-models`, `dbt-documenting-dbt-models`, `dbt-migrating-sql-to-dbt`, `dbt-refactoring-dbt-models` or `dbt-developing-incremental-models`). All project layer, naming, macro, data test and development-execution standards in this file override generic upstream guidance. Translate its execution steps into the approved dev runner; when unavailable, request user/CI evidence. Do not enable dbt MCP execution as a workaround.

Use `altimate-sql-analysis` for compiled SQL checks and column mappings. Source changes invalidate earlier compiled evidence; stale artifacts mean pending verification. The native helper is static analysis, not a dbt test runner.

After model/metric/grain/join/filter/DQ changes, load `motherduck-guides` and update relevant local Guide drafts with evidence and deployment status, or state why there is no durable context change. Commit Guide content for PR review; existing CI alone publishes from main.
