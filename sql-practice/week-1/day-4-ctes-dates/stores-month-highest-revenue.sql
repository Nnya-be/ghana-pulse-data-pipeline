--For each store, find the month with the highest revenue, 
--and show how far above that store’s average monthly revenue it was.
with store_payment_details as (
	select s.store_id ,
	p.payment_id ,
	p.amount , p.payment_date ,
	date_trunc('month', p.payment_date) as payment_month
	from store as s 
		join inventory i 
		on i.store_id  = s.store_id 
			join rental r 
			on r.inventory_id  = i.inventory_id 
				join payment p 
				on p.rental_id = r.rental_id 
), 
store_highest_revenue as (
	select store_id, payment_month, 
	sum(amount) as revenue
	from store_payment_details 
	group by store_id, payment_month 
),
montly_payment_highest_deviation as (
	select store_id,
	payment_month,
	revenue,
	round(avg(revenue) over (partition by store_id), 2) as avg_monthly_revenue,
	row_number() over (partition by store_id order by revenue desc, payment_month ) as month_rank
	from store_highest_revenue 
)
select
store_id, payment_month, 
revenue, avg_monthly_revenue, 
(revenue - avg_monthly_revenue ) as above_average
from montly_payment_highest_deviation
where month_rank  = 1
order by store_id
