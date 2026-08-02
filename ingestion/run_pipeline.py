import argparse
import logging
import os

import dlt

from ingestion.sources.movie_analysis import run_movie_analysis_pipeline
from ingestion.sources.omdb import omdb_static_source, omdb_temporal_source
from ingestion.sources.tmdb import tmdb_static_source, tmdb_temporal_source

PIPELINE_NAME = "horror_movies"
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
        pipeline_name=PIPELINE_NAME,
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


def run_tmdb_pipeline(max_pages: int) -> None:
    """
    Run the TMDB ingestion pipeline.

    Fetches the movie catalogue, full details, and keywords. Paginates the
    discover endpoint once and shares IDs across all three resources.

    Parameters
    ----------
    max_pages : int
        Maximum number of discover pages to fetch (20 movies per page).
    """
    logger.info("Running TMDB static pipeline (max_pages=%d)...", max_pages)
    load_info = dlt.pipeline(
        pipeline_name=PIPELINE_NAME,
        destination=DESTINATION,
        dataset_name=DATASET_NAME,
    ).run(tmdb_static_source(max_pages=max_pages))
    logger.info("TMDB static complete: %s", load_info)


def run_omdb_pipeline() -> None:
    """
    Run the OMDb ingestion pipeline.

    Reads the full movie catalogue and fetches static metadata (cast, crew,
    plot, MPAA rating) for every movie. Uses one OMDb request per movie —
    run selectively to stay within the 1,000 requests/day free tier.
    """
    movies = get_movies()
    logger.info("Running OMDb static pipeline (%d movies)...", len(movies))
    load_info = dlt.pipeline(
        pipeline_name=PIPELINE_NAME,
        destination=DESTINATION,
        dataset_name=DATASET_NAME,
    ).run(omdb_static_source().omdb_metadata(movies=movies))
    logger.info("OMDb static complete: %s", load_info)


def main() -> None:
    """
    Parse CLI arguments and dispatch to the appropriate pipeline functions.

    Defaults to the temporal pipelines when neither ``--static`` nor
    ``--temporal`` is specified, matching the expected daily schedule behaviour.
    """
    parser = argparse.ArgumentParser(
        description="Run the horror movie ingestion pipeline.",
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

    run_tmdb_pipeline(max_pages=args.max_pages)
    run_omdb_pipeline()
    run_movie_analysis_pipeline()


if __name__ == "__main__":
    main()
