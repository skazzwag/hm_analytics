# Altimate deterministic checks and lineage

The native helper is retained; the official dbt workflow skills are installed by the consolidated pinned upstream installer. Native compatibility has not been established by this update. Altimate is a deterministic dependency, never a second agent.

## Install and verify locally
Inspect .opencode/tools/altimate/PROVENANCE.md and package.json, then request user approval for dependency installation. Use the existing Node version requirement, run the helper tests and real native smoke test. Do not infer runtime compatibility from dependency-free unit tests.
```bash
cd .opencode/tools/altimate
npm install
npm test
node analyze.mjs self-test
cd ../..
python .opencode/tools/skills/install_official.py --status
```
Seven standalone Altimate dbt workflow skills are **already included** in `.opencode/skills/dbt-*`, sourced from the uploaded `npx skills` archive. Each has an upstream source hash and project override requiring the development-only dbt runner. Do not run an installer for them. `dbt-model-enhancement` was excluded after the user's security warning. No Altimate agent delegation, additional MCP or Snowflake-only skill was installed. See `.opencode/docs/setup-official-skills.md`. Missing native output is inconclusive, never model-invented lineage.

## Obtain artifacts
Eligible agents may request the dev-only runner after .opencode/docs/setup-dbt-safety.md is completed. Otherwise request traceable user/CI artifacts. Do not run raw dbt, dbt MCP or altimate-dbt. The default runner tree is .analysis/dbt/<actor>/<session>/target/. Use actual artifact paths, not placeholders.

Example preparation after a successful matching compile/catalog run:
```bash
node .opencode/tools/altimate/prepare-dbt.mjs \
  --project-root transformation \
  --manifest .analysis/dbt/implementer/initial/target/manifest.json \
  --catalog .analysis/dbt/implementer/initial/target/catalog.json \
  --model YOUR_MODEL \
  --out .analysis/altimate/YOUR_MODEL
```
Supported checks and custom native lineage:
```bash
altimate-code check .analysis/altimate/YOUR_MODEL/model.sql \
  --schema .analysis/altimate/YOUR_MODEL/schema.json \
  --checks lint,validate,safety --format json --fail-on error
node .opencode/tools/altimate/analyze.mjs lineage \
  --sql .analysis/altimate/YOUR_MODEL/model.sql \
  --schema .analysis/altimate/YOUR_MODEL/schema.json --dialect duckdb
```
After native compatibility tests, analyze.mjs check is an optional direct-engine subset. Do not suppress error exit codes. Review known mappings, relation qualification, unsupported SQL and missing catalog columns on a real model. Static column lineage is per compiled query, not a stitched graph or proof of equivalent filters/grain/results.

## Workflow
Analytics-engineer owns modeling, transformation DQ and local Git Guide maintenance. Reviewer may request the same evidence tools without source editing. Record source/artifact hashes, target/schema, actual result codes and limitations. Current source and a known native result are both required; source changes invalidate earlier evidence. Durable Guide content goes under transformation/guides/ for existing CI publication, not direct MCP mutations.

## Updating already-installed Altimate skills
The consolidated installer will not overwrite local edits or migrate the older unprefixed Altimate entries silently. Back up and remove the old `.agents/skills/<name>/` entries if they exist, then run the new installer. Do not install the old `.opencode/tools/altimate/install-skills.mjs` version. For future updates, review and pin newer commits explicitly in the installer lock. The native engine helpers are unchanged.
