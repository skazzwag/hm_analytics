"""Tests for the dlt load modules wired into Dagster components.

These import the load modules directly so they can run without a dbt
manifest (the full definitions load in test_dagster_definitions.py needs
`dbt parse` to have produced transformation/target/manifest.json).
"""

from __future__ import annotations

import importlib


def test_tmdb_loads_expose_source_and_pipeline() -> None:
    """The TMDB component should expose static and temporal loads."""

    module = importlib.import_module("ingestion.defs.tmdb.loads")
    assert module.tmdb_static_load_source is not None
    assert module.tmdb_static_pipeline is not None
    assert module.tmdb_temporal_load_source is not None
    assert module.tmdb_temporal_pipeline is not None


def test_omdb_loads_expose_source_and_pipeline() -> None:
    """The OMDb component should expose static and temporal loads."""

    module = importlib.import_module("ingestion.defs.omdb.loads")
    assert module.omdb_static_load_source is not None
    assert module.omdb_static_pipeline is not None
    assert module.omdb_temporal_load_source is not None
    assert module.omdb_temporal_pipeline is not None


def test_movie_analysis_load_exposes_source_and_pipeline() -> None:
    """The movie analysis component should expose its load."""

    module = importlib.import_module("ingestion.defs.movie_analysis.loads")
    assert module.movie_analysis_load_source is not None
    assert module.movie_analysis_pipeline is not None
