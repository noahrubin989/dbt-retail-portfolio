select
    transaction_type,
    order_line_id,
    return_id,
    count(*) as n
from {{ ref('fact_sales') }}
group by 1, 2, 3
having count(*) > 1