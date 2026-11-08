with final as (
    select
        scraped_at,
        tmdb_id,
        imdb_id,
        imdb_rating,
        imdb_votes,
        metascore,
        rotten_tomatoes_score,
        metacritic_score,
        box_office,
        _dlt_load_id,
        _dlt_id
    from {{ source('horror_movies', 'omdb_scores') }}
)

select * from final
