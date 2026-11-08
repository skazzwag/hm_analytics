"""dlt loads for the OMDb sources (static and temporal)."""

import os

import dlt

from ingestion.sources.api.omdb.main import omdb_static_source, omdb_temporal_source

_DESTINATION = os.getenv("PIPELINE_DESTINATION", "duckdb")

omdb_static_load_source = omdb_static_source()
omdb_static_pipeline = dlt.pipeline(
    pipeline_name="horror_movies",
    dataset_name="raw",
    destination=_DESTINATION,
)

omdb_temporal_load_source = omdb_temporal_source()
omdb_temporal_pipeline = dlt.pipeline(
    pipeline_name="horror_movies",
    dataset_name="raw",
    destination=_DESTINATION,
)
