# hm_analytics

Analytics project studying the effect of violence and gore on horror movie reception.

Data is ingested from [TMDB](https://www.themoviedb.org/) and [OMDb](https://www.omdbapi.com/) into a DuckDB database using [dlt](https://dlthub.com/). Future sections will add dbt Core transformations and marimo visualisations.

`opencode mcp auth motherduck`

## Project Structure

```
hm_analytics/
├── ingestion/                  # dlt ingestion pipelines
│   ├── sources/
│   │   ├── tmdb.py             # TMDB sources (static + temporal)
│   │   └── omdb.py             # OMDb sources (static + temporal)
│   ├── run_pipeline.py         # Production pipeline runner
│   └── explore.py              # Marimo notebook for post-load inspection
├── transformation/             # dbt Core transformations (coming soon)
├── visualisation/              # Marimo analysis notebooks (coming soon)
└── .dlt/
    └── config.toml             # Non-secret config (API base URLs, dataset name)
```

## Quickstart

### 1. Install dependencies

```bash
uv sync
```

### 2. Configure secrets

Ensure you have the following environment variables set:

```
# For ingestion pipelines
SOURCES__TMDB__API_KEY=...
SOURCES__OMDB__API_KEY=...
DESTINATION__MOTHERDUCK__CREDENTIALS="md:///horror_movies?motherduck_token=..."
ANTHROPIC_API_KEY=...

# For dbt pipelines
MOTHERDUCK_PROD_TOKEN=...

# For MCP assistance
HM_ANALYTICS_DBT_PROJECT_DIR="{repo_root_path}/transformation"
HM_ANALYTICS_DBT_PAT="{repo_root_path}/.venv/bin/dbt"
```

For the MotherDuck remote MCP with Opencode run `opencode mcp auth motherduck` to authenticate.

Get a free TMDB API key at [themoviedb.org/settings/api](https://www.themoviedb.org/settings/api).  
Get a free OMDb API key at [omdbapi.com/apikey](https://www.omdbapi.com/apikey.aspx).

This repo has been set up with `direnv` such that entering the root directory of this repo will effectively run `source .env`. For this to work, 
ensure that you have `direnv` installed, the `eval "$(direnv hook bash)"` added to your `.bashrc` or equivalent, and `direnv allow` has been run in the repo root.

### 3. Run the pipeline

```bash
# First-time setup — run everything
uv run run-ingestion --static --temporal

# Daily temporal run (default) — popularity snapshots + OMDb score batch
uv run run-ingestion

# Weekly static run — new releases, full details, keywords, OMDb metadata
uv run run-ingestion --static

# Limit discover pages for a quick test (20 movies/page)
uv run run-ingestion --max-pages 5

# Reduce OMDb batch size if approaching the 1,000 req/day limit
uv run run-ingestion --omdb-batch-size 400
```

### 4. Explore the data

```bash
uv run marimo run ingestion/explore.py
```

---

## Pipeline Design

The ingestion is split into **static** and **temporal** pipelines to avoid re-fetching unchanged data on every run.

| Cadence | Flag | Pipeline | Tables written |
|---|---|---|---|
| Weekly | `--static` | TMDB static | `movie_catalogue`, `movie_details`, `movie_keywords` |
| Weekly | `--static` | OMDb static | `omdb_metadata` |
| Daily | _(default)_ | TMDB temporal | `movie_popularity` |
| Daily | _(default)_ | OMDb temporal | `omdb_scores` |

### Request cost per run

| Step | Requests | Notes |
|---|---|---|
| TMDB static (25 pages, 500 movies) | ~1,025 | 25 discover + 500 details + 500 keywords |
| TMDB temporal (25 pages) | 25 | Discover endpoint only |
| OMDb static (500 movies) | 500 | One request per movie |
| OMDb temporal (batch of 800) | 800 | Cursor advances each day; resets after full cycle |

The TMDB static pipeline paginates discover once and shares the resulting movie IDs across all three resources — eliminating the 3× duplication that would occur if each resource paginated independently.

The OMDb temporal pipeline uses a persistent dlt state cursor to process movies in batches across consecutive days, keeping each run within the 1,000 requests/day free tier.

---

## Data Tables

All tables sit in the `raw` schema. Static tables use merge disposition (upsert); temporal tables use append (one row per movie per run), enabling time-series analysis.

### Source: TMDB

API: `https://api.themoviedb.org/3` · Horror genre ID: 27 · Rate limit: ~4 req/sec

#### `raw.movie_catalogue` — static, merge

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

#### `raw.movie_details` — static, merge

One row per horror movie. Full metadata from `/movie/{id}`, static fields only.

| Column | Type | Description |
|---|---|---|
| `id` | integer | TMDB movie ID (primary key) |
| `title` | string | Release title |
| `original_title` | string | Title in original language |
| `tagline` | string | Marketing tagline |
| `overview` | string | Plot summary |
| `release_date` | date | Theatrical release date |
| `status` | string | Release status (e.g. Released, Post Production) |
| `runtime` | integer | Runtime in minutes |
| `budget` | integer | Production budget (USD) |
| `revenue` | integer | Box office revenue (USD) |
| `genre_names` | string | Comma-separated genre names |
| `us_certification` | string | MPAA rating for US release (e.g. R, PG-13) |
| `homepage` | string | Official website URL |
| `imdb_id` | string | IMDb title ID (tt-prefixed) |
| `original_language` | string | ISO 639-1 language code |
| `adult` | boolean | Adult content flag |

#### `raw.movie_keywords` — static, merge

Normalised keyword associations, one row per (movie, keyword) pair.

| Column | Type | Description |
|---|---|---|
| `movie_id` | integer | TMDB movie ID (composite primary key) |
| `keyword_id` | integer | TMDB keyword ID (composite primary key) |
| `keyword_name` | string | Keyword text (lowercased) |

#### `raw.movie_popularity` — temporal, append

One row per movie per pipeline run. Popularity and vote metrics from the discover endpoint.

| Column | Type | Description |
|---|---|---|
| `id` | integer | TMDB movie ID (composite primary key) |
| `scraped_at` | timestamp | UTC timestamp of the pipeline run (composite primary key) |
| `popularity` | float | TMDB popularity score |
| `vote_average` | float | Mean user rating (0–10) |
| `vote_count` | integer | Number of user ratings |

---

### Source: OMDb

API: `http://www.omdbapi.com/` · Lookup: by title + release year · Rate limit: 1,000 req/day (free tier)

Movies not found on OMDb are silently skipped. The free tier is shared across both static and temporal pipelines — plan runs accordingly.

#### `raw.omdb_metadata` — static, merge

One row per matched movie. Cast, crew, and descriptive metadata.

| Column | Type | Description |
|---|---|---|
| `imdb_id` | string | IMDb title ID (primary key) |
| `tmdb_id` | integer | TMDB movie ID (foreign key to `movie_catalogue`) |
| `title` | string | Title as listed on OMDb |
| `year` | string | Release year |
| `rated` | string | MPAA content rating (e.g. R, PG-13, NR) |
| `runtime` | string | Runtime (e.g. "109 min") |
| `director` | string | Director name(s) |
| `writer` | string | Writer name(s) |
| `actors` | string | Top-billed cast |
| `plot` | string | Short plot summary |
| `awards` | string | Awards and nominations summary |
| `dvd` | string | DVD release date |

#### `raw.omdb_scores` — temporal, append

One row per matched movie per pipeline run. Aggregated review scores.

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

## Scheduling with GitHub Actions

The pipeline runs automatically via `.github/workflows/ingest.yml`:

| Schedule | Mode | What runs |
|---|---|---|
| Daily, 06:00 UTC | temporal | TMDB popularity snapshot + OMDb score batch |
| Weekly (Sunday), 05:00 UTC | `--tmdb-static` | TMDB catalogue, details, keywords only |
| Manual dispatch | configurable | Any mode with custom `max_pages` and `omdb_batch_size` |

> The weekly job intentionally omits `omdb_static` to avoid consuming the daily OMDb quota. Run `--static` manually when you want to refresh OMDb metadata for the full catalogue.

### GitHub Actions secrets required

Add these in **Settings → Secrets and variables → Actions**:

| Secret | Description |
|---|---|
| `MOTHERDUCK_TOKEN` | MotherDuck personal access token |
| `TMDB_API_KEY` | TMDB API key |
| `OMDB_API_KEY` | OMDb API key |

### MotherDuck (production destination)

GitHub Actions writes to [MotherDuck](https://motherduck.com/) instead of a local DuckDB file. To use MotherDuck locally, add to `.env`:

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
- MotherDuck account (for scheduled/production runs)
