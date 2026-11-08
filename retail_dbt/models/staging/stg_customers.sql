with raw_data as (
    select * from {{ ref('snp_customers') }}
),

cleaned as (
    select
        dbt_scd_id as customer_version_id
        , customer_id
        , lower(trim(first_name)) as first_name
        , lower(trim(last_name)) as last_name
        , lower(trim(email)) as email
        , trim(mobile_number) as mobile_number
        , case
            when lower(trim(marketing_opt_in_flag)) in ('1', 'yes', 'true') then true
            when lower(trim(marketing_opt_in_flag)) in ('0', 'no', 'false') then false
        end as is_marketing_opted_in
        , case
            when lower(trim(email_verified_flag)) in ('1', 'yes', 'true') then true
            when lower(trim(email_verified_flag)) in ('0', 'no', 'false') then false
        end as is_email_verified
        , lower(trim(sex)) as sex
        , created_at
        , updated_at
        , dbt_valid_from as valid_from
        , dbt_valid_to as valid_to
        , dbt_valid_to = cast('9999-12-31' as timestamp) as is_current
    from raw_data
)

select * from cleaned