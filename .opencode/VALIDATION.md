# Validation — complete official specialist skills bundle (2026-11-01)

## Contents and provenance

- Starting point: previous full `opencode-specialist-skills-bundled.zip` distribution, with 35 project and third-party `.opencode/skills/` entries.
- New source: user's `.agents(1).zip`; it contains the **real, full official Dagster `dagster-expert`** from the `dagster` plugin (8,212-byte upstream `SKILL.md`) with **173** separate `.md` reference files. The previous deprecated stub has been replaced.
- Included the 174 Dagster source docs plus Apache-2.0 licence under `.opencode/skills/dagster-expert/`. Excluded **174** Windows `Zone.Identifier` sidecars.
- Verified the uploaded Dagster `SKILL.md` Git blob SHA-1 (`6951cb37396d42a4cab7de2466447738deae32d1`) against the previously confirmed pinned Dagster Git revision `c23c97fe5ffc4a39dc9cc1f9834c0311858cc16f`. The **173 supporting documents were not independently checked against GitHub**; their uploaded-source SHA-256 hashes and packaged SHA-256 hashes are recorded in `vendor/official-skills/dagster-source-manifest.json`.
- Of 174 source documents, **170 copied unchanged**, and four adapted: `SKILL.md` (Primary tool and repository safety policy), `references/cli/api/general.md` (MotherDuck-only MCP / CLI-only policy), `references/cli/launch.md` (execution approval policy), and `references/components/creating-components.md` (corrected a broken local Markdown reference link).
- Existing Altimate seven dbt skills, complete marimo-pair (both scripts/five refs), custom roles, `dagster-fido-dagster`, ignored `analysis/`, native Altimate helpers, Guide policies and disabled-by-default dev-only dbt runner were retained.
- **36** `.opencode/skills/` entries (27 project-local + 9 upstream), plus three existing `.agents/skills/` workflow entries; all **nine** upstream specialist entries return `INSTALLED` from `python tools/skills/install_official.py --status`.
- Only configured MCP: **`motherduck-remote`**. `dbt-model-enhancement` (security alert), Altimate delegation and Dagster MCP were not added.

## Automated checks

- `python -m unittest discover -s tools/config/test -p 'test_*.py'` — **33** passed.
- `python -m unittest discover -s tools/dbt/test -p 'test_*.py'` — **31** passed.
- `python -m unittest discover -s tools/skills/test -p 'test_*.py'` — **16** passed (includes full Dagster reference completeness, relative link resolution and security rules).
- `pytest -q tools/notebooks/test` — **29** passed.
- `node --test tools/altimate/test/*.test.mjs` — **36** passed.

**Total: 145 automated tests passed.** Python's named subtests are included under their parent test count rather than counted as independent tests.

## Unverified in this environment

- Actual WSL OpenCode discovery at runtime and Dagster `dg` CLI execution against the user's real project.
- Dagster Plus credentials or remote deployment state, development dbt and dlt runs, Azure Container Apps logs, and marimo-pair live notebook execution.
- The user should merge the overlay into their real repository, remove duplicate unprefixed skills (see `REMOVALS.txt`) and run `opencode agent list`, plus the selected approved CLI smoke tests before enabling any execution.

ZIP integrity and file-by-file extraction digests are verified during packaging.
