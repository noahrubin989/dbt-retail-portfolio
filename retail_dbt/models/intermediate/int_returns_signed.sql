with sales_returns as (
    select * from {{ ref('stg_returns') }}
),

order_lines as (
    select * from {{ ref('int_order_lines_joined') }}
),

joined as (
    select
        r.return_id
        , r.order_line_id
        , ol.order_id
        , ol.product_id
        , -r.quantity_returned as quantity
        , ol.unit_price
        , ol.customer_id
        , ol.store_id
        , ol.payment_method_id
        , r.return_timestamp
        , r.created_at as return_created_at
        , r.updated_at as return_updated_at
    from sales_returns as r
    -- inner join on purpose: a return with no matching order line has no product,
    -- price, store or customer, so it cannot become a fact row. Unmatched returns
    -- are dropped here and reported by the relationships test on stg_returns
    inner join order_lines as ol
        on r.order_line_id = ol.order_line_id
)

select * from joined