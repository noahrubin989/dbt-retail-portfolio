with sales as (

    select
        order_line_id
        , cast(null as varchar) as return_id
        , 'sale' as transaction_type
        , order_id
        , product_id as product_key
        , customer_id
        , coalesce(store_id, -1) as store_key
        , coalesce(payment_method_id, -1) as payment_method_key
        , order_timestamp as transaction_timestamp
        , quantity
        , unit_price
    from {{ ref('int_order_lines_joined') }}

),

returns as (

    select
        order_line_id
        , cast(return_id as varchar) as return_id
        , 'return' as transaction_type
        , order_id
        , product_id as product_key
        , customer_id
        , coalesce(store_id, -1) as store_key
        , coalesce(payment_method_id, -1) as payment_method_key
        , return_timestamp as transaction_timestamp
        , quantity
        , unit_price
    from {{ ref('int_returns_signed') }}

),

combined as (

    select * from sales
    union all
    select * from returns

),

customer_versions as (

    select
        customer_key
        , customer_id
        , valid_from
        , valid_to
    from {{ ref('dim_customer') }}

),

-- Each row gets the customer version valid when it happened. Walk-ins (null
-- customer_id) go to Guest; a real customer with no version stays null so the
-- not_null test catches it.
with_customer as (

    select
        combined.*
        , case
            when combined.customer_id is null then '-1'
            else cv.customer_key
        end as customer_key
    from combined
    left join customer_versions as cv
        on combined.customer_id = cv.customer_id
        and combined.transaction_timestamp >= cv.valid_from
        and combined.transaction_timestamp < cv.valid_to

)

select
    order_line_id
    , return_id
    , transaction_type
    , order_id
    , product_key
    , customer_key
    , store_key
    , payment_method_key
    , {{ date_to_key('transaction_timestamp') }} as date_key
    , quantity
    , unit_price
    , quantity * unit_price as line_amount
from with_customer
