create schema if not exists raw;

create table raw.weather_daily (
    city_slug          text not null,
    time               date not null,
    temperature_2m_max double precision,
    temperature_2m_min double precision,
    precipitation_sum  double precision,
    weathercode        smallint,
    primary key (city_slug, time)
);

create table raw.fx_rates (
    date  date not null,
    base  char(3) not null,
    quote char(3) not null,
    rate  numeric not null,
    primary key (date, base, quote)
);

select count(*) from raw.weather_daily;                                  -- 12176
select count(*) from raw.fx_rates;                                       -- 516
select min(time), max(time), count(distinct city_slug) from raw.weather_daily;  -- 2024-10-01, 2026-10-31, 16
select version();                                                        -- should say PostgreSQL 18

select count(*) from dbt_dev.stg_weather;   -- 12176
select count(*) from dbt_dev.stg_fx;        -- 516


