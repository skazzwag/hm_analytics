"""Tests for the dlt load modules wired into Dagster components.

These import the load modules directly so they can run without a dbt
manifest (the full definitions load in test_dagster_definitions.py needs
`dbt parse` to have produced transformation/target/manifest.json).
"""

from __future__ import annotations

import importlib
import os
from unittest import mock

# Dummy credentials so module-level dlt source instantiation resolves without
# real secrets; no API calls are made by importing the load modules.
os.environ.setdefault("SOURCES__TMDB__TMDB_CATALOGUE__API_KEY", "test-key")
os.environ.setdefault("SOURCES__OMDB__BOX_OFFICE__API_KEY", "test-key")
os.environ.setdefault("SOURCES__MISTRAL__VIOLENCE_GORE_SUMMARY__API_KEY", "test-key")
os.environ.setdefault(
    "SOURCES__MISTRAL__VIOLENCE_GORE_SUMMARY__BASE_URL", "https://api.mistral.ai/v1"
)


def _import_loads(module_name: str) -> object:
    """Import a load module, patching the TMDB discover fetch as a safety net."""

    with mock.patch(
        "ingestion.sources.api.tmdb.main.paginate_discover",
        return_value=[],
    ):
        return importlib.import_module(module_name)


def test_tmdb_loads_expose_source_and_pipeline() -> None:
    """The TMDB component should expose its catalogue load."""

    module = _import_loads("ingestion.defs.tmdb.loads")
    assert module.tmdb_catalogue_load_source is not None
    assert module.tmdb_catalogue_pipeline is not None


def test_omdb_loads_expose_source_and_pipeline() -> None:
    """The OMDb component should expose its box office load."""

    module = importlib.import_module("ingestion.defs.omdb.loads")
    assert module.box_office_load_source is not None
    assert module.box_office_pipeline is not None


def test_violence_gore_summary_load_exposes_source_and_pipeline() -> None:
    """The violence/gore summary component should expose its load."""

    module = importlib.import_module("ingestion.defs.violence_gore_summary.loads")
    assert module.violence_gore_summary_load_source is not None
    assert module.violence_gore_summary_pipeline is not None
