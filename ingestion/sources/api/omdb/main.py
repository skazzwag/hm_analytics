"""
dlt source for the Open Movie Database (OMDb) box-office snapshots.

One source: ``box_office_source`` appends a full-catalogue snapshot of
IMDb rating, Rotten Tomatoes, Metacritic and box-office values on every
run. There is no completion or cursor logic — each run mirrors the current
OMDb state for all catalogue films, and ``scraped_at`` records when each
snapshot was taken. Final "latest snapshot per film" semantics are derived
downstream in dbt.

Secrets
-------
Resolved from environment variables (loaded via ``.env``):

    SOURCES__OMDB__API_KEY
"""

# dlt config section: keeps SOURCES__OMDB__* env keys and the
# [sources.omdb] config.toml section stable across source renames.
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

    Shared helper for the runtime-dependent sources (``box_office``,
    ``violence_gore_summary``) when no explicit movie list is supplied,
    e.g. when they run under Dagster. Queries are issued via dlt's SQL
    client, which works for both local DuckDB and MotherDuck. Results are
    ordered by ``id`` so downstream consumption is deterministic.

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
        Query parameter dict suitable for passing to ``omdb_get``.
    """
    params: dict = {
        "t": movie.get("title") or movie.get("original_title", ""),
        "type": "movie",
    }
    release_date = movie.get("release_date", "")
    if release_date:
        params["y"] = release_date[:4]
    return params


@dlt.source(name="box_office")
def box_office_source(
    api_key: str = dlt.secrets.value,
    base_url: str = dlt.config.value,
):
    """
    OMDb box-office snapshot source: full catalogue every run.

    Fetches one OMDb lookup per catalogue film and appends a timestamped
    snapshot row per film. A full run costs approximately one request per
    catalogue movie (~1,061), roughly one day's 1,000/day free tier quota,
    so runs are manual.

    Writes to table: ``box_office_snapshots`` (append-only, keyed on
    ``imdb_id`` + ``scraped_at``).

    Parameters
    ----------
    api_key : str
        OMDb API key. Resolved from env var ``SOURCES__OMDB__API_KEY``.
    base_url : str
        OMDb API base URL. Resolved from ``.dlt/config.toml``.
    """

    @dlt.resource(
        name="box_office_snapshots",
        write_disposition="append",
        primary_key=["imdb_id", "scraped_at"],
    )
    def box_office_snapshots(movies: list[dict] | None = None) -> Iterator[TDataItems]:
        """
        Yield a box-office snapshot for every movie in the catalogue.

        Parameters
        ----------
        movies : list[dict], optional
            Full movie list sorted by ``id``, typically from
            ``movie_catalogue``. Read from the pipeline destination when
            omitted.
        """
        if movies is None:
            movies = read_movie_catalogue()

        scraped_at = datetime.now(timezone.utc)

        for movie in movies:
            data = omdb_get(base_url, api_key, lookup_params(movie))
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

    return box_office_snapshots
