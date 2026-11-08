"""Dagster jobs and schedules for the horror movie warehouse chain.

Jobs select the dlt/dbt asset groups produced by the components in this
`defs/` folder. Cadences follow the pipeline design in the root README:

- daily temporal snapshot (TMDB popularity, OMDb scores, LLM analysis)
- weekly static refresh (TMDB catalogue/details/keywords)
"""

from __future__ import annotations

import dagster

from ingestion.defs.dbt.config import IS_PROD

DEFAULT_SCHEDULE_STATUS = (
    dagster.DefaultScheduleStatus.RUNNING
    if IS_PROD
    else dagster.DefaultScheduleStatus.STOPPED
)

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

tmdb_static_ingestion_schedule = dagster.ScheduleDefinition(
    name="tmdb_static_ingestion_schedule",
    job=tmdb_static_ingestion_job,
    cron_schedule="0 5 * * 0",  # Weekly Sunday 05:00 UTC
    execution_timezone="UTC",
    default_status=DEFAULT_SCHEDULE_STATUS,
)

temporal_ingestion_schedule = dagster.ScheduleDefinition(
    name="temporal_ingestion_schedule",
    job=temporal_ingestion_job,
    cron_schedule="0 6 * * *",  # Daily 06:00 UTC
    execution_timezone="UTC",
    default_status=DEFAULT_SCHEDULE_STATUS,
)
