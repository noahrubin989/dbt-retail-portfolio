with raw_data as (
    select * from {{ source('raw', 'products')}}
), 

cleaned as (
    select 
        product_id
        , lower(trim(product_name)) as product_name
        , lower(trim(brand)) as brand
        , lower(trim(product_category)) as product_category
        , lower(trim(product_subcategory)) as product_subcategory
        , created_at
        , updated_at
    from raw_data
)

select * from cleaned