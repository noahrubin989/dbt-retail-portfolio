with sales as (

    select
        order_line_id,
        cast(null as varchar) as return_id,
        'sale' as transaction_type,
        order_id,
        product_id as product_key,
        coalesce(customer_id, -1) as customer_key,
        coalesce(store_id, -1) as store_key,
        coalesce(payment_method_id, -1) as payment_method_key,
        cast(strftime(order_timestamp, '%Y%m%d') as integer) as date_key,
        quantity,
        unit_price
    from {{ ref('int_order_lines_joined') }}

),

returns as (

    select
        order_line_id,
        cast(return_id as varchar) as return_id,
        'return' as transaction_type,
        order_id,
        product_id as product_key,
        coalesce(customer_id, -1) as customer_key,
        coalesce(store_id, -1) as store_key,
        coalesce(payment_method_id, -1) as payment_method_key,
        cast(strftime(return_timestamp, '%Y%m%d') as integer) as date_key,
        quantity,
        unit_price
    from {{ ref('int_returns_signed') }}

),

combined as (

    select * from sales
    union all
    select * from returns

)

select
    *,
    quantity * unit_price as line_amount
from combined