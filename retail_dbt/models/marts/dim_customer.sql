with customers as (

    select
        customer_id as customer_key,
        first_name,
        last_name,
        email,
        mobile_number,
        is_marketing_opted_in,
        is_email_verified,
        sex
    from {{ ref('stg_customers') }}

),

guest_member as (

    select
        -1 as customer_key,
        'guest' as first_name,
        cast(null as varchar) as last_name,
        cast(null as varchar) as email,
        cast(null as varchar) as mobile_number,
        false as is_marketing_opted_in,
        false as is_email_verified,
        'unknown' as sex

)

select * from customers
union all
select * from guest_member