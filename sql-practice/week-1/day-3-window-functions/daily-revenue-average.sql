with daily_revenue as (
    select
         p.payment_date::date as pay_day,           -- the payment date, turned into a day
        sum(amount) as revenue      -- that day's total
    from payment as p
    group by pay_day 
)
select
    pay_day,
    revenue,
    round(
        avg(revenue) over (
            order by pay_day
            rows between 6 preceding and current row
        ), 2
    ) as moving_avg_7d
from daily_revenue
order by pay_day;