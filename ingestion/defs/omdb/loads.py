"""dlt loads for the OMDb box-office source."""

import os

import dlt

from ingestion.sources.api.omdb.main import box_office_source

_DESTINATION = os.getenv("PIPELINE_DESTINATION", "duckdb")

box_office_load_source = box_office_source()
box_office_pipeline = dlt.pipeline(
    pipeline_name="box_office",
    dataset_name="raw",
    destination=_DESTINATION,
)
