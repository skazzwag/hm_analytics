{{
  config(
    materialized = 'table',
    schema = 'staging'
  )
}}

SELECT
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
FROM {{ source('horror_movies', 'omdb_scores') }}