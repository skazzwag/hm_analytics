{{
  config(
    materialized = 'table',
    schema = 'staging'
  )
}}

SELECT
    movie_id,
    keyword_id,
    keyword_name,
    _dlt_load_id,
    _dlt_id
FROM {{ source('horror_movies', 'movie_keywords') }}