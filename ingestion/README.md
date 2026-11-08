# Data ingestion

This project uses [dlt](https://dlthub.com/) to define pipelines and
[Dagster](https://dagster.io/) to orchestrate them.

## Layout

- `definitions.py` — Dagster loads components from `defs/`
- `defs/` — Dagster components (dlt loads, dbt project, manual-trigger jobs)
- `sources/` — dlt source implementations (`api`, `sql_schema`, `blob_storage`, …)
- `dockerfiles/` — user-code and webserver images

## Sources

| Source module | dlt sources | dlt pipelines | Tables written |
| --- | --- | --- | --- |
| `api/tmdb` | `tmdb_static`, `tmdb_temporal` | `tmdb_static`, `tmdb_temporal` | `movie_catalogue`, `movie_details`, `movie_keywords` (static); `movie_popularity` (temporal) |
| `api/omdb` | `omdb_static`, `omdb_temporal` | `omdb_static`, `omdb_temporal` | `omdb_metadata` (static); `omdb_scores` (temporal) |
| `api/movie_analysis` | `anthropic` | `violence_gore_analysis` | `violence_gore_analysis` |

`movie_catalogue` is owned solely by the `tmdb_static` load (ADR 0001). The
OMDb temporal source keeps a persistent dlt state cursor so each daily run
scores the next batch of movies, staying within the 1,000 requests/day free
tier.

### Run order on a fresh warehouse

`omdb_temporal` and `movie_analysis` read `movie_catalogue` from the
destination at runtime, so the `tmdb_static` load must run first. In Dagster
this ordering is enforced by asset dependencies (`raw/omdb_scores` and
`raw/violence_gore_analysis` depend on `raw/movie_catalogue`), which also
orders the assets within `temporal_ingestion_job`. Without Dagster, run
`uv run ingestion/run_pipeline.py --static` once before the temporal mode.

## Dagster jobs

Jobs in `defs/jobs.py` are manual-trigger only (no schedules). Each ingestion
area has a base job (source-hardcoded write dispositions) and a `*_refresh_job`
that runs the same assets with `write_disposition="replace"` via the
`RefreshableDltLoadCollectionComponent` in `ingestion/components.py`.

## Local testing

- Start local Dagster stack: `make serve`
- Tear down: `make teardown`
- Lightweight local process (no Docker): `make dev`
- Run pipelines without Dagster: `uv run ingestion/run_pipeline.py [--static | --temporal]`
- Validate defs/YAML: `PYTHONPATH=. uv run dg check yaml` (the project is not
  an installed package, so dg CLI needs the repo root on `PYTHONPATH` to
  resolve the project-local component type)

## Adding a source

Put extract logic in `ingestion/sources/<kind>/<name>/` and a Dagster
`DltLoadCollectionComponent` under `ingestion/defs/<name>/`. Keep credentials
in environment variables (see `.env.example`); never commit secrets.
