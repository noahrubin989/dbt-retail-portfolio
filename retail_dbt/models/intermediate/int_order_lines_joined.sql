with order_lines as (
    select * from {{ ref('stg_order_lines') }}
),

orders as (
    select * from {{ ref('stg_orders') }}
),

joined as (
    select
        ol.order_line_id
        , ol.order_id
        , ol.product_id
        , ol.quantity
        , ol.unit_price
        , o.customer_id
        , o.store_id
        , o.payment_method_id
        , o.order_timestamp
        , ol.created_at as line_created_at
        , ol.updated_at as line_updated_at
    from order_lines as ol
    -- inner join on purpose: lines with no matching order cannot become fact rows
    -- (no date, store or payment method), so they are dropped here and reported
    -- by the relationships test on stg_order_lines
    inner join orders as o
        on ol.order_id = o.order_id
)

select * from joined