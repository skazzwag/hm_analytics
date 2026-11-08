with final as (
    select
        movie_id,
        keyword_id,
        keyword_name,
        _dlt_load_id,
        _dlt_id
    from {{ source('horror_movies', 'movie_keywords') }}
)

select * from final
