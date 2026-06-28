{{
  config(
    materialized = 'table',
    schema = 'staging'
  )
}}

SELECT
    title,
    release_date,
    model,
    model_response,
    timestamp,
    _dlt_load_id,
    _dlt_id
FROM {{ source('horror_movies', 'violence_gore_analysis') }}
