--Rank customers by their total spend, and show each customer’s share of all revenue as a percentage.
with customer_spend_details as (
	select customer_id, sum(amount) as customer_total_spend
	from payment
	group by customer_id
)
select customer_id, customer_total_spend,
sum(customer_total_spend) over ()  as overall_spend,
rank() over (order by customer_total_spend desc, customer_id) as rank_of_spend,
round(((100*customer_total_spend)  / sum(customer_total_spend)  over ()), 2) as pct_spend
from customer_spend_details 
order by rank_of_spend