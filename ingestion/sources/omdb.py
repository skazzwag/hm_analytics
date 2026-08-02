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

import time
from datetime import datetime, timezone
from typing import Iterator

import dlt
import requests
from dlt.common.typing import TDataItems

REQUEST_DELAY = 0.5  # OMDb free tier: 1,000 req/day — be conservative


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


@dlt.source(name="omdb")
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
    def omdb_metadata(movies: list[dict]) -> Iterator[TDataItems]:
        """
        Yield static OMDb metadata for each movie.

        Movies not found on OMDb (``Response: False``) are silently skipped.

        Parameters
        ----------
        movies : list[dict]
            Movie records from ``movie_catalogue``, each containing at least
            ``id``, ``title``, and ``release_date``.
        """
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
