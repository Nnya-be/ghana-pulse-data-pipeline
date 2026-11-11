with total_calculated_revenue as (
select 
to_char(date_trunc('month', p.payment_date)::date, 'YYYY-MM') as monthly,
SUM(p.amount) as total_revenue
from payment p 
group by monthly  
),
previous_monthly_calculated as (
select monthly, total_revenue ,
lag(total_revenue ) over( order by monthly ) as previous_monthly_revenue
from total_calculated_revenue 
) select *,
round(((total_revenue - previous_monthly_revenue)/ (nullif(previous_monthly_revenue,0 ) )* 100 ),2 ) as pct_change
from previous_monthly_calculated
order by monthly ;




