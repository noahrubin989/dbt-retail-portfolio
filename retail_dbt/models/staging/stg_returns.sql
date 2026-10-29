with raw_data as (
    select * from {{ source('raw', 'returns')}}
), 

cleaned as (
    select 
        return_id
        , order_line_id
        , quantity_returned
        , return_timestamp
        , created_at
        , updated_at
    from raw_data
)
-- semi-redundant but follows structure of prior ones
select * from cleaned