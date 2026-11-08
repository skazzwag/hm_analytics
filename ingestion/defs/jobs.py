"""Dagster asset jobs for the horror movie warehouse chain.

Jobs are manual-trigger only; there are no schedules. Base jobs run dlt loads
with the dispositions hardcoded in each source. Refresh jobs carry the
``dlt/write_disposition`` run tag so the ``RefreshableDltLoadCollectionComponent``
overrides every selected dlt load to ``replace``.
"""

from __future__ import annotations

import dagster

from ingestion.components import WRITE_DISPOSITION_TAG

tmdb_static_ingestion_job = dagster.define_asset_job(
    name="tmdb_static_ingestion_job",
    selection=dagster.AssetSelection.groups("tmdb_static"),
)

omdb_static_ingestion_job = dagster.define_asset_job(
    name="omdb_static_ingestion_job",
    selection=dagster.AssetSelection.groups("omdb_static"),
)

temporal_ingestion_job = dagster.define_asset_job(
    name="temporal_ingestion_job",
    selection=dagster.AssetSelection.groups(
        "tmdb_temporal",
        "omdb_temporal",
        "movie_analysis",
    ),
)

dbt_job = dagster.define_asset_job(
    name="dbt_job",
    selection=dagster.AssetSelection.groups("dbt"),
)

tmdb_static_refresh_job = dagster.define_asset_job(
    name="tmdb_static_refresh_job",
    selection=dagster.AssetSelection.groups("tmdb_static"),
    tags={WRITE_DISPOSITION_TAG: "replace"},
)

omdb_static_refresh_job = dagster.define_asset_job(
    name="omdb_static_refresh_job",
    selection=dagster.AssetSelection.groups("omdb_static"),
    tags={WRITE_DISPOSITION_TAG: "replace"},
)

temporal_refresh_job = dagster.define_asset_job(
    name="temporal_refresh_job",
    selection=dagster.AssetSelection.groups(
        "tmdb_temporal",
        "omdb_temporal",
        "movie_analysis",
    ),
    tags={WRITE_DISPOSITION_TAG: "replace"},
)
