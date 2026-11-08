# Data ingestion

This project uses [dlt](https://dlthub.com/) to define pipelines and
[Dagster](https://dagster.io/) to orchestrate them.

## Layout

- `definitions.py` — Dagster loads components from `defs/`
- `defs/` — Dagster components (dlt loads, dbt project, schedules)
- `sources/` — dlt source implementations (`api`, `sql_schema`, `blob_storage`, …)
- `dockerfiles/` — user-code and webserver images

## Sources

| Source | Cadence | Tables written |
| --- | --- | --- |
| `api/tmdb` | weekly static / daily temporal | `movie_catalogue`, `movie_details`, `movie_keywords`, `movie_popularity` |
| `api/omdb` | weekly static / daily temporal | `omdb_metadata`, `omdb_scores` |
| `api/movie_analysis` | after catalogue updates | `violence_gore_analysis` |

The OMDb temporal source keeps a persistent dlt state cursor so each daily run
scores the next batch of movies, staying within the 1,000 requests/day free tier.

## Local testing

- Start local Dagster stack: `make serve`
- Tear down: `make teardown`
- Lightweight local process (no Docker): `make dev`
- Run pipelines without Dagster: `uv run ingestion/run_pipeline.py [--static | --temporal]`

## Adding a source

Put extract logic in `ingestion/sources/<kind>/<name>/` and a Dagster
`DltLoadCollectionComponent` under `ingestion/defs/<name>/`. Keep credentials
in environment variables (see `.env.example`); never commit secrets.
