"""
Production runner for the horror movie ingestion pipelines.

Thin CLI wrapper around the dlt sources for manual runs without Dagster.
The Dagster asset jobs in ``ingestion/defs/jobs.py`` run the same sources
via manual triggers.

Pipelines (in dependency order):

1. ``tmdb_catalogue`` — TMDB discover catalogue feeding ``movie_catalogue``.
2. ``box_office`` — OMDb snapshot of ratings/box office for the catalogue.
3. ``violence_gore_summary`` — Mistral web-search summaries for the catalogue.

The two downstream pipelines read ``movie_catalogue`` from the pipeline
destination at runtime, so run ``tmdb_catalogue`` first on a fresh database.

Usage::

    uv run python -m ingestion.run_pipeline                # all three
    uv run python -m ingestion.run_pipeline --tmdb         # catalogue only
    uv run python -m ingestion.run_pipeline --box-office --violence-gore
"""

import argparse
import logging
import os

import dlt

from ingestion.sources.api.omdb.main import box_office_source
from ingestion.sources.api.tmdb.main import tmdb_catalogue_source
from ingestion.sources.api.violence_gore_summary.main import violence_gore_summary_source

DATASET_NAME = "raw"
DESTINATION = os.getenv("PIPELINE_DESTINATION", "duckdb")

logger = logging.getLogger(__name__)


def run_tmdb_catalogue(max_pages: int) -> None:
    """
    Run the TMDB catalogue pipeline.

    Fetches static fields for the horror catalogue from the discover
    endpoint and merges them into ``movie_catalogue``.

    Parameters
    ----------
    max_pages : int
        Maximum number of discover pages to fetch (20 movies per page).
    """
    logger.info("Running TMDB catalogue pipeline (max_pages=%d)...", max_pages)
    load_info = dlt.pipeline(
        pipeline_name="tmdb_catalogue",
        destination=DESTINATION,
        dataset_name=DATASET_NAME,
    ).run(tmdb_catalogue_source(max_pages=max_pages))
    logger.info("TMDB catalogue complete: %s", load_info)


def run_box_office() -> None:
    """
    Run the OMDb box-office snapshot pipeline.

    Reads the full movie catalogue from the pipeline destination and
    fetches IMDb rating, Rotten Tomatoes, Metacritic and box-office
    values for every movie. Uses one OMDb request per movie — run
    selectively to stay within the 1,000 requests/day free tier.
    """
    logger.info("Running box-office pipeline...")
    load_info = dlt.pipeline(
        pipeline_name="box_office",
        destination=DESTINATION,
        dataset_name=DATASET_NAME,
    ).run(box_office_source())
    logger.info("Box-office complete: %s", load_info)


def run_violence_gore_summary() -> None:
    """
    Run the violence/gore summary pipeline.

    Reads the movie catalogue from the pipeline destination and requests
    a concise violence/gore summary per movie from the Mistral
    Conversations API, appending the raw responses.
    """
    logger.info("Running violence/gore summary pipeline...")
    load_info = dlt.pipeline(
        pipeline_name="violence_gore_summary",
        destination=DESTINATION,
        dataset_name=DATASET_NAME,
    ).run(violence_gore_summary_source())
    logger.info("Violence/gore summary complete: %s", load_info)


def main() -> None:
    """
    Parse CLI arguments and dispatch to the appropriate pipeline functions.

    Runs all three pipelines when no per-pipeline flag is given; otherwise
    runs only the selected ones, in dependency order.
    """
    parser = argparse.ArgumentParser(
        description=(
            "Run the horror movie ingestion pipelines. Defaults to all "
            "three; per-pipeline flags select a subset."
        ),
    )
    parser.add_argument(
        "--tmdb",
        action="store_true",
        help="Run the TMDB catalogue pipeline (movie_catalogue).",
    )
    parser.add_argument(
        "--box-office",
        action="store_true",
        help="Run the OMDb box-office snapshot pipeline (~1 request/movie).",
    )
    parser.add_argument(
        "--violence-gore",
        action="store_true",
        help="Run the Mistral violence/gore summary pipeline (~1 request/movie).",
    )
    parser.add_argument(
        "--max-pages",
        type=int,
        default=25,
        metavar="N",
        help="Max TMDB discover pages to fetch (20 movies/page). Default: 25.",
    )
    args = parser.parse_args()

    logging.basicConfig(
        level=logging.INFO,
        format="%(asctime)s %(levelname)s %(name)s — %(message)s",
    )

    run_all = not (args.tmdb or args.box_office or args.violence_gore)

    if run_all or args.tmdb:
        run_tmdb_catalogue(max_pages=args.max_pages)
    if run_all or args.box_office:
        run_box_office()
    if run_all or args.violence_gore:
        run_violence_gore_summary()


if __name__ == "__main__":
    main()
