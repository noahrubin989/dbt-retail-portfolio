with sales as (

    select
        order_line_id,
        order_id,
        product_id as product_key,
        coalesce(customer_id, -1) as customer_key,
        coalesce(store_id, -1) as store_key,
        coalesce(payment_method_id, -1) as payment_method_key,
        cast(strftime(order_timestamp, '%Y%m%d') as integer) as date_key,
        quantity,
        unit_price
    from {{ ref('int_order_lines_joined') }}

)

select * from sales