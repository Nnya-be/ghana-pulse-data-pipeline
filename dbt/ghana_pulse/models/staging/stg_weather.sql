with source as (

    select * from {{ source('raw', 'weather_daily') }}

),

renamed as (

    select
        city_slug,
        time as weather_date,
        temperature_2m_max as temp_max_c,
        temperature_2m_min as temp_min_c,
        precipitation_sum as rainfall_mm,
        weathercode as weather_code
    from source

)

select * from renamed