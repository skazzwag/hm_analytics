{{
  config(
    materialized = 'table',
    schema = 'staging'
  )
}}

SELECT
    id,
    title,
    original_title,
    release_date,
    original_language,
    adult,
    video,
    backdrop_path,
    poster_path,
    overview,
    _dlt_load_id,
    _dlt_id
FROM {{ source('horror_movies', 'movie_catalogue') }}