"""dlt load for the Anthropic violence/gore analysis source."""

import os

import dlt

from ingestion.sources.api.movie_analysis.main import movie_analysis_source

_DESTINATION = os.getenv("PIPELINE_DESTINATION", "duckdb")

movie_analysis_load_source = movie_analysis_source()
movie_analysis_pipeline = dlt.pipeline(
    pipeline_name="violence_gore_analysis",
    dataset_name="raw",
    destination=_DESTINATION,
)
