with dates as (

    select cast(generate_series as date) as date_day
    from generate_series('2020-01-01'::date, '2075-12-31'::date, interval 1 day)

)

select
    cast(strftime(date_day, '%Y%m%d') as integer) as date_key
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