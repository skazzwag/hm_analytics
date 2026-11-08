from __future__ import annotations

import importlib
import os
from pathlib import Path

import pytest

DBT_MANIFEST = Path("transformation/target/manifest.json")

# The full definitions load includes the dbt component, which requires the
# dbt manifest. Until `dbt parse` has run (after profiles.yml is aligned to
# the horror_analytics profile), skip rather than fail.
pytestmark = pytest.mark.skipif(
    not DBT_MANIFEST.exists(),
    reason=(
        "dbt manifest not built yet — run "
        "`uv run dbt parse --project-dir transformation --profiles-dir transformation`"
    ),
)


def _set_minimal_ingestion_env() -> None:
    """Set env vars so Dagster definitions can load without secrets."""

    os.environ.setdefault("PIPELINE_DESTINATION", "duckdb")
    os.environ.setdefault("DBT_TARGET", "dev-local")
    os.environ.setdefault("DAGSTER_ENVIRONMENT", "dev")


def test_definitions_load_exposes_ingestion_jobs_and_schedules() -> None:
    """Definitions should load and expose the ingestion jobs and schedules."""

    _set_minimal_ingestion_env()

    definitions_module = importlib.import_module("ingestion.definitions")
    definitions_obj = definitions_module.definitions()
    repository = definitions_obj.get_repository_def()

    job_names = {job.name for job in repository.get_all_jobs()}
    assert {
        "tmdb_static_ingestion_job",
        "omdb_static_ingestion_job",
        "temporal_ingestion_job",
        "dbt_job",
    }.issubset(job_names)

    schedule_names = {schedule.name for schedule in repository.schedule_defs}
    assert {
        "tmdb_static_ingestion_schedule",
        "temporal_ingestion_schedule",
    }.issubset(schedule_names)
