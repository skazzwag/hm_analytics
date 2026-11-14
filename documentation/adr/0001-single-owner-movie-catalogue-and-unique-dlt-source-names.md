# ADR 0001: Single owner for `movie_catalogue` and unique dlt source names

- **Status:** Superseded by ADR 0002 (originally Accepted 2026-11-08)
- **Date:** 2026-11-08
- **Owner:** data-architect
- **Implementation owner (when approved):** data-engineer (ingestion); analytics-engineer consulted for dbt/Guide impact

## Context

The Dagster code location cannot load because repository assembly aborts on two
classes of pre-existing conflicts:

1. **Duplicate asset key `raw/movie_catalogue`.** Both TMDB loads expose a
   `movie_catalogue` dlt resource into the same `raw` dataset:
   - `ingestion/sources/api/tmdb/main.py:150` — `tmdb_static_source`
     (merge, weekly cadence).
   - `ingestion/sources/api/tmdb/main.py:264` — `tmdb_temporal_source`
     (merge, daily cadence). Its docstring says it upserts the catalogue
     "so that OMDb temporal can always find the table even when the static
     pipeline has not yet run".
   Both loads in `ingestion/defs/tmdb/loads.py` use `dataset_name="raw"`, so
   dagster-dlt derives the same asset key `raw/movie_catalogue` for both.
2. **Latent duplicate multi-asset op names.** Both loads per source share
   `@dlt.source(name="tmdb")` / `@dlt.source(name="omdb")` plus
   `dataset_name="raw"`. dagster-dlt names the ops
   `dlt_assets_{source.name}_{dataset_name}`, yielding `dlt_assets_tmdb_raw`
   twice and `dlt_assets_omdb_raw` twice. These surface immediately after #1
   is fixed.

Additional constraints weighing on the design:

- Runs are **manual-only** (schedules were removed). Asset groups:
  `tmdb_static`, `tmdb_temporal`, `omdb_static`, `omdb_temporal`,
  `movie_analysis`, `dbt`. Refresh jobs run the same dlt loads with a
  run-level `dlt/write_disposition=replace` tag that overrides **all** loads
  in the selected groups (`ingestion/components.py`).
- `omdb_temporal` and `movie_analysis` read `movie_catalogue` from the
  destination at runtime (`ingestion/sources/api/omdb/main.py::read_movie_catalogue`
  via `dlt.current.pipeline()`; `ingestion/sources/api/movie_analysis/main.py`
  via hardcoded `raw.movie_catalogue` / `raw.violence_gore_analysis` SQL).
- All dlt loads except `movie_analysis` share `pipeline_name="horror_movies"`,
  so overlapping manual runs race on shared dlt state.
- OMDb free tier: 1,000 req/day; `omdb_scores` keeps a persistent dlt
  resource-state cursor. `violence_gore_analysis` skips already-analyzed
  movies via table set-difference, not dlt state.
- Destination is DuckDB locally / MotherDuck in prod (`PIPELINE_DESTINATION`).
- dbt reads one source, `horror_movies`, schema `raw`
  (`transformation/models/0_sources/source.yml`), with staging models
  `stg_movie_catalogue`, `stg_movie_details`, `stg_movie_keywords`,
  `stg_movie_popularity` (source only), `stg_omdb_metadata`,
  `stg_omdb_scores`, `stg_violence_gore_analysis`.

## Options considered

### (a) Single owner for `movie_catalogue` — static load owns it

Remove the `movie_catalogue` resource from `tmdb_temporal_source`. The static
load becomes the sole writer.

- *Pros:* eliminates the duplicate asset key at its root; the temporal
  resource was writing byte-identical data (same discover pagination, same
  field filtering) to what static writes, so no information is lost.
- *Bonus fix:* today `temporal_refresh_job` would apply run-level `replace`
  to the temporal `movie_catalogue` load, **wiping the catalogue down to the
  current top-25 discover pages** (movies that dropped out of popularity
  would be deleted). Single ownership removes `movie_catalogue` from the
  temporal group entirely, closing a latent data-loss path.
- *Cons:* the bootstrap convenience ("OMDb temporal works before static has
  ever run") disappears. Mitigated below.

### (b) Distinct dataset names per load (`raw` vs `raw_temporal`)

- *Pros:* fixes both duplicate asset keys and duplicate op names.
- *Cons:* splits dbt source tables across two schemas (new dbt source or
  per-table overrides — analytics-engineer work); breaks
  `raw.movie_catalogue` reads in `movie_analysis` and
  `read_movie_catalogue`; the temporal catalogue upsert would no longer
  update the table dbt/OMDb actually read, defeating its stated purpose.
- *Rejected.*

### (c) Merge static + temporal into one source with different cadence jobs

- *Cons:* a dlt load runs as one multi-asset op; the daily temporal job would
  re-execute the full source (~500+ `/movie/{id}` and `/keywords` requests
  per day), blowing the request budgets the split was designed to protect.
  Dagster asset selection cannot split a single dlt load's execution.
- *Rejected.*

### (d) Recommended: (a) + distinct dlt source names + distinct pipeline names

Keep `dataset_name="raw"` everywhere (so dbt sources, `read_movie_catalogue`,
and `movie_analysis` SQL are untouched), and:

1. **Single owner:** `tmdb_static_source` is the only writer of
   `movie_catalogue`; remove the resource from `tmdb_temporal_source`
   (temporal keeps only `movie_popularity`, append).
2. **Distinct source names** to fix op names:
   `@dlt.source(name="tmdb_static")`, `name="tmdb_temporal"`,
   `name="omdb_static"`, `name="omdb_temporal"` (movie_analysis keeps
   `name="anthropic"` — already unique). Ops become e.g.
   `dlt_assets_tmdb_static_raw`, `dlt_assets_tmdb_temporal_raw`.
3. **Distinct pipeline names per load** (reviewer suggestion, adopted):
   `tmdb_static`, `tmdb_temporal`, `omdb_static`, `omdb_temporal` instead of
   the shared `horror_movies`, eliminating the shared dlt state race between
   overlapping manual runs. `movie_analysis` already uses its own pipeline
   name (`violence_gore_analysis`).

### Bootstrap replacement for "temporal keeps catalogue fresh"

With runs manual-only, the cheapest correct replacement is run-order
documentation plus an optional Dagster dependency:

- **Required:** document in `ingestion/README.md` and the job descriptions
  that on a fresh warehouse, `tmdb_static_ingestion_job` must run before
  `omdb_temporal` / `movie_analysis` (both read `movie_catalogue` at runtime).
- **Preferred (flag for verification):** declare an asset dependency from the
  `omdb_temporal` and `movie_analysis` loads on the `raw/movie_catalogue`
  asset so Dagster enforces ordering in the UI. Whether
  `DltLoadCollectionComponent` translation supports external `deps` needs
  verification during implementation; if unsupported, fall back to
  documentation-only ordering.

## Decision

Adopt option **(d)**: static TMDB load becomes the single owner of
`movie_catalogue`; the temporal TMDB source drops the resource; all four
static/temporal dlt sources get distinct names (`tmdb_static`,
`tmdb_temporal`, `omdb_static`, `omdb_temporal`) fixing the duplicate op
names; each load gets its own dlt pipeline name, replacing the shared
`horror_movies` pipeline name. `dataset_name` remains `raw` for every load.

## Consequences

### Positive

- Code location loads: unique asset keys and unique op names.
- Closes the latent `temporal_refresh_job` `replace` wipe of
  `movie_catalogue`.
- No shared dlt state races between overlapping manual runs.
- **Zero dbt changes and zero changes to runtime SQL readers** — dataset,
  table names, and schema are untouched.

### Trade-offs / negative

- The bootstrap behavior (OMDb temporal functioning before any static run) is
  replaced by documented run order (and optionally a Dagster dependency).
- Renaming sources and pipelines **resets dlt state**: the `omdb_scores`
  resource-state cursor restarts at 0, re-fetching one batch (~800 OMDb
  requests, one time; append-only table so it appears as extra snapshots
  without breaking the time series). `violence_gore_analysis` is unaffected
  (uses table set-difference, not dlt state). Merge loads are unaffected
  (primary-key upserts read from the table, not state).
- `movie_popularity`'s `primary_key=["id", "scraped_at"]` with `append`
  remains a no-op dedupe hint (pre-existing; unchanged by this ADR).

## Migration steps (ingestion — data-engineer, not in this ADR's scope to implement)

1. In `ingestion/sources/api/tmdb/main.py`: delete the `movie_catalogue`
   resource from `tmdb_temporal_source`; rename both `@dlt.source` names to
   `tmdb_static` / `tmdb_temporal`; update module docstrings.
2. In `ingestion/sources/api/omdb/main.py`: rename `@dlt.source` names to
   `omdb_static` / `omdb_temporal`.
3. In `ingestion/defs/tmdb/loads.py`, `ingestion/defs/omdb/loads.py`, and
   `ingestion/run_pipeline.py`: use per-load pipeline names
   (`tmdb_static`, `tmdb_temporal`, `omdb_static`, `omdb_temporal`); keep
   `dataset_name="raw"`. Note `run_pipeline.py`'s `get_movies()` can keep any
   pipeline handle that points at the same destination/dataset.
4. Update job descriptions / README run-order note (see bootstrap
   replacement above); optionally add the Dagster asset dependency after
   verifying component support.
5. Verify the code location loads (`dagster definitions validate` or loading
   in the UI) and that all seven asset keys are unique:
   `raw/movie_catalogue`, `raw/movie_details`, `raw/movie_keywords`,
   `raw/movie_popularity`, `raw/omdb_metadata`, `raw/omdb_scores`,
   `raw/violence_gore_analysis`.

## Follow-ups and impact callouts

- **analytics-engineer (dbt):** no `transformation/` change expected —
  `source.yml` (`horror_movies.raw`) and all staging models are untouched by
  this decision. Please confirm no downstream docs/tests reference the old
  dlt source/pipeline names. **Guide impact:** check whether
  `transformation/guides/warehouse-overview/guide.md` (or future guides)
  should record `movie_catalogue` ownership (TMDB static load, weekly) and
  the manual run-order dependency; this ADR proposes that semantic
  definition but does not edit Guides.
- **Open questions for the user:**
  1. Accept the one-time OMDb temporal cursor reset (~800 extra API requests,
     one batch re-fetched) as the cost of the rename? If not, pipeline names
     can stay shared and only source names change (op-name fix preserved,
     state race remains).
  2. Prefer the Dagster asset dependency (needs component-support
     verification) or documentation-only run order for the bootstrap case?
  3. Should `temporal_ingestion_job` continue to bundle `tmdb_temporal`,
     `omdb_temporal`, and `movie_analysis` in one job, or split now that
     `movie_analysis` depends on catalogue freshness?
