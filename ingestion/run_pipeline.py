"""
Production runner for the horror movie ingestion pipelines.

Thin CLI wrapper around the dlt sources for manual runs without Dagster.
The Dagster asset jobs in ``ingestion/defs/jobs.py`` run the same sources
via manual triggers.
"""

import argparse
import logging
import os

import dlt

from ingestion.sources.api.movie_analysis.main import movie_analysis_source
from ingestion.sources.api.omdb.main import omdb_static_source, omdb_temporal_source
from ingestion.sources.api.tmdb.main import tmdb_static_source, tmdb_temporal_source

DATASET_NAME = "raw"
DESTINATION = os.getenv("PIPELINE_DESTINATION", "duckdb")

logger = logging.getLogger(__name__)


def get_movies() -> list[dict]:
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
    pipeline = dlt.pipeline(
        pipeline_name="tmdb_static",
        destination=DESTINATION,
        dataset_name=DATASET_NAME,
    )
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
    load_info = dlt.pipeline(
        pipeline_name="tmdb_static",
        destination=DESTINATION,
        dataset_name=DATASET_NAME,
    ).run(tmdb_static_source(max_pages=max_pages))
    logger.info("TMDB static complete: %s", load_info)


def run_tmdb_temporal(max_pages: int) -> None:
    """
    Run the TMDB temporal pipeline.

    Appends a popularity and vote snapshot for the current horror movies.

    Parameters
    ----------
    max_pages : int
        Maximum number of discover pages to fetch (20 movies per page).
    """
    logger.info("Running TMDB temporal pipeline (max_pages=%d)...", max_pages)
    load_info = dlt.pipeline(
        pipeline_name="tmdb_temporal",
        destination=DESTINATION,
        dataset_name=DATASET_NAME,
    ).run(tmdb_temporal_source(max_pages=max_pages))
    logger.info("TMDB temporal complete: %s", load_info)


def run_omdb_static() -> None:
    """
    Run the OMDb static pipeline.

    Reads the full movie catalogue and fetches static metadata (cast, crew,
    plot, MPAA rating) for every movie. Uses one OMDb request per movie —
    run selectively to stay within the 1,000 requests/day free tier.
    """
    movies = get_movies()
    logger.info("Running OMDb static pipeline (%d movies)...", len(movies))
    load_info = dlt.pipeline(
        pipeline_name="omdb_static",
        destination=DESTINATION,
        dataset_name=DATASET_NAME,
    ).run(omdb_static_source().omdb_metadata(movies=movies))
    logger.info("OMDb static complete: %s", load_info)


def run_omdb_temporal(batch_size: int) -> None:
    """
    Run the OMDb temporal pipeline.

    Scores the next batch of movies via the persistent dlt state cursor,
    advancing one batch per run and cycling back after the full list.

    Parameters
    ----------
    batch_size : int
        Movies to score per run (max ~900 for the free tier).
    """
    movies = get_movies()
    logger.info(
        "Running OMDb temporal pipeline (%d movies, batch_size=%d)...",
        len(movies),
        batch_size,
    )
    load_info = dlt.pipeline(
        pipeline_name="omdb_temporal",
        destination=DESTINATION,
        dataset_name=DATASET_NAME,
    ).run(omdb_temporal_source(batch_size=batch_size).omdb_scores(movies=movies))
    logger.info("OMDb temporal complete: %s", load_info)


def run_movie_analysis(batch_size: int) -> None:
    """
    Run the violence/gore analysis pipeline.

    Sends unprocessed movies to the Anthropic API for a violence/gore
    assessment and appends the raw responses.

    Parameters
    ----------
    batch_size : int
        Maximum number of movies to analyze in this run.
    """
    logger.info("Running violence/gore analysis pipeline (batch_size=%d)...", batch_size)
    load_info = dlt.pipeline(
        pipeline_name="violence_gore_analysis",
        destination=DESTINATION,
        dataset_name=DATASET_NAME,
    ).run(movie_analysis_source(batch_size=batch_size))
    logger.info("Analysis pipeline complete: %s", load_info)


def main() -> None:
    """
    Parse CLI arguments and dispatch to the appropriate pipeline functions.

    Defaults to the temporal pipelines when neither ``--static`` nor
    ``--temporal`` is specified.
    """
    parser = argparse.ArgumentParser(
        description="Run the horror movie ingestion pipeline.",
    )
    parser.add_argument(
        "--static",
        action="store_true",
        help=(
            "Run the static pipelines (TMDB catalogue/details/keywords "
            "+ OMDb metadata)."
        ),
    )
    parser.add_argument(
        "--temporal",
        action="store_true",
        help=(
            "Run the temporal pipelines (TMDB popularity, OMDb scores, "
            "analysis). Default when neither flag is given."
        ),
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
    else:
        run_tmdb_temporal(max_pages=args.max_pages)
        run_omdb_temporal(batch_size=args.omdb_batch_size)
        run_movie_analysis(batch_size=300)


if __name__ == "__main__":
    main()
