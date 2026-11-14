"""dlt loads for the TMDB catalogue source."""

import os

import dlt

from ingestion.sources.api.tmdb.main import tmdb_catalogue_source

_DESTINATION = os.getenv("PIPELINE_DESTINATION", "duckdb")

tmdb_catalogue_load_source = tmdb_catalogue_source()
tmdb_catalogue_pipeline = dlt.pipeline(
    pipeline_name="tmdb_catalogue",
    dataset_name="raw",
    destination=_DESTINATION,
)
