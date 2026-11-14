with final as (
    select
        tmdb_id,
        title,
        release_date,
        summary,
        model,
        scraped_at,
        _dlt_load_id,
        _dlt_id
    from {{ source('horror_movies', 'violence_gore_summary') }}
)

select * from final
