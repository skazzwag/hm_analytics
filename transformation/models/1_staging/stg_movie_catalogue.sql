with final as (
    select
        adult,
        backdrop_path,
        id,
        original_language,
        original_title,
        overview,
        poster_path,
        release_date,
        title,
        video,
        _dlt_load_id,
        _dlt_id
    from {{ source('horror_movies', 'movie_catalogue') }}
)

select * from final
