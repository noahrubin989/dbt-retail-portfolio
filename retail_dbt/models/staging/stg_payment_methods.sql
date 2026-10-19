with raw_data as (
    select * 
    from {{ source('raw', 'payment_methods') }}
), cleaned as (
    select 
    payment_method_id
    , lower(trim(method_name)) as method_name
    , case lower(trim(is_active))
        when 'y' then true
        when 'n' then false
    end as is_active
    from raw_data
)
select * from cleaned
