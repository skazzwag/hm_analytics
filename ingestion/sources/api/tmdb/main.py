"""
dlt sources for The Movie Database (TMDB) API.

Two sources handle different run cadences:

- `tmdb_static_source` — movie catalogue, full details, keywords.
  Run weekly. Paginates the discover endpoint once and shares the resulting
  movie IDs across all three resources, eliminating the 3x discover duplication
  that would occur if each resource re-paginated independently.

- `tmdb_temporal_source` — popularity and vote snapshots.
  Run daily. Uses the discover endpoint only (~25 requests for 500 movies);
  never calls ``/movie/{id}``.

Secrets
-------
Resolved from environment variables (loaded via ``.env``):

    SOURCES__TMDB__API_KEY
"""

# dlt config section: keeps SOURCES__TMDB__* env keys and the
# [sources.tmdb] config.toml section stable across the static/temporal split.
__source_name__ = "tmdb"

import time
from datetime import datetime, timezone
from typing import Iterator

import dlt
import requests
from dlt.common.typing import TDataItems

HORROR_GENRE_ID = 27
REQUEST_DELAY = 0.25  # TMDB allows ~4 requests/sec

# Fields present on /movie/{id} that are already captured in movie_popularity
_TEMPORAL_DETAIL_FIELDS = {"popularity", "vote_average", "vote_count"}


def tmdb_get(
    base_url: str,
    path: str,
    api_key: str,
    params: dict | None = None,
) -> dict:
    """
    Make a GET request to the TMDB API and apply the rate-limit delay.

    Parameters
    ----------
    base_url : str
        TMDB API base URL (e.g. ``https://api.themoviedb.org/3``).
    path : str
        Endpoint path, including leading slash (e.g. ``/discover/movie``).
    api_key : str
        TMDB API key appended as a query parameter.
    params : dict, optional
        Additional query parameters to merge into the request.

    Returns
    -------
    dict
        Parsed JSON response body.

    Raises
    ------
    requests.HTTPError
        If the API returns a non-2xx status code.
    """
    url = f"{base_url}{path}"
    all_params = {"api_key": api_key, **(params or {})}
    response = requests.get(url, params=all_params, timeout=30)
    response.raise_for_status()
    time.sleep(REQUEST_DELAY)
    return response.json()


def paginate_discover(base_url: str, api_key: str, max_pages: int) -> list[dict]:
    """
    Paginate the TMDB discover endpoint and return all results as a list.

    Called once per source invocation so that movie IDs are shared across
    multiple resources without re-hitting the API.

    Parameters
    ----------
    base_url : str
        TMDB API base URL.
    api_key : str
        TMDB API key.
    max_pages : int
        Maximum number of pages to fetch. Capped at the API-reported
        ``total_pages`` if that value is smaller.

    Returns
    -------
    list[dict]
        All movie objects returned across all fetched pages, in order.
    """
    movies: list[dict] = []
    page = 1
    while page <= max_pages:
        data = tmdb_get(
            base_url,
            "/discover/movie",
            api_key,
            params={
                "with_genres": HORROR_GENRE_ID,
                "sort_by": "popularity.desc",
                "page": page,
            },
        )
        total_pages = data.get("total_pages", 1)
        effective_max = min(max_pages, total_pages)
        movies.extend(data.get("results", []))
        page += 1
        if page > effective_max:
            break
    return movies


@dlt.source(name="tmdb_static")
def tmdb_static_source(
    api_key: str = dlt.secrets.value,
    base_url: str = dlt.config.value,
    max_pages: int = 25,
):
    """
    Static TMDB data: movie catalogue, full details, keywords.

    Paginates the discover endpoint once and shares the resulting movie IDs
    across all three resources — no duplicate API requests. Run weekly to
    capture new releases and update structural metadata.

    Writes to tables: ``movie_catalogue``, ``movie_details``, ``movie_keywords``.
    All use merge disposition (upsert on primary key).

    Parameters
    ----------
    api_key : str
        TMDB API key. Resolved from env var ``SOURCES__TMDB__API_KEY``.
    base_url : str
        TMDB API base URL. Resolved from ``.dlt/config.toml``.
    max_pages : int, optional
        Discover pages to fetch (20 movies per page). Default is 25.
    """
    movies = paginate_discover(base_url, api_key, max_pages)
    movie_ids = [m["id"] for m in movies]

    @dlt.resource(
        name="movie_catalogue",
        write_disposition="merge",
        primary_key="id",
    )
    def movie_catalogue() -> Iterator[TDataItems]:
        """Yield static fields from the discover endpoint, excluding temporal metrics."""
        for movie in movies:
            yield {k: v for k, v in movie.items() if k not in _TEMPORAL_DETAIL_FIELDS}

    @dlt.resource(
        name="movie_details",
        write_disposition="merge",
        primary_key="id",
    )
    def movie_details() -> Iterator[TDataItems]:
        """
        Yield full static details and US certification for each movie.

        Fetches ``/movie/{id}?append_to_response=release_dates``, extracts
        the US MPAA certification, flattens the genre list, and strips
        temporal metrics and deeply nested objects that do not load cleanly.
        """
        for movie_id in movie_ids:
            details = tmdb_get(
                base_url,
                f"/movie/{movie_id}",
                api_key,
                params={"append_to_response": "release_dates"},
            )

            # Extract US certification from nested release_dates
            certification = None
            release_dates_info = details.pop("release_dates", {})
            for country in release_dates_info.get("results", []):
                if country["iso_3166_1"] == "US":
                    for release in country.get("release_dates", []):
                        if release.get("certification"):
                            certification = release["certification"]
                            break
                    break

            details["us_certification"] = certification

            # Flatten genre list to comma-separated string
            genres = details.pop("genres", [])
            details["genre_names"] = ", ".join(g["name"] for g in genres)

            # Remove deeply nested fields that do not load cleanly
            for field in (
                "belongs_to_collection",
                "production_companies",
                "production_countries",
                "spoken_languages",
            ):
                details.pop(field, None)

            # Drop temporal fields — captured separately in movie_popularity
            for field in _TEMPORAL_DETAIL_FIELDS:
                details.pop(field, None)

            yield details

    @dlt.resource(
        name="movie_keywords",
        write_disposition="merge",
        primary_key=["movie_id", "keyword_id"],
    )
    def movie_keywords() -> Iterator[TDataItems]:
        """Yield normalised keyword associations (one row per movie/keyword pair)."""
        for movie_id in movie_ids:
            kw_data = tmdb_get(
                base_url,
                f"/movie/{movie_id}/keywords",
                api_key,
            )
            for kw in kw_data.get("keywords", []):
                yield {
                    "movie_id": movie_id,
                    "keyword_id": kw["id"],
                    "keyword_name": kw["name"].lower(),
                }

    return movie_catalogue, movie_details, movie_keywords


@dlt.source(name="tmdb_temporal")
def tmdb_temporal_source(
    api_key: str = dlt.secrets.value,
    base_url: str = dlt.config.value,
    max_pages: int = 25,
):
    """
    Temporal TMDB snapshot: popularity and vote metrics per movie per run.

    Uses the discover endpoint only — approximately 25 requests to cover
    500 movies. Each daily run appends a new timestamped snapshot, building
    a time series suitable for tracking popularity and rating trends.

    Writes to table: ``movie_popularity`` (append-only). Catalogue ownership
    lives with ``tmdb_static_source`` (see its ``movie_catalogue`` resource).

    Parameters
    ----------
    api_key : str
        TMDB API key. Resolved from env var ``SOURCES__TMDB__API_KEY``.
    base_url : str
        TMDB API base URL. Resolved from ``.dlt/config.toml``.
    max_pages : int, optional
        Discover pages to fetch (20 movies per page). Default is 25.
    """

    movies = paginate_discover(base_url, api_key, max_pages)

    @dlt.resource(
        name="movie_popularity",
        write_disposition="append",
        primary_key=["id", "scraped_at"],
    )
    def movie_popularity() -> Iterator[TDataItems]:
        """Yield a popularity and vote snapshot for every discovered movie."""
        scraped_at = datetime.now(timezone.utc)
        for movie in movies:
            yield {
                "id": movie["id"],
                "popularity": movie["popularity"],
                "vote_average": movie["vote_average"],
                "vote_count": movie["vote_count"],
                "scraped_at": scraped_at,
            }

    return movie_popularity
