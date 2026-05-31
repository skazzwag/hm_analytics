{{
  config(
    materialized = 'table',
    schema = 'staging'
  )
}}

SELECT
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
FROM {{ source('horror_movies', 'omdb_metadata') }}