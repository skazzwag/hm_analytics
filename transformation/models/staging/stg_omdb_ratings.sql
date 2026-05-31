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
    imdb_rating,
    imdb_votes,
    metascore,
    metacritic_score,
    rotten_tomatoes_score,
    box_office,
    dvd,
    _dlt_load_id,
    _dlt_id
FROM {{ source('horror_movies', 'omdb_ratings') }}