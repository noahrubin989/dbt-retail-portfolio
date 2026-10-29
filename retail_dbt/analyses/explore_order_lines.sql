select
    order_line_id
    , order_id
    , product_id
    , quantity
    , cast(replace(trim(unit_price), '$', '') as decimal(10,2)) as unit_price    , created_at
    , updated_at
from {{ source('raw', 'order_lines') }}
