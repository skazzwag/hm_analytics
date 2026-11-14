"""Dagster asset jobs for the horror movie warehouse chain.

Jobs are manual-trigger only; there are no schedules. Base jobs run dlt loads
with the dispositions hardcoded in each source. Refresh jobs carry the
``dlt/write_disposition`` run tag so the ``RefreshableDltLoadCollectionComponent``
overrides every selected dlt load to ``replace``.
"""

from __future__ import annotations

import dagster

from ingestion.components import WRITE_DISPOSITION_TAG

tmdb_catalogue_ingestion_job = dagster.define_asset_job(
    name="tmdb_catalogue_ingestion_job",
    selection=dagster.AssetSelection.groups("tmdb_catalogue"),
)

box_office_ingestion_job = dagster.define_asset_job(
    name="box_office_ingestion_job",
    selection=dagster.AssetSelection.groups("box_office"),
)

violence_gore_summary_ingestion_job = dagster.define_asset_job(
    name="violence_gore_summary_ingestion_job",
    selection=dagster.AssetSelection.groups("violence_gore_summary"),
)

dbt_job = dagster.define_asset_job(
    name="dbt_job",
    selection=dagster.AssetSelection.groups("dbt"),
)

tmdb_catalogue_refresh_job = dagster.define_asset_job(
    name="tmdb_catalogue_refresh_job",
    selection=dagster.AssetSelection.groups("tmdb_catalogue"),
    tags={WRITE_DISPOSITION_TAG: "replace"},
)

# Deliberate destructive reset (confirmed by user 2026-11-14): the replace tag
# wipes the append-only ``box_office_snapshots`` snapshot history by design.
# Use the base ``box_office_ingestion_job`` for normal refreshes.
box_office_refresh_job = dagster.define_asset_job(
    name="box_office_refresh_job",
    selection=dagster.AssetSelection.groups("box_office"),
    tags={WRITE_DISPOSITION_TAG: "replace"},
)

violence_gore_summary_refresh_job = dagster.define_asset_job(
    name="violence_gore_summary_refresh_job",
    selection=dagster.AssetSelection.groups("violence_gore_summary"),
    tags={WRITE_DISPOSITION_TAG: "replace"},
)
