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
from typing import Iterator, TypedDict

import dlt
import requests
from dlt.common.typing import TDataItems

HORROR_GENRE_ID = 27
REQUEST_DELAY = 0.25  # TMDB allows ~4 requests/sec

# Temporal metrics exposed by /discover/movie. They belong to snapshot
# pipelines, not to the catalogue, and are stripped from catalogue rows.
TEMPORAL_DISCOVER_FIELDS = {"popularity", "vote_average", "vote_count"}


class TmdbQueryParams(TypedDict, total=False):
    """Query parameters for the TMDB ``/discover/movie`` endpoint."""

    with_genres: int
    sort_by: str
    page: int


class TmdbMovie(TypedDict, total=False):
    """One movie item from a TMDB ``/discover/movie`` results page.

    Temporal fields (``popularity``, ``vote_average``, ``vote_count``) are
    present in discover items but stripped before rows are yielded.
    """

    id: int
    title: str
    original_title: str
    original_language: str
    overview: str
    release_date: str
    adult: bool
    video: bool
    poster_path: str | None
    backdrop_path: str | None
    genre_ids: list[int]
    popularity: float
    vote_average: float
    vote_count: int


class TmdbDiscoverPage(TypedDict):
    """One page of TMDB ``/discover/movie`` results."""

    page: int
    results: list[TmdbMovie]
    total_pages: int


def tmdb_get(
    base_url: str,
    path: str,
    api_key: str,
    params: TmdbQueryParams | None = None,
) -> TmdbDiscoverPage:
    """
    Make a GET request to the TMDB discover endpoint and apply the
    rate-limit delay.

    Used for (and returns) the ``/discover/movie`` endpoint response only;
    the return type is therefore the discover-specific ``TmdbDiscoverPage``.

    Parameters
    ----------
    base_url : str
        TMDB API base URL (e.g. ``https://api.themoviedb.org/3``).
    path : str
        Discover endpoint path, including leading slash
        (e.g. ``/discover/movie``).
    api_key : str
        TMDB API key appended as a query parameter.
    params : TmdbQueryParams, optional
        Additional discover query parameters (``with_genres``, ``sort_by``,
        ``page``) to merge into the request.

    Returns
    -------
    TmdbDiscoverPage
        Parsed JSON response body: one page of discover results.

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


def paginate_discover(base_url: str, api_key: str, max_pages: int) -> list[TmdbMovie]:
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
    list[TmdbMovie]
        All movie objects returned across all fetched pages, in order.
    """
    movies: list[TmdbMovie] = []
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
        # TmdbDiscoverPage declares total_pages required; .get() is defensive.
        total_pages = data.get("total_pages", 1)
        effective_max = min(max_pages, total_pages)
        # TmdbDiscoverPage declares results required; .get() is defensive.
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
) -> dlt.sources.DltSource:
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

    Returns
    -------
    dlt.sources.DltSource
        The ``tmdb_catalogue`` source with its ``movie_catalogue`` resource.
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
