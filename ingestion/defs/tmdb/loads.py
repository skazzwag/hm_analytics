"""dlt loads for the TMDB sources (static and temporal)."""

import os

import dlt

from ingestion.sources.api.tmdb.main import tmdb_static_source, tmdb_temporal_source

_DESTINATION = os.getenv("PIPELINE_DESTINATION", "duckdb")

tmdb_static_load_source = tmdb_static_source()
tmdb_static_pipeline = dlt.pipeline(
    pipeline_name="tmdb_static",
    dataset_name="raw",
    destination=_DESTINATION,
)

tmdb_temporal_load_source = tmdb_temporal_source()
tmdb_temporal_pipeline = dlt.pipeline(
    pipeline_name="tmdb_temporal",
    dataset_name="raw",
    destination=_DESTINATION,
)
