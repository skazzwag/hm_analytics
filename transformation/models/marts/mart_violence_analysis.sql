{{
  config(
    materialized = 'table',
    schema = 'marts'
  )
}}

WITH violence_extracted AS (
  SELECT
    title,
    release_date,
    model,
    model_response,
    CASE
      WHEN model_response LIKE '%Mild%' THEN 'Mild'
      WHEN model_response LIKE '%Moderate%' THEN 'Moderate'
      WHEN model_response LIKE '%High%' THEN 'High'
      WHEN model_response LIKE '%Extreme%' THEN 'Extreme'
      ELSE NULL
    END AS severity,
    CASE
      WHEN model_response LIKE '%Isolated%' THEN 'Isolated'
      WHEN model_response LIKE '%Occasional%' THEN 'Occasional'
      WHEN model_response LIKE '%Frequent%' THEN 'Frequent'
      WHEN model_response LIKE '%Pervasive%' THEN 'Pervasive'
      ELSE NULL
    END AS frequency,
    timestamp
  FROM {{ ref('stg_violence_gore_analysis') }}
)

SELECT
  md.title,
  case
      when md.release_date = '' then null
      else md.release_date::date
  end as release_date,
  md.original_language,
  md.budget::decimal(12,2) as budget,
  md.revenue::decimal(12,2) as revenue,
  md.runtime,
  md.us_certification,
  string_split(md.genre_names, ',') as genre_names,
  md.overview,
  case
      when orat.imdb_rating = 'N/A' then null
      else (10 * orat.imdb_rating::decimal(2,1))::integer
  end as imdb_rating,  -- cast to decimal(2, 1)
  case
      when orat.imdb_votes = 'N/A' then null
      else replace(orat.imdb_votes, ',', '')::integer
  end as imdb_votes,  -- cast to decimal(2, 1)
  case
      when orat.metascore = 'N/A' then null
      else orat.metascore::integer
  end as metascore,
  replace(orat.rotten_tomatoes_score, '%', '' )::integer as rotten_tomatoes_score,
  case
      when orat.box_office = 'N/A' then null
      else replace(replace(orat.box_office, '$', ''), ',', '')::decimal(12,2) 
  end as box_office,
  ve.severity,
  ve.frequency,
  ve.model_response,
  ve.timestamp AS analysis_timestamp
FROM {{ ref('stg_movie_details') }} md
LEFT JOIN {{ ref('stg_omdb_scores') }} orat ON md.imdb_id = orat.imdb_id
LEFT JOIN violence_extracted ve ON md.title = ve.title AND md.release_date = ve.release_date
