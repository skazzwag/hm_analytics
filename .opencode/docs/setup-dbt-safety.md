# Development dbt execution without production credentials

## Decision and limits
Allow analytics-engineer and reviewer to request a small opt-in dev runner. Keep raw dbt, dbt MCP, altimate-dbt and hidden orchestration execution denied. No new agent is needed.

Removing MOTHERDUCK_PROD_TOKEN is a good first step, not a complete boundary. A target name is configuration, not access control. A fresh token belonging to the same production service account has the same underlying identity. Use a different development account with no production ownership/write/admin capability. Production source access should be through approved read-only shares; writes should be confined to that development account's own database(s).

The runner prevents common target/profile/flag mistakes. It cannot sandbox dbt macros, Python models, packages, custom schema/database macros, filesystem access, network calls or alternate credentials. Its enabled/verified flags are operator acknowledgements, not a live proof of grants. Do not enable it until the actual credential and warehouse boundary is verified. Do not use OpenCode auto-approve or blanket shell approval for runtime commands.

## 1. Remove production capabilities from the agent environment
The user/admin performs these steps, not an agent inspecting secrets:
- Keep the production service account credential only in the approved CI secret store. Protect main, deployment workflow changes and the production environment using controls available on your GitHub plan.
- Remove production variables from shell startup, dotenv/direnv, containers and subprocess environments. Account for MOTHERDUCK_PROD_TOKEN, MOTHERDUCK_TOKEN, motherduck_token, DBT_ENV_SECRET_* and project-specific aliases without printing their values.
- Audit persistent MotherDuck/DuckDB authentication, stored secrets, profiles, browser authentication, secret-manager access, mounted Windows home directories and other agents/MCP credentials. A credential denied to a file-read tool may still be reachable from project code or the shell.
- Stop and restart OpenCode, its persistent backend and any affected MCP processes after changing inherited credentials. Unsetting a variable in a new shell does not alter an already-running process.
- For stronger isolation, run in a dedicated development container/OS account with only the repo/dev credentials mounted. Do not mount the normal home, production secret stores, Windows drives or Docker socket. A dev container with all host credentials mounted is not meaningful isolation.

Do not delete or revoke shared production credentials blindly. Coordinate rotation/revocation with CI owners if copies have leaked; removal from the development environment is distinct from disabling CI's credential.

## 2. Provision and verify a separate dev identity
An administrator establishes a non-production identity, an owned development database such as agent_dev_fido, and approved read-only source shares. Use the README's share references only after confirming current access and names. Do not grant ownership of production databases just so an agent can build access-layer copies.

Verify the connected identity, owned/writable databases, share access and absence of production/admin privileges. Use administrator permission inspection and disposable non-production fixtures for deny tests; do not attempt destructive writes against production to prove they fail. Read-only source access can still expose sensitive data and incur query cost.

If the chosen account can acquire prod/admin credentials, impersonate the production account, or write the production objects, stop. Use a more isolated identity/environment or user/CI-only execution. Roles, grants and token handling must be checked in the live organization; this archive has not done so.

A globally read-only token cannot generally build dev models. The required shape is a development identity able to write its own dev database while production inputs remain read-only shares. Do not confuse read-only MCP with this separate runtime identity.

## 3. Inspect project routing and hooks
The actual dbt project was not provided with this update. Before enabling runtime, inspect:
- dbt_project.yml, generate_database_name and generate_schema_name, per-model +database/+schema, access/mart materializations and any explicit prod-qualified outputs;
- on-run/pre/post hooks, custom macros, Python models, seeds, snapshots and packages;
- external output paths, token lookups, environment variables and other service credentials;
- the installed dbt Core/dbt-duckdb/DuckDB versions and MotherDuck compatibility.

The supplied wrapper uses target name agent_dev. Existing macros that distinguish dev-cloud/dev-local/prod may need a reviewed update to recognise agent_dev. No such project files are changed in this overlay. Ensure role/session schemas are preserved rather than collapsed by custom macros. Configure access-layer models to use dev destinations or exclude them; do not grant prod access to make failures disappear.

## 4. Install the opt-in policy
Use the existing locked dbt environment; do not upgrade it just for this setup. The wrapper itself uses Python standard library only.

Copy .opencode/tools/dbt/agent-policy.example.json to a user-controlled non-secret policy file, for example ~/.config/opencode/dbt-agent.json. It is disabled by default. Set the absolute dbt executable, exact agent_dev_* database and only the source share attachments the selected models require. The user sets enabled and boundary_verified_by_user to true only after the preceding checks.

Optional attachment shape (the example share is from the supplied README, not a live discovery):
```json
{"path": "md:_share/prod_analytics/b57bb6cc-f153-49c4-92c6-36f40631858b", "alias": "prod_analytics"}
```
Use an alias required by the existing source definitions; the runner forces read_only=true. Source share aliases may be prod_*; the destination must be agent_dev_*. Never add tokens, custom settings/plugins or a production profile to this file.

Point the launcher to the non-secret config:
```bash
export DBT_AGENT_CONFIG="$HOME/.config/opencode/dbt-agent.json"
```
Set MOTHERDUCK_AGENT_DEV_TOKEN through your approved user-managed credential injection, without entering the value into agent chat, committed files or shell history. The runner fails without this explicit token. It maps only that token to the child motherduck_token/DBT_ENV_SECRET_MOTHERDUCK_DEV_TOKEN variables, generates one credential-free agent_dev profile and uses a private HOME. It does not rely on undocumented auth-cache precedence. These measures do not prevent arbitrary project code from reading files elsewhere if the OS allows it.

## 5. Dry-run and staged acceptance
From the real repository root:
```bash
python .opencode/tools/dbt/run.py compile --actor implementer --session initial --select +YOUR_MODEL --dry-run
```
Dry-run prints the exact argv, generated profile and source digest. It does not authenticate, validate permissions, compile or run SQL. Review the destination and selection (a small returned dataset or SQL LIMIT is not a cost bound).

With actual command approval, test a small known project/model:
```bash
python .opencode/tools/dbt/run.py parse --actor implementer --session initial
python .opencode/tools/dbt/run.py compile --actor implementer --session initial --select +YOUR_MODEL
python .opencode/tools/dbt/run.py build --actor implementer --session initial --select +YOUR_MODEL
python .opencode/tools/dbt/run.py catalog --actor implementer --session initial --select +YOUR_MODEL
```
The catalog command maps to dbt docs generate, not a warehouse-wide metadata dump assumed to be free. Validate selector support/coverage in your installed version. Use a new session if source changes; commands in a session otherwise share its target/logs. The initial build may need a larger reviewed upstream selection or additional source shares.

For independent verification of the same source:
```bash
python .opencode/tools/dbt/run.py build --actor reviewer --session review_initial --select +YOUR_MODEL
python .opencode/tools/dbt/run.py catalog --actor reviewer --session review_initial --select +YOUR_MODEL
```
The actor flag labels evidence/schema and is not authentication. The wrapper does not make an untrusted model harmless. Reviewer retains no source-edit permission, but writes development models/test artifacts through approved execution. Test/build may run hooks, persist failures or execute Python; compile can connect and run introspective queries. No run-operation, arbitrary flags, vars, defer, full-refresh or automatic dependency installation are exposed. Add support only after explicit human review; do not bypass limitations.

## 6. Altimate artifacts and review status
Use .analysis/dbt/<actor>/<session>/target/manifest.json and catalog.json with .opencode/tools/altimate/prepare-dbt.mjs --project-root transformation. The existing converter still checks source freshness. Ensure schema/catalog coverage and dev routing match the SQL under analysis.

The runner records a digest of relevant transformation source/package files (excluding generated output and Guide prose), result code, destination and artifact paths. It is not complete signed provenance for imported Python outside the project, environment-dependent macros or live data. Include Git revision and any external dependencies in review notes. Evidence folders are private/ignored and may contain compiled SQL or data; do not publish logs wholesale. Only captured output redacts the literal injected token; raw dbt logs are not a general secret-safe export.

After fixes use a new session and report whether final source was actually rechecked. Dev verification never proves production deployment, production data equivalence or Guide publication.

## Sources verified for this design
- https://docs.getdbt.com/docs/local/profiles.yml
- https://docs.getdbt.com/reference/commands/compile
- https://github.com/duckdb/dbt-duckdb
- https://motherduck.com/docs/key-tasks/data-warehousing/environment-management/
- https://motherduck.com/docs/concepts/resource-management/
- https://motherduck.com/docs/key-tasks/service-accounts-guide/impersonate-service-accounts/
- https://docs.github.com/en/actions/how-tos/deploy/configure-and-manage-deployments/manage-environments
MotherDuck account-boundary guidance was checked through its documentation connector. No organization permissions or credentials were inspected, and no warehouse access was attempted.
