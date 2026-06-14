"""
Horror movie ingestion pipeline — production runner.

Two pipeline cadences:

Static (run weekly, ``--static`` flag):
    TMDB: discover all movies, fetch full details and keywords.
    OMDb: fetch static metadata (cast, crew, plot, MPAA rating).

Temporal (run daily, default behaviour):
    TMDB: discover endpoint only — popularity and vote snapshots.
    OMDb: rotating batch of score snapshots (IMDb, RT, Metacritic).
          Advances a cursor through the movie list so the full corpus
          is covered across multiple days within the 1,000 req/day limit.

Usage
-----
Run from the repo root so that both Python imports and dlt config resolution
(which uses cwd to locate ``.dlt/``) work correctly::

    uv run run-ingestion                        # temporal (daily default)
    uv run run-ingestion --static               # static pipelines only
    uv run run-ingestion --static --temporal    # everything (first-time setup)
    uv run run-ingestion --max-pages 5          # limit discover pages
    uv run run-ingestion --omdb-batch-size 400  # smaller OMDb batch

Destination
-----------
Defaults to a local DuckDB file (``horror_movies.duckdb``). Set the
``PIPELINE_DESTINATION`` environment variable to ``motherduck`` to write
to MotherDuck, which also requires ``DESTINATION__MOTHERDUCK__CREDENTIALS``
in the environment.

Secrets (resolved from ``.env``)
---------------------------------
    SOURCES__TMDB__API_KEY
    SOURCES__OMDB__API_KEY
    DESTINATION__MOTHERDUCK__CREDENTIALS  (MotherDuck only)
"""

import argparse
import logging
import os

import dlt
from dotenv import load_dotenv

from ingestion.sources.movie_analysis import run_movie_analysis_pipeline
from ingestion.sources.omdb import omdb_static_source, omdb_temporal_source
from ingestion.sources.tmdb import tmdb_static_source, tmdb_temporal_source

load_dotenv()

PIPELINE_NAME = "horror_movies"
DATASET_NAME = "raw"
DESTINATION = os.getenv("PIPELINE_DESTINATION", "duckdb")

logger = logging.getLogger(__name__)


def _pipeline() -> dlt.Pipeline:
    """
    Create a dlt pipeline using the configured destination.

    Returns
    -------
    dlt.Pipeline
        Pipeline instance writing to ``DESTINATION`` (default: ``duckdb``).
    """
    return dlt.pipeline(
        pipeline_name=PIPELINE_NAME,
        destination=DESTINATION,
        dataset_name=DATASET_NAME,
    )


def _get_movies() -> list[dict]:
    """
    Read the movie catalogue from the pipeline destination.

    Used to provide the movie list to OMDb sources. Queries are issued
    via dlt's SQL client, which works for both local DuckDB and MotherDuck.
    Results are ordered by ``id`` to keep the OMDb temporal cursor stable.

    Returns
    -------
    list[dict]
        Records from ``movie_catalogue`` with keys ``id``, ``title``,
        ``original_title``, and ``release_date``.
    """
    pipeline = _pipeline()
    with pipeline.sql_client() as client:
        table = client.make_qualified_table_name("movie_catalogue")
        with client.execute_query(
            f"SELECT id, title, original_title, release_date FROM {table} ORDER BY id"
        ) as cursor:
            cols = [d[0] for d in cursor.description]
            return [dict(zip(cols, row)) for row in cursor.fetchall()]


def run_tmdb_static(max_pages: int) -> None:
    """
    Run the TMDB static pipeline.

    Fetches the movie catalogue, full details, and keywords. Paginates the
    discover endpoint once and shares IDs across all three resources.

    Parameters
    ----------
    max_pages : int
        Maximum number of discover pages to fetch (20 movies per page).
    """
    logger.info("Running TMDB static pipeline (max_pages=%d)...", max_pages)
    load_info = _pipeline().run(tmdb_static_source(max_pages=max_pages))
    logger.info("TMDB static complete: %s", load_info)


def run_tmdb_temporal(max_pages: int) -> None:
    """
    Run the TMDB temporal pipeline.

    Fetches only the discover endpoint and appends a popularity/vote snapshot.
    Approximately ``max_pages`` API requests.

    Parameters
    ----------
    max_pages : int
        Maximum number of discover pages to fetch (20 movies per page).
    """
    logger.info("Running TMDB temporal pipeline (max_pages=%d)...", max_pages)
    load_info = _pipeline().run(tmdb_temporal_source(max_pages=max_pages))
    logger.info("TMDB temporal complete: %s", load_info)


def run_omdb_static() -> None:
    """
    Run the OMDb static pipeline.

    Reads the full movie catalogue and fetches static metadata (cast, crew,
    plot, MPAA rating) for every movie. Uses one OMDb request per movie —
    run selectively to stay within the 1,000 requests/day free tier.
    """
    movies = _get_movies()
    logger.info("Running OMDb static pipeline (%d movies)...", len(movies))
    load_info = _pipeline().run(omdb_static_source().omdb_metadata(movies=movies))
    logger.info("OMDb static complete: %s", load_info)


def run_omdb_temporal(batch_size: int) -> None:
    """
    Run the OMDb temporal pipeline.

    Reads the full movie catalogue and processes a batch of ``batch_size``
    movies starting from a persistent cursor. The cursor advances each run
    and resets to 0 after the full list has been covered, cycling through
    the corpus over multiple days.

    Parameters
    ----------
    batch_size : int
        Number of movies to score per run. Keep at or below ~900 to stay
        within OMDb's 1,000 requests/day free tier.
    """
    movies = _get_movies()
    logger.info(
        "Running OMDb temporal pipeline (%d movies, batch_size=%d)...",
        len(movies),
        batch_size,
    )
    load_info = _pipeline().run(
        omdb_temporal_source(batch_size=batch_size).omdb_scores(movies=movies)
    )
    logger.info("OMDb temporal complete: %s", load_info)


def main() -> None:
    """
    Parse CLI arguments and dispatch to the appropriate pipeline functions.

    Defaults to the temporal pipelines when neither ``--static`` nor
    ``--temporal`` is specified, matching the expected daily schedule behaviour.
    """
    parser = argparse.ArgumentParser(
        description="Run the horror movie ingestion pipeline.",
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog="""
            examples:
            uv run run-ingestion                        daily temporal run (default)
            uv run run-ingestion --static               weekly static run
            uv run run-ingestion --static --temporal    full run (first-time setup)
        """,
    )
    parser.add_argument(
        "--analysis",
        action="store_true",
        help="Run movie analysis pipeline.",
    )
    parser.add_argument(
        "--static",
        action="store_true",
        help="Run static pipelines: TMDB details/keywords + OMDb metadata.",
    )
    parser.add_argument(
        "--temporal",
        action="store_true",
        help="Run temporal pipelines: TMDB popularity snapshot + OMDb score batch.",
    )
    parser.add_argument(
        "--max-pages",
        type=int,
        default=25,
        metavar="N",
        help="Max TMDB discover pages to fetch (20 movies/page). Default: 25.",
    )
    parser.add_argument(
        "--omdb-batch-size",
        type=int,
        default=800,
        metavar="N",
        help="Movies to score per OMDb temporal run (max ~900 for free tier). Default: 800.",
    )
    args = parser.parse_args()

    logging.basicConfig(
        level=logging.INFO,
        format="%(asctime)s %(levelname)s %(name)s — %(message)s",
    )

    if args.static:
        run_tmdb_static(max_pages=args.max_pages)
        run_omdb_static()

    if args.temporal:
        run_tmdb_temporal(max_pages=args.max_pages)
        run_omdb_temporal(batch_size=args.omdb_batch_size)

    # Run analysis pipeline after tmdb/omdb pipelines if triggered
    if args.analysis:
        run_movie_analysis_pipeline()

if __name__ == "__main__":
    main()
