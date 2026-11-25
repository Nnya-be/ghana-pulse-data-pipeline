with spine as (
    {{
        dbt_utils.date_spine(
            datepart="day",
            start_date="cast('2024-10-01' as date)",
            end_date="cast('2028-01-01' as date)"
        )
    }}

),
days as (
    select cast(date_day as date) as full_date
    from spine
)
select
    cast(to_char(full_date, 'YYYYMMDD') as integer) as date_key,
    full_date,
    cast(extract(isodow from full_date) as integer) as day_of_week_number,
    to_char(full_date, 'FMDay') as day_name,
    cast(extract(day from full_date) as integer) as day_of_month,
    cast(extract(month from full_date) as integer) as month_number,
    to_char(full_date, 'FMMonth') as month_name,
    cast(extract(year from full_date) as integer) as calendar_year,
    cast(extract(quarter from full_date) as integer) as quarter,
    extract(isodow from full_date) in (6, 7) as is_weekend
from days