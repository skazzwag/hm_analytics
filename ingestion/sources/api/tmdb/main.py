"""
dlt source for The Movie Database (TMDB) movie catalogue.

Catalogue-only source: it feeds the ``movie_catalogue`` table that serves as
the join spine and runtime dependency of the downstream ``box_office`` and
``violence_gore_summary`` pipelines. Popularity snapshots, full details and
keywords resources were dropped in the purpose-based restructure (plan
2026-11-09 v2, superseding ADR 0001).

Secrets
-------
Resolved from environment variables (loaded via ``.env``):

    SOURCES__TMDB__API_KEY
"""

# dlt config section: keeps SOURCES__TMDB__* env keys and the
# [sources.tmdb] config.toml section stable across source renames.
__source_name__ = "tmdb"

import time
from typing import Iterator

import dlt
import requests
from dlt.common.typing import TDataItems

HORROR_GENRE_ID = 27
REQUEST_DELAY = 0.25  # TMDB allows ~4 requests/sec

# Temporal metrics exposed by /discover/movie. They belong to snapshot
# pipelines, not to the catalogue, and are stripped from catalogue rows.
TEMPORAL_DISCOVER_FIELDS = {"popularity", "vote_average", "vote_count"}


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

    Called once per pipeline run (from inside the resource body) so no
    HTTP request happens at source-instantiation or definitions-load time.

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


@dlt.source(name="tmdb_catalogue")
def tmdb_catalogue_source(
    api_key: str = dlt.secrets.value,
    base_url: str = dlt.config.value,
    max_pages: int = 25,
):
    """
    TMDB movie catalogue: static fields from the discover endpoint.

    Paginates the discover endpoint once per pipeline run and yields one
    catalogue row per movie, with temporal metrics stripped. Run manually
    to refresh the join spine before the downstream box-office and
    violence/gore pipelines.

    Writes to table: ``movie_catalogue`` (merge disposition, upsert on
    primary key ``id``).

    Parameters
    ----------
    api_key : str
        TMDB API key. Resolved from env var ``SOURCES__TMDB__API_KEY``.
    base_url : str
        TMDB API base URL. Resolved from ``.dlt/config.toml``.
    max_pages : int, optional
        Discover pages to fetch (20 movies per page). Default is 25.
    """

    @dlt.resource(
        name="movie_catalogue",
        write_disposition="merge",
        primary_key="id",
    )
    def movie_catalogue() -> Iterator[TDataItems]:
        """Yield static fields from the discover endpoint, excluding temporal metrics."""
        movies = paginate_discover(base_url, api_key, max_pages)
        for movie in movies:
            yield {k: v for k, v in movie.items() if k not in TEMPORAL_DISCOVER_FIELDS}

    return movie_catalogue
