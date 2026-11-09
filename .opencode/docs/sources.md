# Sources and scope
Design basis: exact user-supplied Guide README in reference/motherduck-guides-readme.md. The complete PR/scripts/metadata and CI were not supplied; README intent is not evidence of implementation correctness.

Technical references checked October 25, 2026:
- https://opencode.ai/docs/agents/
- https://opencode.ai/docs/permissions/
- https://docs.getdbt.com/docs/local/profiles.yml
- https://docs.getdbt.com/reference/commands/compile
- https://docs.getdbt.com/docs/build/data-tests
- https://github.com/duckdb/dbt-duckdb
- https://dlthub.com/docs/general-usage/schema-contracts
- https://docs.github.com/en/actions/how-tos/deploy/configure-and-manage-deployments/manage-environments
MotherDuck's documentation connector confirmed separate identities for dev/prod, account-owned development databases and read-only input shares. It did not establish your actual grants or cached-credential precedence. References returned:
- https://motherduck.com/docs/key-tasks/data-warehousing/environment-management/
- https://motherduck.com/docs/concepts/resource-management/
- https://motherduck.com/docs/key-tasks/service-accounts-guide/impersonate-service-accounts/

The dev runner is custom code. Its operation against your installed dbt/Core/adapter, macros, schema routing and MotherDuck credentials must be accepted locally. No live warehouse or Guide queries were performed. Existing native Altimate and notebook runtime limits remain.

## Official skills pinned upstream

- Altimate dbt skill pack: https://github.com/AltimateAI/data-engineering-skills
- marimo-pair live notebook workflow: https://github.com/marimo-team/marimo-pair
- Dagster official `dagster-expert` (active dagster plugin): https://github.com/dagster-io/skills
- OpenCode skill discovery/naming: https://opencode.ai/docs/skills

See `.opencode/tools/skills/official-sources.lock.json` and `.opencode/docs/setup-official-skills.md` for pinned SHA and local security adaptation.
