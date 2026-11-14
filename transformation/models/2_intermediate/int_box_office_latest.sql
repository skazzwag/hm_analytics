-- One row per film: the latest box-office snapshot per imdb_id.
--
-- Deliberately uses explicit row_number() ordering, NOT arg_max(): DuckDB's
-- arg_max(arg, val) skips rows where the arg is NULL, so a value->'N/A'
-- regression (observed in the data, e.g. the 'Dracula' film) would be silently
-- masked by an earlier non-NULL value. The latest snapshot is authoritative
-- even when it regresses to 'N/A'.
with final as (
    select
        imdb_id,
        tmdb_id,
        scraped_at,
        imdb_rating,
        imdb_votes,
        metascore,
        rotten_tomatoes_score,
        metacritic_score,
        box_office
    from {{ ref('stg_box_office_snapshots') }}
    qualify row_number() over (
        partition by imdb_id
        order by scraped_at desc
    ) = 1
)

select
    imdb_id,
    tmdb_id,
    scraped_at,
    imdb_rating,
    imdb_votes,
    metascore,
    rotten_tomatoes_score,
    metacritic_score,
    box_office
from final
