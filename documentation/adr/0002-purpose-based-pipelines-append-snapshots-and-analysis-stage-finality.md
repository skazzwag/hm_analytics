# ADR 0002: Purpose-based pipelines, append snapshots, and analysis-stage finality

- **Status:** Accepted (2026-11-14)
- **Date:** 2026-11-14
- **Owner:** data-architect
- **Implementation owner (when approved):** data-engineer (ingestion, Dagster); analytics-engineer (dbt/Guide impact)
- **Supersedes:** ADR 0001 (static/temporal cadence split). Also supersedes v1 of the
  underlying plan (completion-aware ingestion skipping, removed by user decision 2026-11-14).
- **Plan:** `~/.opencode/plan/2026-11-09-box-office-restructure.md` (v2, revised 2026-11-14)

## Context

ADR 0001 fixed the Dagster load conflicts within the existing **cadence-based**
pipeline split (`tmdb_static`, `tmdb_temporal`, `omdb_static`, `omdb_temporal`,
`movie_analysis`). The box-office analytics project has since made that split the
wrong axis: what matters is pipeline **purpose** (catalogue spine, box-office
evidence, content analysis), not how often a source was assumed to change. Two
facts drive the redesign:

1. **No API freshness field exists.** Neither OMDb nor TMDB exposes last-updated
   metadata, so a `merge` write disposition cannot detect staleness — there is no
   signal to compare against. Appending dated snapshots is the only way to
   preserve evidence that a value changed.
2. **"Final box office" is an analytical judgement, not an ingestion fact.** The
   validated ≥16-weeks-past-release plateau proxy
   (`analysis/notebooks/omdb_box_office_plateau.py`: 100% of films ≥16 weeks past
   release showed a plateau, k=2 consecutive identical values; 508 films) is a
   filter to apply in dbt/analysis — putting completion logic in ingestion would
   bake an analysis assumption into raw data capture.

## Decision

Replace the static/temporal cadence split with **purpose-based pipelines**:

| Pipeline | Content | Write disposition |
|---|---|---|
| `tmdb_catalogue` | Catalogue-only TMDB (join spine + runtime dependency of both downstream pipelines) | merge (catalogue upsert) |
| `box_office` | OMDb box-office data; renamed from `omdb_temporal`; resource/table renamed `box_office_snapshots` | **append**, full-catalogue re-fetch per run, `primary_key=["imdb_id", "scraped_at"]` |
| `violence_gore_summary` | Renamed from `movie_analysis`; Anthropic → **Mistral Conversations API** with server-side `web_search` tool; concise-summary prompt (severity/frequency labels retained) | full re-analysis of all ~1,061 films; old `violence_gore_analysis` table kept as legacy |

Final-value derivation (latest snapshot per film) and the ≥16-week finality
filter move downstream to dbt. Dagster asset groups/jobs are restructured to
match; runs stay manual-only.

## Rationale

- **Append over merge:** with no freshness field, merge cannot stale-detect;
  append preserves the only change evidence and is the minimal change from the
  current pipeline. "Final box office" = latest snapshot per film, derived
  downstream (`row_number() ... order by scraped_at desc`, never `arg_max`,
  which NULL-skips).
- **Finality at the analysis stage:** ingestion mirrors current OMDb state for
  all films (in-run films included); the plateau proxy is applied as a
  dbt/analysis filter on `release_date`. Confidence is high for back-catalogue,
  low for current releases (one in-run observation) — recalibrate as snapshots
  accumulate.
- **Purpose-based naming** makes dependencies legible: `box_office` and
  `violence_gore_summary` both read `raw/movie_catalogue` at runtime, so the
  catalogue pipeline must remain a first-class load.

## Consequences

### Positive

- Pipeline names state intent; the join spine (`tmdb_catalogue`), evidence
  capture (`box_office_snapshots`), and derived analysis (dbt final-value +
  finality) each have one clear home.
- Change evidence is preserved: every run appends a dated full-catalogue
  snapshot, so value changes (and regressions, e.g. value→N/A) remain
  observable.
- The Mistral swap enables real web search per film with citation provenance
  (optional `tool_reference` title/url columns).

### Trade-offs / negative

- **Dropped sources:** `movie_popularity`, `movie_details`, `movie_keywords`
  (TMDB), `omdb_metadata` (OMDb). Lost: the TMDB worldwide `revenue` cross-check
  (investigation showed it unreliable for validation anyway: median ratio 1.88,
  ~5% stale) and future popularity history. **Already-ingested data remains in
  MotherDuck**; git history retains the source code, so re-adding is cheap.
- **OMDb quota:** each run fetches the full catalogue (~1,061 calls ≈ one day's
  1,000/day free tier). Manual triggering fits this; more-frequent-than-daily
  runs would exceed quota.
- **OMDb update lag is unknowable from the API** — a snapshot plateau may
  reflect OMDb staleness rather than real-world finality. Accepted and to be
  documented in Guide context, not engineered around.
- **Mistral `web_search` is billed per use** (~1,061 billed searches for the
  full re-analysis); a bounded single-movie smoke test precedes any bulk run.
- **Legacy table:** old `violence_gore_analysis` stays in MotherDuck as legacy
  reference; the new pipeline writes a fresh table.
- **dbt semantic loss** in `prs_*` models from removed columns must be
  reported, not silent (analytics-engineer).

## Follow-ups and impact callouts

- **analytics-engineer (dbt):** latest-snapshot dedup model, `box_office_final`
  presentation model, analysis-stage finality filter, removal of staging models
  for dropped sources, renames (`stg_violence_gore_summary`,
  `prs_violence_gore_summary`), `source.yml` updates. **Guide impact:** likely
  durable-context note on `box_office_snapshots` value domain, snapshot cadence,
  and finality semantics — propose, don't publish.
- **data-engineer (ingestion):** pipeline/source/resource renames, Mistral
  provider swap, Dagster groups/jobs, unit tests per the plan.
- ADR 0001's structural fixes (unique asset keys, unique op names, distinct
  pipeline names, single `movie_catalogue` owner) remain valid and are carried
  forward; only the cadence framing is superseded.
