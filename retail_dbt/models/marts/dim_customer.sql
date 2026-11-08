with versions as (

    select
        customer_id,
        first_name,
        last_name,
        email,
        mobile_number,
        is_marketing_opted_in,
        is_email_verified,
        sex,
        valid_from,
        valid_to,
        is_current,
        row_number() over (partition by customer_id order by valid_from) = 1 as is_first_version
    from {{ ref('stg_customers') }}

),

customers as (

    select
        {{ dbt_utils.generate_surrogate_key(['customer_id', 'valid_from']) }} as customer_key,
        customer_id,
        first_name,
        last_name,
        email,
        mobile_number,
        is_marketing_opted_in,
        is_email_verified,
        sex,
        -- The first version also covers sales from before snapshotting began.
        case
            when is_first_version then cast('1900-01-01' as timestamp)
            else valid_from
        end as valid_from,
        valid_to,
        is_current
    from versions

),

guest_member as (

    select
        '-1' as customer_key,
        -1 as customer_id,
        'guest' as first_name,
        cast(null as varchar) as last_name,
        cast(null as varchar) as email,
        cast(null as varchar) as mobile_number,
        false as is_marketing_opted_in,
        false as is_email_verified,
        'unknown' as sex,
        cast('1900-01-01' as timestamp) as valid_from,
        cast('9999-12-31' as timestamp) as valid_to,
        true as is_current

)

select * from customers
union all
select * from guest_member
