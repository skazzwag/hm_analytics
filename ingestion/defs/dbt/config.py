"""Shared dbt configuration derived from environment variables."""

from __future__ import annotations

import os
from pathlib import Path

DBT_PROJECT_DIR = Path(__file__).resolve().parents[3] / "transformation"

DAGSTER_ENVIRONMENT = os.getenv("DAGSTER_ENVIRONMENT", "dev")

IS_PROD = DAGSTER_ENVIRONMENT == "prod"

DBT_TARGET = os.getenv("DBT_TARGET", "dev-local")
