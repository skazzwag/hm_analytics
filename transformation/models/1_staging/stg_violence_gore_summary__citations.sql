with final as (
    select
        title,
        url,
        _dlt_parent_id,
        _dlt_load_id,
        _dlt_id
    from {{ source('horror_movies', 'violence_gore_summary__citations') }}
)

select * from final
