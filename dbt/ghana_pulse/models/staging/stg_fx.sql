with source as (

    select * from {{ source('raw', 'fx_rates') }}

),

renamed as (

    select
        date as rate_date,
        base as base_currency,
        quote as quote_currency,
        rate
    from source

)

select * from renamed