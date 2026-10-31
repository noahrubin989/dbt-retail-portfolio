select
    transaction_type,
    count(*) as n,
    sum(quantity) as units,
    min(quantity) as min_qty,
    max(quantity) as max_qty
from {{ ref('fact_sales') }}
group by 1