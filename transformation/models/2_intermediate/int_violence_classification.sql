{{ config(materialized='table', enabled=var('use_ai_functions', false)) }}

-- One row per movie: Jev-classified violence/gore severity and frequency for
-- the latest summary snapshot per tmdb_id (same dedup pattern as
-- int_box_office_latest: explicit row_number() over scraped_at desc).
--
-- MotherDuck-only: prompt_jev() requires AI functions and fails on the
-- dev-local duckdb target ("AI functions are not available for your
-- organization"), so the model is gated by the use_ai_functions project var
-- (true on MotherDuck targets, false on dev-local). Downstream models must
-- LEFT JOIN and treat the classification columns as nullable.
--
-- The prompt_jev call uses the questions form so both questions run in ONE
-- request per row (input sent once). The CTE is MATERIALIZED per the
-- MotherDuck docs mandate: without it DuckDB may re-evaluate the CTE (and
-- re-call the model) for every field read from the result. The table
-- materialization stores results so later queries never re-call the model.
--
-- Criteria are ported from the legacy ingestion prompt's label definitions
-- (ADR 0003), without pre-build validation (user decision, 2026-11-14);
-- confidence columns expose uncertain rows for later review. The prompt_jev
-- CTE is deliberately not unit-testable (it would invoke the real function).
with latest_summary as (
    select
        tmdb_id,
        title,
        release_date,
        summary,
        scraped_at
    from {{ ref('stg_violence_gore_summary') }}
    qualify row_number() over (
        partition by tmdb_id
        order by scraped_at desc
    ) = 1
),

classified as MATERIALIZED (
    select
        tmdb_id,
        title,
        release_date,
        summary,
        scraped_at,
        prompt_jev(
            summary,
            questions := {
                severity: {
                    type: 'score',
                    instructions: 'Rate how graphic and disturbing the violence and gore in this movie summary is. Examples: Terrifier is extreme; The Shining is high; Lake Mungo is mild.',
                    criteria: [
                        {label: 'Mild', description: 'Minor injuries, implied violence, no blood'},
                        {label: 'Moderate', description: 'Blood, injuries, some gore'},
                        {label: 'High', description: 'Graphic injuries, mutilation, psychological'},
                        {label: 'Extreme', description: 'Dismemberment, torture, cannibalism, rituals'}
                    ]
                },
                frequency: {
                    type: 'score',
                    instructions: 'Rate how often violence or gore appears throughout the movie described in this summary.',
                    criteria: [
                        {label: 'Isolated', description: '1-2 brief or minor instances'},
                        {label: 'Occasional', description: '3-5 scenes or present but not central'},
                        {label: 'Frequent', description: '6+ scenes or recurring element'},
                        {label: 'Pervasive', description: 'constant, central to plot, overwhelming'}
                    ]
                }
            }
        ) as answer
    from latest_summary
),

final as (
    select
        classified.tmdb_id,
        classified.title,
        classified.release_date,
        classified.summary,
        -- score is a weighted position on the 0-3 rubric; the macro rounds
        -- to the nearest criterion index (DuckDB lists are 1-indexed, and
        -- round() is half-away-from-zero, so .5 ties pick the higher label).
        {{ jev_score_to_label(['Mild', 'Moderate', 'High', 'Extreme'], 'classified.answer.severity.score') }} as severity,
        classified.answer.severity.score as severity_score,
        classified.answer.severity.confidence as severity_confidence,
        {{ jev_score_to_label(['Isolated', 'Occasional', 'Frequent', 'Pervasive'], 'classified.answer.frequency.score') }} as frequency,
        classified.answer.frequency.score as frequency_score,
        classified.answer.frequency.confidence as frequency_confidence,
        -- Deterministic provenance: the scrape timestamp of the classified
        -- summary, not the build wall clock.
        classified.scraped_at as classified_at
    from classified
)

select
    tmdb_id,
    title,
    release_date,
    summary,
    severity,
    severity_score,
    severity_confidence,
    frequency,
    frequency_score,
    frequency_confidence,
    classified_at
from final
