with final as (
    select
        title,
        release_date,
        model,
        model_response,
        timestamp,
        _dlt_load_id,
        _dlt_id
    from {{ source('horror_movies', 'violence_gore_analysis') }}
)

select * from final
