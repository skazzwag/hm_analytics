FROM python:3.13-slim-bookworm

RUN apt-get update && \
    apt-get upgrade -y && \
    apt-get install -y --no-install-recommends git && \
    apt-get clean && \
    rm -rf /var/lib/apt/lists/*

COPY --from=ghcr.io/astral-sh/uv:latest /uv /usr/local/bin/uv

ENV _DAGSTER_ROOT=/opt/dagster
ENV DAGSTER_ROOT=$_DAGSTER_ROOT/ \
    DAGSTER_HOME=$_DAGSTER_ROOT/dagster_home/ \
    DAGSTER_APP=$_DAGSTER_ROOT/app/ \
    PATH="/opt/dagster/app/.venv/bin:$PATH"

# Install dependencies in a separate directory so pyproject.toml (which contains
# [tool.dg] config) is never present in DAGSTER_HOME. If it were, dagster-webserver
# would trigger dg auto-discovery and try to import `ingestion` locally instead of
# routing to the user code gRPC server via workspace.yaml.
WORKDIR $DAGSTER_APP
COPY pyproject.toml uv.lock ./
RUN uv sync --no-dev --group dagster --no-cache

WORKDIR $DAGSTER_HOME
COPY .dagster_home/dagster.yaml .dagster_home/workspace.yaml ./
COPY .dlt/config.toml ./.dlt/config.toml
