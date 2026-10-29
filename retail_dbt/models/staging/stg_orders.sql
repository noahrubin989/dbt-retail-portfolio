with raw_data as (
    select * from {{ source('raw', 'orders') }}
),

cleaned as (
    select
        order_id
        , customer_id
        , store_id
        , payment_method_id
        , order_timestamp
        , created_at
        , updated_at
    from raw_data
    qualify row_number() over (
        partition by order_id
        order by updated_at desc, created_at desc
    ) = 1
)

select * from cleaned