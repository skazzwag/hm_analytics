-- Violence/gore summary analysis, one row per analysed movie (tmdb_id).
--
-- The Mistral web-search pipeline appends one summary row per movie per run
-- to violence_gore_summary and stores its web-search citations in the dlt
-- child table violence_gore_summary__citations (joined via _dlt_parent_id =
-- parent _dlt_id). The latest analysis per film is selected with
-- row_number() over (partition by tmdb_id order by scraped_at desc),
-- matching int_box_office_latest. Films not yet analysed are absent: the
-- grain is the summary pipeline, not the full catalogue.
--
-- Jev classification columns (severity, scores, confidence) come from
-- int_violence_classification via LEFT JOIN on tmdb_id. That model is
-- MotherDuck-only (prompt_jev requires AI functions) and is disabled on the
-- dev-local duckdb target via the use_ai_functions project var, so the ref
-- and join are emitted conditionally on the same var: on dev-local the
-- classification columns are typed NULLs and the model still builds. Films
-- without a classification (or any row on dev-local) carry NULL there.
--
-- Citations of the latest run are aggregated into a single
-- semicolon-separated 'title: url' string (NULL when the run produced no
-- citations). Citation order is not guaranteed; the column is display
-- provenance only, not machine-parseable.
{% if var('use_ai_functions', false) %}
with classification as (
    select
        tmdb_id,
        severity,
        severity_score,
        severity_confidence,
        frequency,
        frequency_score,
        frequency_confidence
    from {{ ref('int_violence_classification') }}
),
{% endif %}

summary_latest as (
    select
        tmdb_id,
        title,
        cast(nullif(release_date, '') as date) as release_date,
        summary,
        model,
        scraped_at,
        _dlt_id
    from {{ ref('stg_violence_gore_summary') }}
    qualify row_number() over (
        partition by tmdb_id
        order by scraped_at desc
    ) = 1
),

citations as (
    select
        cit._dlt_parent_id,
        string_agg(coalesce(cit.title, '(untitled)') || ': ' || cit.url, '; ') as citations
    from {{ ref('stg_violence_gore_summary__citations') }} cit
    group by cit._dlt_parent_id
),

final as (
    select
        summary_latest.tmdb_id,
        summary_latest.title,
        summary_latest.release_date,
        summary_latest.summary,
        summary_latest.model as summary_model,
        summary_latest.scraped_at,
        citations.citations
        {% if var('use_ai_functions', false) %}
        ,classification.severity
        ,classification.severity_score
        ,classification.severity_confidence
        ,classification.frequency
        ,classification.frequency_score
        ,classification.frequency_confidence
        {% else %}
        ,cast(null as varchar) as severity
        ,cast(null as double) as severity_score
        ,cast(null as double) as severity_confidence
        ,cast(null as varchar) as frequency
        ,cast(null as double) as frequency_score
        ,cast(null as double) as frequency_confidence
        {% endif %}
    from summary_latest
    {% if var('use_ai_functions', false) %}
    left join classification
        on summary_latest.tmdb_id = classification.tmdb_id
    {% endif %}
    left join citations
        on summary_latest._dlt_id = citations._dlt_parent_id
)

select
    final.tmdb_id,
    final.title,
    final.release_date,
    final.summary,
    final.summary_model,
    final.scraped_at,
    final.citations,
    final.severity,
    final.severity_score,
    final.severity_confidence,
    final.frequency,
    final.frequency_score,
    final.frequency_confidence
from final
