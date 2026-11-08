with dates as (
    select cast(date_day as date) as date_day
    from ( 
        {{ dbt_utils.date_spine(
            datepart="day",
            start_date="cast('2020-01-01' as date)",
            end_date="cast('2076-01-01' as date)"
        ) }}
    )
)

select
    {{ date_to_key('date_day') }} as date_key
    , date_day
    , extract(year from date_day) as calendar_year
    , extract(quarter from date_day) as calendar_quarter
    , extract(month from date_day) as month_number
    , monthname(date_day) as month_name
    , extract(day from date_day) as day_of_month
    , extract(isodow from date_day) as day_of_week_number
    , dayname(date_day) as day_name
    , extract(isodow from date_day) in (6, 7) as is_weekend
from dates