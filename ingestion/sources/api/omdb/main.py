"""
dlt sources for the Open Movie Database (OMDb) API.

Two sources handle different run cadences:

- `omdb_static_source` — cast, crew, plot, awards, MPAA rating.
  Run weekly alongside the TMDB static pipeline.

- `omdb_temporal_source` — IMDb rating, Rotten Tomatoes, Metacritic scores.
  Run daily. Uses a dlt resource state cursor to advance through the movie
  list in configurable batches, cycling back to the start when complete.
  This keeps each run well within the 1,000 requests/day free tier limit.

Secrets
-------
Resolved from environment variables (loaded via ``.env``):

    SOURCES__OMDB__API_KEY
"""

# dlt config section: keeps SOURCES__OMDB__* env keys and the
# [sources.omdb] config.toml section stable across the static/temporal split.
__source_name__ = "omdb"

import time
from datetime import datetime, timezone
from typing import Iterator

import dlt
import requests
from dlt.common.typing import TDataItems

REQUEST_DELAY = 0.5  # OMDb free tier: 1,000 req/day — be conservative


def read_movie_catalogue() -> list[dict]:
    """
    Read the movie catalogue from the pipeline destination.

    Used by OMDb resources when no explicit movie list is supplied, e.g.
    when the source runs under Dagster. Queries are issued via dlt's SQL
    client, which works for both local DuckDB and MotherDuck. Results are
    ordered by ``id`` to keep the OMDb temporal cursor stable.

    Returns
    -------
    list[dict]
        Records from ``movie_catalogue`` with keys ``id``, ``title``,
        ``original_title``, and ``release_date``.
    """
    pipeline = dlt.current.pipeline()
    with pipeline.sql_client() as client:
        table = client.make_qualified_table_name("movie_catalogue")
        with client.execute_query(
            f"SELECT id, title, original_title, release_date FROM {table} ORDER BY id"
        ) as cursor:
            columns = [column[0] for column in cursor.description]
            return [dict(zip(columns, row)) for row in cursor.fetchall()]


def omdb_get(base_url: str, api_key: str, params: dict) -> dict:
    """
    Make a GET request to the OMDb API and apply the rate-limit delay.

    Parameters
    ----------
    base_url : str
        OMDb API base URL (e.g. ``http://www.omdbapi.com/``).
    api_key : str
        OMDb API key appended as the ``apikey`` query parameter.
    params : dict
        Additional query parameters (e.g. title lookup, year).

    Returns
    -------
    dict
        Parsed JSON response body. Contains ``{"Response": "False"}`` when
        the movie is not found rather than raising an HTTP error.

    Raises
    ------
    requests.HTTPError
        If the API returns a non-2xx status code.
    """
    all_params = {"apikey": api_key, **params}
    response = requests.get(base_url, params=all_params, timeout=30)
    response.raise_for_status()
    time.sleep(REQUEST_DELAY)
    return response.json()


def lookup_params(movie: dict) -> dict:
    """
    Build OMDb title-lookup query parameters from a movie dict.

    Prefers ``title`` over ``original_title``. Includes release year when
    available to disambiguate remakes and sequels.

    Parameters
    ----------
    movie : dict
        Movie record with at least ``title`` or ``original_title``, and
        optionally ``release_date`` (ISO 8601 date string).

    Returns
    -------
    dict
        Query parameter dict suitable for passing to ``_omdb_get``.
    """
    params: dict = {
        "t": movie.get("title") or movie.get("original_title", ""),
        "type": "movie",
    }
    release_date = movie.get("release_date", "")
    if release_date:
        params["y"] = release_date[:4]
    return params


@dlt.source(name="omdb_static")
def omdb_static_source(
    api_key: str = dlt.secrets.value,
    base_url: str = dlt.config.value,
):
    """
    Static OMDb metadata: cast, crew, plot, awards, MPAA rating.

    Run weekly alongside the TMDB static pipeline. Uses merge disposition
    so re-runs safely update any changed values without duplicating rows.

    Writes to table: ``omdb_metadata``. Merge on ``imdb_id``.

    Parameters
    ----------
    api_key : str
        OMDb API key. Resolved from env var ``SOURCES__OMDB__API_KEY``.
    base_url : str
        OMDb API base URL. Resolved from ``.dlt/config.toml``.
    """

    @dlt.resource(
        name="omdb_metadata",
        write_disposition="merge",
        primary_key="imdb_id",
    )
    def omdb_metadata(movies: list[dict] | None = None) -> Iterator[TDataItems]:
        """
        Yield static OMDb metadata for each movie.

        Movies not found on OMDb (``Response: False``) are silently skipped.

        Parameters
        ----------
        movies : list[dict], optional
            Movie records from ``movie_catalogue``, each containing at least
            ``id``, ``title``, and ``release_date``. Read from the pipeline
            destination when omitted.
        """
        if movies is None:
            movies = read_movie_catalogue()
        for movie in movies:
            data = omdb_get(base_url, api_key, lookup_params(movie))
            if data.get("Response") == "False":
                continue
            yield {
                "tmdb_id": movie["id"],
                "imdb_id": data.get("imdbID"),
                "title": data.get("Title"),
                "year": data.get("Year"),
                "rated": data.get("Rated"),
                "runtime": data.get("Runtime"),
                "director": data.get("Director"),
                "writer": data.get("Writer"),
                "actors": data.get("Actors"),
                "plot": data.get("Plot"),
                "awards": data.get("Awards"),
                "dvd": data.get("DVD"),
            }

    return omdb_metadata


@dlt.source(name="omdb_temporal")
def omdb_temporal_source(
    api_key: str = dlt.secrets.value,
    base_url: str = dlt.config.value,
    batch_size: int = 800,
):
    """
    Temporal OMDb scores: IMDb rating, Rotten Tomatoes, Metacritic.

    Uses dlt resource state as a persistent cursor to process movies in
    daily batches. Each run advances the cursor by ``batch_size``, wrapping
    back to the start when the full list has been covered. This spreads the
    request load across multiple days and stays within OMDb's 1,000
    requests/day free tier.

    Writes to table: ``omdb_scores``. Append-only.

    Parameters
    ----------
    api_key : str
        OMDb API key. Resolved from env var ``SOURCES__OMDB__API_KEY``.
    base_url : str
        OMDb API base URL. Resolved from ``.dlt/config.toml``.
    batch_size : int, optional
        Number of movies to process per run. Default is 800, leaving
        headroom below the 1,000 requests/day free tier limit.

    Notes
    -----
    The ``movies`` argument passed to ``omdb_scores`` must be sorted
    consistently (e.g. by ``id``) across runs so that the integer cursor
    always refers to the same position in the list.
    """

    @dlt.resource(
        name="omdb_scores",
        write_disposition="append",
        primary_key=["imdb_id", "scraped_at"],
    )
    def omdb_scores(movies: list[dict] | None = None) -> Iterator[TDataItems]:
        """
        Yield a score snapshot for the current batch of movies.

        Reads and advances a persistent cursor stored in dlt resource state.
        The cursor resets to 0 after the full movie list has been processed.

        Parameters
        ----------
        movies : list[dict], optional
            Full movie list sorted by ``id``, typically from
            ``movie_catalogue``. Read from the pipeline destination when
            omitted.
        """
        if movies is None:
            movies = read_movie_catalogue()

        state = dlt.current.resource_state()
        cursor = state.get("cursor", 0)

        # Wrap cursor if the movie list has shrunk or a cycle just completed
        if cursor >= len(movies):
            cursor = 0

        batch = movies[cursor : cursor + batch_size]
        scraped_at = datetime.now(timezone.utc)
        processed = 0

        for movie in batch:
            data = omdb_get(base_url, api_key, lookup_params(movie))
            processed += 1
            if data.get("Response") == "False":
                continue

            ratings_list = data.get("Ratings", [])
            rt_score = next(
                (r["Value"] for r in ratings_list if r["Source"] == "Rotten Tomatoes"),
                None,
            )
            metacritic_score = next(
                (r["Value"] for r in ratings_list if r["Source"] == "Metacritic"),
                None,
            )

            yield {
                "scraped_at": scraped_at,
                "tmdb_id": movie["id"],
                "imdb_id": data.get("imdbID"),
                "imdb_rating": data.get("imdbRating"),
                "imdb_votes": data.get("imdbVotes"),
                "metascore": data.get("Metascore"),
                "rotten_tomatoes_score": rt_score,
                "metacritic_score": metacritic_score,
                "box_office": data.get("BoxOffice"),
            }

        new_cursor = cursor + processed
        state["cursor"] = new_cursor if new_cursor < len(movies) else 0

    return omdb_scores
