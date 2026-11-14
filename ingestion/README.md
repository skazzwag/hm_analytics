# Data ingestion

This project uses [dlt](https://dlthub.com/) to define pipelines and
[Dagster](https://dagster.io/) to orchestrate them.

## Layout

- `definitions.py` — Dagster loads components from `defs/`
- `defs/` — Dagster components (dlt loads, dbt project, manual-trigger jobs)
- `sources/` — dlt source implementations (`api`, `sql_schema`, `blob_storage`, …)
- `dockerfiles/` — user-code and webserver images

## Pipelines

Pipelines are purpose-based (ADR 0002), not split by static/temporal cadence:

| Source module | dlt source | dlt pipeline | Table(s) written | Write disposition |
| --- | --- | --- | --- | --- |
| `api/tmdb` | `tmdb_catalogue_source` | `tmdb_catalogue` | `movie_catalogue` | merge |
| `api/omdb` | `box_office_source` | `box_office` | `box_office_snapshots` | append (pk `imdb_id` + `scraped_at`) |
| `api/violence_gore_summary` | `violence_gore_summary_source` | `violence_gore_summary` | `violence_gore_summary` (+ `violence_gore_summary__citations` child) | append |

- `tmdb_catalogue` fetches the horror catalogue from the TMDB discover
  endpoint and merges static fields into `movie_catalogue` (the join spine).
- `box_office` appends a full-catalogue OMDb snapshot per run — IMDb rating,
  Rotten Tomatoes, Metacritic and box-office values stamped with `scraped_at`.
  There is no completion or cursor logic; "latest snapshot per film" is
  derived downstream in dbt.
- `violence_gore_summary` starts one Mistral Conversations API conversation
  (`web_search` tool) per catalogue movie and appends a concise violence/gore
  summary with `tool_reference` citations stored in the `__citations` child
  table.

`movie_catalogue` is owned solely by the `tmdb_catalogue` load (ADR 0002).
Both `box_office` and `violence_gore_summary` read `movie_catalogue` from the
destination at runtime.

### Run order on a fresh warehouse

`box_office` and `violence_gore_summary` read `movie_catalogue` from the
destination at runtime, so the `tmdb_catalogue` load must run first. In
Dagster this ordering is enforced by asset dependencies (`raw/box_office_snapshots`
and `raw/violence_gore_summary` depend on `raw/movie_catalogue`), which also
orders the assets within `box_office_ingestion_job` and
`violence_gore_summary_ingestion_job`. Without Dagster, run
`uv run ingestion/run_pipeline.py --tmdb` once before the other pipelines.

## Dagster jobs

Jobs in `defs/jobs.py` are manual-trigger only (no schedules): one job per
pipeline (`tmdb_catalogue_ingestion_job`, `box_office_ingestion_job`,
`violence_gore_summary_ingestion_job`) plus `dbt_job`. Each ingestion area
also has a `*_refresh_job` that runs the same assets with
`write_disposition="replace"` via the `RefreshableDltLoadCollectionComponent`
in `ingestion/components.py`.

## Local testing

- Start local Dagster stack: `make serve`
- Tear down: `make teardown`
- Lightweight local process (no Docker): `make dev`
- Run pipelines without Dagster: `uv run ingestion/run_pipeline.py [--tmdb | --box-office | --violence-gore]`
- Validate defs/YAML: `PYTHONPATH=. uv run dg check yaml` (the project is not
  an installed package, so dg CLI needs the repo root on `PYTHONPATH` to
  resolve the project-local component type)

## Adding a source

Put extract logic in `ingestion/sources/<kind>/<name>/` and a Dagster
`DltLoadCollectionComponent` under `ingestion/defs/<name>/`. Keep credentials
in environment variables (see `.env.example`); never commit secrets.
