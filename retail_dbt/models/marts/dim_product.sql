select
    product_id as product_key,
    product_name,
    brand,
    product_category,
    product_subcategory
from {{ ref('stg_products') }}