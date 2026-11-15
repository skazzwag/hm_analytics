# Onboarding

1. Install [uv](https://docs.astral.sh/uv/) and Make.
2. Clone the repo and run `make setup`.
3. Copy `.env.example` to `.env` and fill in local credentials
   (TMDB, OMDb, Anthropic, MotherDuck). With `direnv`, entering the repo
   root loads `.env` automatically.
4. Read `ingestion/README.md` and `transformation/README.md`.
5. Run the ingestion pipelines locally by triggering the Dagster jobs
   (`tmdb_catalogue_ingestion_job`, `box_office_ingestion_job`,
   `violence_gore_summary_ingestion_job`, `dbt_job`) from the Dagster UI;
   run `tmdb_catalogue_ingestion_job` first on a fresh warehouse.
6. Build the dbt models: `uv run dbt build --project-dir transformation --profiles-dir transformation`.
7. Add sources and models using the layer conventions in the root README
   and the repo AGENTS.md / `.opencode/rules/`.
