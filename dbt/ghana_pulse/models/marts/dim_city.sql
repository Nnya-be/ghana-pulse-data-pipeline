select 
    {{ dbt_utils.generate_surrogate_key(['city_slug']) }} as city_key,
    city_slug,
    city as city_name,
    region,
    latitude,
    longitude
from {{ ref('cities')}}