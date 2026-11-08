with final as (
    select
        tmdb_id,
        imdb_id,
        title,
        year,
        rated,
        runtime,
        director,
        writer,
        actors,
        plot,
        awards,
        dvd,
        _dlt_load_id,
        _dlt_id
    from {{ source('horror_movies', 'omdb_metadata') }}
)

select * from final
