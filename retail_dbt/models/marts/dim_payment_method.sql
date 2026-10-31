with payment_methods as (

    select
        payment_method_id as payment_method_key,
        method_name,
        is_active
    from {{ ref('stg_payment_methods') }}

),

unknown_member as (

    select
        -1 as payment_method_key,
        'unknown' as method_name,
        false as is_active

)

select * from payment_methods
union all
select * from unknown_member