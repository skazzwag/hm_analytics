# ADR 0003: Warehouse-native violence classification via prompt_jev

- **Status:** Accepted (2026-11-14)
- **Date:** 2026-11-14
- **Owner:** data-architect
- **Implementation owner (when approved):** data-engineer (ingestion prompt); analytics-engineer (dbt transformation, Guide impact)
- **Supersedes:** ADR 0002's **labels-in-prompt** aspect only (the severity/frequency labels retained in the `violence_gore_summary` prompt). ADR 0002's purpose-based pipeline structure, the Mistral/web-search swap, append-snapshot semantics, and the pipeline/resource renames all stand unchanged.
- **Plan:** `~/.opencode/plan/2026-11-14-jev-violence-classification.md` (APPROVED 2026-11-14)
- **Evidence:** MotherDuck `prompt_jev` docs — https://motherduck.com/docs/sql-reference/motherduck-sql-reference/ai-functions/prompt-jev (verified 2026-11-14)

## Context

ADR 0002 moved violence/gore analysis into the `violence_gore_summary` pipeline
(Mistral Conversations API with server-side `web_search`), with the prompt
instructing the model to emit severity/frequency **labels** (Severity:
Mild/Moderate/High/Extreme; Frequency: Isolated/Occasional/Frequent/Pervasive)
embedded in the summary text. That couples classification to ingestion: labels
live as unstructured text, cannot be queried as columns, and every
re-classification costs a billed Mistral web search per film (~1,061 per
full-catalogue run).

MotherDuck's `prompt_jev()` (TypeSafe Jev integration) answers closed questions
from SQL and returns a STRUCT with label, calibrated probabilities, and
confidence. Its `score` type implements an **ordered rubric**, returning the
numeric position (0..n-1) plus probabilities plus confidence — a direct fit for
both ordered scales. `questions := {...}` batches multiple questions into one
request per row (input sent once). Cost is AI Units on input tokens only:
~60k rows per AI Unit at 1,000-char inputs (default batch 32), so the full
catalogue (~1,061 movies) costs a fraction of one AI Unit.

## Decision

Violence/gore severity and frequency classification becomes a **warehouse-native
dbt transformation** via `prompt_jev()`:

1. **Jev is the system of record** for severity/frequency labels, ordered scores,
   and confidence. Ingestion produces only concise, label-free summaries — the
   prompt's label tables and label-emission instructions are stripped.
2. **Classification model:** a new `int_violence_classification`
   (`2_intermediate/`) deduplicates the latest summary per movie (reusing the
   `int_box_office_latest` pattern) and makes a single `prompt_jev()` call with
   `questions := {severity: {type: 'score', ...}, frequency: {type: 'score',
   ...}}`, unpacked to columns: `severity`, `severity_score` (DOUBLE 0–3),
   `severity_confidence`, `frequency`, `frequency_score`, `frequency_confidence`.
   `prs_violence_gore_summary` joins and exposes these columns, replacing the
   "labels embedded in summary text" documentation.
3. **Environment gating:** a project var `use_ai_functions` (true on MotherDuck
   targets, false on `dev-local`) enables/disables the model; downstream models
   LEFT JOIN and expose nullable classification columns so dev-local builds
   succeed.
4. **Materialization:** the classification model is materialized as a **table**
   (never evaluated per query — the docs mandate materialized CTEs / stored
   tables). Re-classification is bounded via a content-hash incremental
   predicate: only summaries whose content changed are re-classified.
5. **Criteria source:** the score rubric descriptions are ported directly from
   the legacy prompt's label definitions, **without pre-build validation**
   (user decision, 2026-11-14 — the plan's sample-validation step was revoked);
   confidence scores expose uncertain rows for later review, and criteria can be
   tuned with a cheap bounded re-classification.

## Rationale

- **Richer, structured output:** ordered score rubrics return numeric position +
  calibrated confidence — queryable columns strictly richer than labels embedded
  in summary text.
- **Cost:** a fraction of one AI Unit for ~1,061 movies versus ~1,061 billed
  Mistral web searches per full re-analysis under ADR 0002's prompt design.
- **Bounded re-classification:** the materialized table + content-hash
  incremental design keeps non-zero per-build AI Unit cost proportional to
  changed summaries, and mitigates cross-run non-determinism (classification is
  keyed to summary content, re-evaluated only on change).

## Consequences

### Positive

- Classification semantics become first-class warehouse columns with
  provenance (Jev), testable accepted-value domains, and confidence for
  triage — instead of prose parsing.
- Full-catalogue re-classification is cheap enough to treat as routine, so
  criteria tuning carries no meaningful cost penalty.

### Trade-offs / negative

- **MotherDuck-only:** `prompt_jev()` fails on the dev-local duckdb target (and
  errors with "AI functions are not available for your organization" when
  disabled/unpaid). The `use_ai_functions` var gates the model off locally;
  downstream classification columns are NULL on dev-local builds. Requires a
  paid MotherDuck plan with AI functions enabled (user to confirm separately).
- **Materialized table mandatory:** the function must never be re-evaluated per
  query; the table materialization is a hard requirement, not a tuning choice.
- **dbt unit tests cannot mock the function:** unit-testing the model would
  invoke the real `prompt_jev()`. The classification model therefore stays a
  thin wrapper, and unit fixtures cover only pure-SQL parts (e.g., any
  score→label mapping); the `prompt_jev` CTE is documented as un-unit-tested.
- **No pre-build validation of ported criteria:** the rubric descriptions were
  ported from the legacy prompt's label definitions without the planned
  ~20-movie sample validation (user decision, 2026-11-14). Classification
  quality versus the old LLM labels is unverified at acceptance time;
  confidence scores expose uncertain rows, and criteria wording sensitivity is
  a known risk to be revisited after the first full run.
- **Per-build AI Unit cost is non-zero** on MotherDuck even when nothing
  changed (the incremental predicate bounds it, not eliminates it).

## Follow-ups and impact callouts

- **analytics-engineer (dbt):** implement `int_violence_classification` (table,
  gated by `use_ai_functions`, content-hash incremental), wire
  `prs_violence_gore_summary` nullable classification columns, update column
  docs + `data_tests` (not_null `tmdb_id`; accepted_values on severity/frequency
  labels gated to MotherDuck runs). **Guide impact:** candidate durable-context
  note on classification semantics, the score scale, confidence meaning, and Jev
  provenance — propose, don't publish.
- **data-engineer (ingestion):** strip the severity/frequency label tables from
  the `violence_gore_summary` prompt (keep identity keying, citations capture,
  model/scraped_at columns); update the module docstring and mocked ingestion
  tests if they assert prompt content.
- ADR 0002's pipeline-structure, Mistral-swap, append-snapshot, and rename
  decisions remain fully in force; only its labels-in-prompt aspect is
  superseded by this ADR.
