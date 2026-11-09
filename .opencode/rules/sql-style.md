# SQL style

Load this file when writing or reviewing SQL (dbt models, DuckDB CLI, MotherDuck queries).

- Follow project sqlfluff rules. 4-space indent for SQL, 2-space for YAML.
- Meaningful aliases. Never single-letter aliases.
- Explicit column lists. `SELECT *` only in staging models or data-mart copy models.
- **RF02:** qualify every column when more than one table/CTE is in scope, including `QUALIFY`, calculated fields, and `WHERE`.
- No `USING` joins. Use explicit `ON`.
- Prefer equi-joins. Normalize NULLs to sentinels (`'__NULL__'`, `-1`) in CTEs before joining. Do not use `OR` in join conditions.
- CTE order: source → normalized → enriched → aggregated → `final`. Last CTE is always `final`.
- Descriptive CTE names: `{entity}_normalized`, `{entity}_enriched`, `{entity}_deduplicated`.
- Deduplicate with `QUALIFY`.
- When renaming override columns through CTEs, prefix with `override_` (for example `additional_comments` → `override_additional_comments`).
