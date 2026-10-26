with raw_data as (
    select * from {{ source('raw', 'stores') }}
),

cleaned as (
    select
        store_id
        , lower(trim(store_name)) as store_name
        , lower(trim(store_type)) as store_type
        , lower(trim(city)) as city
        , lower(trim(state)) as state
        , opened_date
        , created_at
        , updated_at
    from raw_data
)

select * from cleaned