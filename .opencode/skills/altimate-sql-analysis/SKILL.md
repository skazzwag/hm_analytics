---
name: altimate-sql-analysis
description: Run Altimate deterministic checks and native column lineage on supplied compiled dbt SQL. Use for SQL validation, column rename impact, refactors and lineage evidence. Use approved compiled artifacts or the dev runner; never launch another AI agent.
---

# Altimate SQL analysis

> **Primary tool:** Altimate native engine — deterministic checks and column lineage on supplied artifacts.

Read `.opencode/rules/altimate-analysis.md`. Reviewer may request the same approved local checks and dev runner without editing source.

## Preconditions

Require Node >=22, an installed native dependency in `.opencode/tools/altimate/`, a passing local `self-test`, and an inspected real-model compatibility test. Read `.opencode/docs/setup-altimate.md` when setup is incomplete. Do not install dependencies or regenerate dbt artifacts silently.

For dbt, require current approved dev-runner or user/CI-produced `manifest.json` and `catalog.json` for the approved target. Never analyze uncompiled Jinja or claim that a manifest model graph is column lineage. Verify whether the task concerns deployed data or proposed code.

## Commands (repo root, with normal shell approval)

Replace the model name and use separate output folders for before/after evidence. Preparation must succeed before analysis.

```bash
node .opencode/tools/altimate/prepare-dbt.mjs   --project-root transformation   --manifest .analysis/dbt/ACTOR/SESSION/target/manifest.json   --catalog .analysis/dbt/ACTOR/SESSION/target/catalog.json   --model MODEL_NAME   --out .analysis/altimate/MODEL_NAME
```

Supported headless SQL checker:

```bash
altimate-code check .analysis/altimate/MODEL_NAME/model.sql   --schema .analysis/altimate/MODEL_NAME/schema.json   --checks lint,validate,safety --format json --fail-on error
```

Native column lineage (custom local adapter, not a second agent):

```bash
node .opencode/tools/altimate/analyze.mjs lineage   --sql .analysis/altimate/MODEL_NAME/model.sql   --schema .analysis/altimate/MODEL_NAME/schema.json --dialect duckdb
```

After compatibility testing, `node .opencode/tools/altimate/analyze.mjs check --sql ... --schema ...` is an optional native-only check path. Save detailed output under `.analysis/altimate/` when useful; report short summaries and paths rather than dumping JSON into every handoff. Capture exit status; never hide failures with `|| true`.

## Interpret and verify

Inspect renamed and derived output mappings, join/CTE behavior, relation qualification and unresolved inputs. Use manifest dependencies to select consumer models; compute their mappings before asserting downstream column impact. Do not claim a complete cross-model/dlt/Dagster graph.

Keep findings, unsupported SQL, incomplete schemas and stale artifacts explicit. A successful process exit proves neither runtime correctness nor unchanged grain/filter semantics. No dependency/unsupported result means inconclusive, not a successful check.

Return source/model identity, compiled SQL/schema hashes, target/provenance, checks executed, key mappings, limitations and pending runtime dbt validation. Pass only durable reviewed conclusions to `motherduck-guides`; do not publish raw output.
