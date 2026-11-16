--show monthly revenue per store, with a subtotal for each store and a grand total, using ROLLUP.
with payment_details as (
	select s.store_id,
           date_trunc('month', p.payment_date) as payment_month,
           p.amount
	from store as s 
		join inventory as i 
		on i.store_id  = s.store_id 
			join rental as r
			on r.inventory_id = i.inventory_id 
				join payment as p
				on p.rental_id = r.rental_id 
	)
select store_id,
       case
           when grouping(store_id) = 1 then 'Grand Total'
           when grouping(payment_month) = 1 then 'Store_Total'
           else to_char(payment_month, 'YYYY-MM')
       end as period,
       sum(amount) as revenue
from payment_details
group by rollup(store_id, payment_month)
order by store_id, payment_month;

