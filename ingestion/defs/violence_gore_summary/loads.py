"""dlt loads for the violence/gore summary source."""

import os

import dlt

from ingestion.sources.api.violence_gore_summary.main import (
    violence_gore_summary_source,
)

_DESTINATION = os.getenv("PIPELINE_DESTINATION", "duckdb")

violence_gore_summary_load_source = violence_gore_summary_source()
violence_gore_summary_pipeline = dlt.pipeline(
    pipeline_name="violence_gore_summary",
    dataset_name="raw",
    destination=_DESTINATION,
)
