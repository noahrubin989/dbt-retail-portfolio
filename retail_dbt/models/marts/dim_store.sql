with stores as (

    select
        store_id as store_key,
        store_name,
        store_type,
        city,
        state,
        opened_date
    from {{ ref('stg_stores') }}

),

unknown_member as (

    select
        -1 as store_key,
        'unknown' as store_name,
        'unknown' as store_type,
        cast(null as varchar) as city,
        cast(null as varchar) as state,
        cast(null as date) as opened_date

)

select * from stores
union all
select * from unknown_member