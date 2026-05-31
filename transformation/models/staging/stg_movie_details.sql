{{
  config(
    materialized = 'table',
    schema = 'staging'
  )
}}

SELECT
    id,
    imdb_id,
    title,
    original_title,
    release_date,
    original_language,
    adult,
    video,
    popularity,
    vote_average,
    vote_count,
    budget,
    revenue,
    runtime,
    status,
    tagline,
    us_certification,
    genre_names,
    backdrop_path,
    poster_path,
    overview,
    _dlt_load_id,
    _dlt_id
FROM {{ source('horror_movies', 'movie_details') }}