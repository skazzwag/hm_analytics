{{
  config(
    materialized = 'table',
    schema = 'staging'
  )
}}

SELECT
   adult,
   backdrop_path,
   budget,
   homepage,
   id,
   imdb_id,
   original_language,
   original_title,
   overview,
   poster_path,
   release_date,
   revenue,
   runtime,
   status,
   tagline,
   title,
   video,
   us_certification,
   genre_names,
   _dlt_load_id,
   _dlt_id
FROM {{ source('horror_movies', 'movie_details') }}