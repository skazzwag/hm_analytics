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
-- Severity and frequency labels are NOT separate warehouse columns; they are
-- embedded at the end of the summary text and are deliberately not
-- re-extracted here (see stg_violence_gore_summary).
--
-- Citations of the latest run are aggregated into a single
-- semicolon-separated 'title: url' string (NULL when the run produced no
-- citations). Citation order is not guaranteed; the column is display
-- provenance only, not machine-parseable.
with summary_latest as (
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
    from summary_latest
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
    final.citations
from final
