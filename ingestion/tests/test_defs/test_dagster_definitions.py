from __future__ import annotations

import importlib
import os
from pathlib import Path

import dagster
import pytest
from dagster import RepositoryDefinition

from ingestion.components import WRITE_DISPOSITION_TAG

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

BASE_JOB_NAMES = {
    "tmdb_static_ingestion_job",
    "omdb_static_ingestion_job",
    "temporal_ingestion_job",
    "dbt_job",
}
REFRESH_JOB_NAMES = {
    "tmdb_static_refresh_job",
    "omdb_static_refresh_job",
    "temporal_refresh_job",
}

# The seven raw asset keys (ADR 0001, migration step 5).
RAW_ASSET_KEYS = {
    "raw/movie_catalogue",
    "raw/movie_details",
    "raw/movie_keywords",
    "raw/movie_popularity",
    "raw/omdb_metadata",
    "raw/omdb_scores",
    "raw/violence_gore_analysis",
}


def _set_minimal_ingestion_env() -> None:
    """Set env vars so Dagster definitions can load without secrets."""

    os.environ.setdefault("PIPELINE_DESTINATION", "duckdb")
    os.environ.setdefault("DBT_TARGET", "dev-local")
    os.environ.setdefault("DAGSTER_ENVIRONMENT", "dev")


def _load_repository() -> RepositoryDefinition:
    """Load the project definitions and return the repository definition."""

    _set_minimal_ingestion_env()

    definitions_module = importlib.import_module("ingestion.definitions")
    definitions_obj = definitions_module.definitions()
    return definitions_obj.get_repository_def()


def _load_definitions() -> dagster.Definitions:
    """Load the project definitions."""

    _set_minimal_ingestion_env()

    definitions_module = importlib.import_module("ingestion.definitions")
    return definitions_module.definitions()


def test_definitions_load_exposes_ingestion_jobs() -> None:
    """Definitions should expose the base jobs and their refresh variants."""

    repository = _load_repository()

    job_names = {job.name for job in repository.get_all_jobs()}
    assert BASE_JOB_NAMES | REFRESH_JOB_NAMES <= job_names


def test_definitions_load_has_no_schedules() -> None:
    """Definitions must not register any schedules (manual-trigger only)."""

    repository = _load_repository()

    assert not repository.schedule_defs


def test_refresh_jobs_carry_write_disposition_tag() -> None:
    """Refresh jobs must attach the replace write disposition run tag."""

    repository = _load_repository()
    jobs_by_name = {job.name: job for job in repository.get_all_jobs()}

    for name in REFRESH_JOB_NAMES:
        job = jobs_by_name[name]
        assert job.tags.get(WRITE_DISPOSITION_TAG) == "replace"

    for name in BASE_JOB_NAMES:
        job = jobs_by_name[name]
        assert WRITE_DISPOSITION_TAG not in job.tags


def test_raw_asset_keys_are_unique_and_complete() -> None:
    """The dlt loads must expose exactly the seven unique raw asset keys."""

    definitions_obj = _load_definitions()

    asset_keys = {
        spec.key.to_user_string()
        for asset in definitions_obj.assets
        for spec in asset.specs
    }
    assert RAW_ASSET_KEYS <= asset_keys
    raw_count = sum(
        1
        for asset in definitions_obj.assets
        for spec in asset.specs
        if spec.key.to_user_string() in RAW_ASSET_KEYS
    )
    assert raw_count == len(RAW_ASSET_KEYS)


def test_runtime_readers_depend_on_movie_catalogue() -> None:
    """omdb_temporal and movie_analysis loads must depend on raw/movie_catalogue."""

    definitions_obj = _load_definitions()

    deps_by_asset: dict[str, set[str]] = {}
    for asset in definitions_obj.assets:
        for spec in asset.specs:
            deps_by_asset[spec.key.to_user_string()] = {
                dep.asset_key.to_user_string() for dep in spec.deps
            }

    assert "raw/movie_catalogue" in deps_by_asset["raw/omdb_scores"]
    assert "raw/movie_catalogue" in deps_by_asset["raw/violence_gore_analysis"]
    assert "raw/movie_catalogue" not in deps_by_asset.get("raw/movie_popularity", set())
