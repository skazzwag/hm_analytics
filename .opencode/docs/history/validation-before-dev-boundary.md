# Validation - notebook update (2026-10-25)

## Executed tests

| Check | Result | What it establishes |
|---|---|---|
| `python -m pytest -q tools/notebooks/test` | 29 passed | AST policy behavior, syntax of three template notebooks, widget-cell convention, template gating/overflow and truthful CLI reporting |
| `node --test tools/altimate/test/*.test.mjs tools/guides/test/*.test.mjs` | 57 passed | Existing dependency-free Altimate adapter/artifact/freshness/installer and Guide-validator regressions |

Total: **86 passing unit tests**. These are not 86 live database or notebook-rendering checks.

Additional packaging checks parse modified JSON/YAML, validate the two updated skills, compare retained Guide/core files to the preceding ZIP, and verify that the patch reconstructs the updated overlay. See the delivered packaging report for actual results and file counts.

## Not verified

- Real marimo graph/lint execution, Altair rendering, UI interactions or notebook data correctness. Neither marimo, Altair nor DuckDB was initially installed. An isolated `uv pip install` failed because the environment could not resolve `pypi.org`; no runtime pass is claimed.
- Live MotherDuck authentication, query costs, remote permissions, raw-result/export privacy or Guide retrieval/publication.
- The PR on `zb_20261007_1`, its head revision, comments, Guide layout, version strategy or deployment code. GitHub's accessible-repository and installation lists were empty despite the plugin being enabled.
- Real OpenCode permission enforcement, actual tool names in the user's installed MCP, native Altimate engine compatibility or startup latency. Existing limitations still apply.

## Required local acceptance

Use `docs/setup-notebooks.md`: install/sync a reviewed locked environment, run `marimo check`, render the synthetic fixture, check local selections, then test an approved bounded real dataset. Live notebook runtime requires separately approved read-only authentication and scope. No agent may run dbt.

Guide implementation files and publishing permissions were deliberately retained, not guessed from the unavailable PR. Do not adopt the old example Guide layout over the repository's actual implementation. Resolve repository access and inspect the PR before migrating.

## Historical validation

The preceding package's report is retained at `docs/history/validation-before-notebooks.md`. Its claims are historical; this report is the status for the current notebook update.
