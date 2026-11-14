# hm_analytics

Analytics project studying the effect of violence and gore on horror movie reception.

Data is ingested from [TMDB](https://www.themoviedb.org/) and [OMDb](https://www.omdbapi.com/) into a DuckDB/MotherDuck database using [dlt](https://dlthub.com/). Classifications on the level of violence and gore in the horror movies are determined through the Mistral Conversations API with server-side web search, which is also handled as a custom dlt pipeline.

## Project Structure

```
hm_analytics/
├── ingestion/                     # dlt pipelines orchestrated by Dagster
│   ├── definitions.py             # Dagster definitions entrypoint
│   ├── defs/                      # Dagster components (dlt loads, dbt, jobs)
│   ├── sources/                   # dlt source implementations
│   │   └── api/
│   │       ├── tmdb/              # TMDB catalogue source
│   │       ├── omdb/              # OMDb box-office snapshot source
│   │       └── violence_gore_summary/ # Mistral web-search summary source
│   ├── dockerfiles/               # user-code and webserver images
│   └── run_pipeline.py            # CLI runner (manual runs without Dagster)
├── transformation/                # dbt Core transformations (DuckDB / MotherDuck)
│   ├── models/0_sources/          # source declarations
│   ├── models/1_staging/          # stg_ — clean and standardize
│   ├── models/2_intermediate/     # int_ — business logic and joins
│   ├── models/3_domain/           # dmn_ — core business entities
│   ├── models/4_presentation/     # prs_ — analysis-ready tables
│   ├── models/5_activation/       # act_ — reverse ETL / activation
│   ├── macros/                    # project macros
│   └── guides/                    # warehouse Guides
├── infrastructure/motherduck/     # SQL for warehouse databases, shares, grants
├── documentation/                 # onboarding and engineering docs
├── tools/                         # repo tooling (dbt metadata checks)
└── visualisation/                 # reserved for dashboards
```

## Quickstart

### 1. Install dependencies

```bash
make setup   # uv + pre-commit (or: uv sync)
```

### 2. Configure secrets

Copy `.env.example` to `.env` and fill in the values:

```
# For ingestion pipelines
SOURCES__TMDB__API_KEY=...
SOURCES__OMDB__API_KEY=...
SOURCES__MISTRAL__API_KEY=...
DESTINATION__MOTHERDUCK__CREDENTIALS="md:///horror_movies?motherduck_token=..."

# For dbt pipelines
MOTHERDUCK_PROD_TOKEN=...
```

For the MotherDuck remote MCP with Opencode run `opencode mcp auth motherduck` to authenticate.

Get a free TMDB API key at [themoviedb.org/settings/api](https://www.themoviedb.org/settings/api).  
Get a free OMDb API key at [omdbapi.com/apikey](https://www.omdbapi.com/apikey.aspx).  
Get a Mistral API key at [console.mistral.ai](https://console.mistral.ai/).

This repo has been set up with `direnv` such that entering the root directory of this repo will effectively run `source .env`. For this to work, 
ensure that you have `direnv` installed, the `eval "$(direnv hook bash)"` added to your `.bashrc` or equivalent, and `direnv allow` has been run in the repo root.

### 3. Run the pipeline

Without Dagster (manual runs):

```bash
uv run ingestion/run_pipeline.py             # all three pipelines
uv run ingestion/run_pipeline.py --tmdb      # catalogue only
uv run ingestion/run_pipeline.py --box-office --violence-gore
```

With Dagster:

```bash
make dev       # Dagster UI without Docker
make serve     # Dagster UI via Docker Compose
make teardown  # stop Docker Compose
```

## Layer conventions

| Folder | Prefix | Role |
| --- | --- | --- |
| `1_staging` | `stg_` | Clean and standardize source data |
| `2_intermediate` | `int_` | Business logic and joins |
| `3_domain` | `dmn_` | Core business entities |
| `4_presentation` | `prs_` | Analysis-ready tables |
| `5_activation` | `act_` | Reverse ETL / activation |

dbt lives under `transformation/`. Default target is `dev-local` (a local DuckDB file).

```shell
uv run dbt seed --project-dir transformation --profiles-dir transformation --target dev-local
uv run dbt build --project-dir transformation --profiles-dir transformation --target dev-local
```

---

## Pipeline Design

The ingestion is organized into **purpose-based pipelines** (ADR 0002) rather
than a static/temporal cadence split:

| Purpose | dlt pipeline | Tables written | Write disposition |
|---|---|---|---|
| Catalogue (join spine) | `tmdb_catalogue` | `movie_catalogue` | merge |
| Box-office snapshots | `box_office` | `box_office_snapshots` | append |
| Content analysis | `violence_gore_summary` | `violence_gore_summary` (+ `violence_gore_summary__citations`) | append |

The `box_office` pipeline appends a full-catalogue OMDb snapshot on every run
(no completion or cursor logic); "final box office" is the latest snapshot per
film, derived downstream in dbt. The `violence_gore_summary` pipeline sends
one Mistral Conversations API request (with the `web_search` tool) per movie.

> **Run order on a fresh warehouse:** `movie_catalogue` is written only by the
> `tmdb_catalogue` pipeline. The `box_office` and `violence_gore_summary`
> pipelines read it at runtime, so run the catalogue load first (in Dagster,
> `raw/box_office_snapshots` and `raw/violence_gore_summary` declare a
> dependency on `raw/movie_catalogue`, which enforces this ordering).

### Request cost per run

| Step | Requests | Notes |
|---|---|---|
| TMDB catalogue (25 pages, 500 movies) | 25 | Discover endpoint only |
| OMDb box office (~1,061 movies) | ~1,061 | One request per movie — roughly one day's 1,000/day free tier quota |
| Mistral violence/gore summary | ~1,061 | One conversation per movie; web search billed per use |

The TMDB catalogue pipeline paginates the discover endpoint once and merges
the results into `movie_catalogue`. The OMDb box-office pipeline fetches the
full catalogue on every run, so it is triggered manually to stay within the
1,000 requests/day free tier.

---

## Data Tables

All tables sit in the `raw` schema. The catalogue uses merge disposition
(upsert); the snapshot and analysis tables use append (one row per movie per
run), enabling time-series analysis.

### Source: TMDB

API: `https://api.themoviedb.org/3` · Horror genre ID: 27 · Rate limit: ~4 req/sec

#### `raw.movie_catalogue`

One row per horror movie. Static fields from the discover endpoint.

| Column | Type | Description |
|---|---|---|
| `id` | integer | TMDB movie ID (primary key) |
| `title` | string | Release title |
| `original_title` | string | Title in original language |
| `original_language` | string | ISO 639-1 language code |
| `overview` | string | Plot summary |
| `release_date` | date | Theatrical release date |
| `adult` | boolean | Adult content flag |
| `video` | boolean | Video release flag |
| `poster_path` | string | Relative path to poster image |
| `backdrop_path` | string | Relative path to backdrop image |
| `genre_ids` | list | TMDB genre ID list |

---

### Source: OMDb

API: `http://www.omdbapi.com/` · Lookup: by title + release year · Rate limit: 1,000 req/day (free tier)

Movies not found on OMDb are silently skipped. A full-catalogue run consumes roughly the entire daily free-tier quota — plan runs accordingly.

#### `raw.box_office_snapshots`

One row per matched movie per pipeline run. Aggregated review scores and box-office values, appended as timestamped snapshots.

| Column | Type | Description |
|---|---|---|
| `imdb_id` | string | IMDb title ID (composite primary key) |
| `scraped_at` | timestamp | UTC timestamp of the pipeline run (composite primary key) |
| `tmdb_id` | integer | TMDB movie ID (foreign key to `movie_catalogue`) |
| `imdb_rating` | string | IMDb weighted average rating (0–10) |
| `imdb_votes` | string | Number of IMDb user votes |
| `metascore` | string | Metacritic score (0–100) |
| `rotten_tomatoes_score` | string | Rotten Tomatoes tomatometer (e.g. "72%") |
| `metacritic_score` | string | Metacritic score from Ratings array |
| `box_office` | string | US box office gross (e.g. "$47,000,000") |

---

### Source: Mistral

API: `https://api.mistral.ai/v1` · Conversations API with the `web_search` tool · One conversation per movie

#### `raw.violence_gore_summary`

One row per movie per pipeline run. Concise violence/gore summary generated via web search.

| Column | Type | Description |
|---|---|---|
| `title` | string | Movie title used in the prompt |
| `release_date` | string | Theatrical release date |
| `tmdb_id` | integer | TMDB movie ID (foreign key to `movie_catalogue`) |
| `model` | string | Mistral model used |
| `summary` | string | Concise violence/gore summary ending in severity and frequency labels |
| `citations` | list | Web-search citations (also exploded into the child table) |
| `scraped_at` | timestamp | UTC timestamp of the pipeline run |

#### `raw.violence_gore_summary__citations`

Child table with the web-search citations backing each summary row.

| Column | Type | Description |
|---|---|---|
| `title` | string | Citation source title |
| `url` | string | Citation source URL |

---

## Manual triggering with Dagster

All Dagster jobs are manual-trigger only; nothing runs on a schedule. Launch
them from the Dagster UI (Deployment > Jobs > Launch) or the CLI:

```bash
# From the repository root
uv run dagster job launch -m ingestion.definitions -j box_office_ingestion_job
# Refresh variant (runs the same assets with write_disposition="replace")
uv run dagster job launch -m ingestion.definitions -j box_office_refresh_job
```

| Job | What runs |
|---|---|
| `tmdb_catalogue_ingestion_job` | TMDB catalogue (merge) |
| `box_office_ingestion_job` | OMDb box-office snapshots (append) |
| `violence_gore_summary_ingestion_job` | Mistral violence/gore summaries (append) |
| `dbt_job` | dbt transformation models |

Each pipeline also has a `*_refresh_job` (`tmdb_catalogue_refresh_job`,
`box_office_refresh_job`, `violence_gore_summary_refresh_job`) that runs the
same assets with `write_disposition="replace"`: it **deletes and rebuilds**
the target tables, so use it only when you want a full reload.

### MotherDuck (production destination)

Manual runs write to [MotherDuck](https://motherduck.com/) instead of a local DuckDB file. To use MotherDuck locally, add to `.env`:

```
PIPELINE_DESTINATION=motherduck
DESTINATION__MOTHERDUCK__CREDENTIALS=md:///horror_movies?motherduck_token=YOUR_TOKEN
```

---

## Requirements

- Python 3.12+
- [uv](https://docs.astral.sh/uv/)
- TMDB API key (free)
- OMDb API key (free)
- Mistral API key
- MotherDuck account (for production runs)
