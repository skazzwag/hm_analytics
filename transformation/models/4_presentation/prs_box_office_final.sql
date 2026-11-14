-- One row per film: final (latest-snapshot) US domestic gross with provenance.
--
-- Finality semantics: ingestion appends full-catalogue snapshots with no
-- completion logic. "Final box office" is derived here as the latest snapshot
-- per film (int_box_office_latest). The >=16-weeks-past-release plateau proxy
-- is exposed as the documented boolean column `is_finished_cohort` rather
-- than hard-coded as a row filter, so analysis-stage queries choose their own
-- cohort definition. See the model YAML for caveats.
with catalogue as (
    select
        id as tmdb_id,
        title,
        release_date,
        original_language
    from {{ ref('stg_movie_catalogue') }}
),

box_office_latest as (
    select
        imdb_id,
        tmdb_id,
        scraped_at,
        box_office
    from {{ ref('int_box_office_latest') }}
),

final as (
    select
        catalogue.tmdb_id,
        catalogue.title,
        cast(nullif(catalogue.release_date, '') as date) as release_date,
        catalogue.original_language,
        box_office_latest.imdb_id,
        box_office_latest.scraped_at as box_office_scraped_at,
        case
            when box_office_latest.box_office = 'N/A' then null
            else replace(replace(box_office_latest.box_office, '$', ''), ',', '')::decimal(12, 2)
        end as final_domestic_gross,
        cast(nullif(catalogue.release_date, '') as date)
            <= box_office_latest.scraped_at::date - interval '16 weeks'
            as is_finished_cohort
    from catalogue
    left join box_office_latest
        on catalogue.tmdb_id = box_office_latest.tmdb_id
)

select
    final.tmdb_id,
    final.title,
    final.release_date,
    final.original_language,
    final.imdb_id,
    final.box_office_scraped_at,
    final.final_domestic_gross,
    final.is_finished_cohort
from final
