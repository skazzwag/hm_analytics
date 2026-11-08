with violence_extracted as (
    select
        analysis.title,
        analysis.release_date,
        analysis.model,
        analysis.model_response,
        case
            when analysis.model_response like '%Mild%' then 'Mild'
            when analysis.model_response like '%Moderate%' then 'Moderate'
            when analysis.model_response like '%High%' then 'High'
            when analysis.model_response like '%Extreme%' then 'Extreme'
            else null
        end as severity,
        case
            when analysis.model_response like '%Isolated%' then 'Isolated'
            when analysis.model_response like '%Occasional%' then 'Occasional'
            when analysis.model_response like '%Frequent%' then 'Frequent'
            when analysis.model_response like '%Pervasive%' then 'Pervasive'
            else null
        end as frequency,
        analysis.timestamp
    from {{ ref('stg_violence_gore_analysis') }} as analysis
),

final as (
    select
        movie_details.title,
        case
            when movie_details.release_date = '' then null
            else movie_details.release_date::date
        end as release_date,
        movie_details.original_language,
        movie_details.budget::decimal(12, 2) as budget,
        movie_details.revenue::decimal(12, 2) as revenue,
        movie_details.runtime,
        movie_details.us_certification,
        string_split(movie_details.genre_names, ',') as genre_names,
        movie_details.overview,
        case
            when omdb_scores.imdb_rating = 'N/A' then null
            else (10 * omdb_scores.imdb_rating::decimal(2, 1))::integer
        end as imdb_rating,
        case
            when omdb_scores.imdb_votes = 'N/A' then null
            else replace(omdb_scores.imdb_votes, ',', '')::integer
        end as imdb_votes,
        case
            when omdb_scores.metascore = 'N/A' then null
            else omdb_scores.metascore::integer
        end as metascore,
        replace(omdb_scores.rotten_tomatoes_score, '%', '')::integer as rotten_tomatoes_score,
        case
            when omdb_scores.box_office = 'N/A' then null
            else replace(replace(omdb_scores.box_office, '$', ''), ',', '')::decimal(12, 2)
        end as box_office,
        violence_extracted.severity,
        violence_extracted.frequency,
        violence_extracted.model_response,
        violence_extracted.timestamp as analysis_timestamp
    from {{ ref('stg_movie_details') }} as movie_details
    left join {{ ref('stg_omdb_scores') }} as omdb_scores
        on movie_details.imdb_id = omdb_scores.imdb_id
    left join violence_extracted
        on movie_details.title = violence_extracted.title
        and movie_details.release_date = violence_extracted.release_date
)

select * from final
