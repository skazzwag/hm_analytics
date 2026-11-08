FROM python:3.13-slim-bookworm

RUN apt-get update && \
    apt-get upgrade -y && \
    apt-get install -y --no-install-recommends git && \
    apt-get clean && \
    rm -rf /var/lib/apt/lists/*

COPY --from=ghcr.io/astral-sh/uv:latest /uv /usr/local/bin/uv

WORKDIR /opt/dagster/app
COPY .dlt ./.dlt
COPY ingestion ./ingestion
COPY transformation ./transformation
COPY pyproject.toml uv.lock ./

RUN uv sync --no-dev --group dagster --group dbt --no-cache

# Dagster recommend generating the manifest at build time to avoid the
# overhead of recompiling your dbt project every time your Dagster code
# is executed:
#
# - https://docs.dagster.io/integrations/libraries/dbt/reference#loading-dbt-models-from-a-dbt-project
#
# We only need to parse the project, which does not need MotherDuck or
# blob-storage access. DBT_PARSE_ONLY prevents the on-run-start hook from
# creating MotherDuck Azure secrets during image construction.
#
# Note: running Dagster locally will point the dbt
# models to their prod locations, so we recommend NOT running any dbt
# pipelines in Dagster locally.
RUN : \
    && uv run dbt deps --project-dir transformation \
    && MOTHERDUCK_PROD_TOKEN="" \
    DBT_PARSE_ONLY=true \
    uv run dbt parse --project-dir transformation --profiles-dir transformation --target prod

EXPOSE 4000

HEALTHCHECK --timeout=1s --start-period=3s --interval=3s --retries=20 \
    CMD ["uv", "run", "dagster", "api", "grpc-health-check", "--port", "4000"]

CMD [ \
    "uv", "run", \
    "dagster", "code-server", "start", \
    "--host", "0.0.0.0", \
    "--port", "4000", \
    "--python-file", "ingestion/definitions.py" \
]
