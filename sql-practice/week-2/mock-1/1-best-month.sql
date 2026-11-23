--For each customer who has made at least one payment,
-- find the month in which they spent the most (the total of their payments in that month).
with customer_payment as (
	select c.customer_id, c.first_name || ' ' || c.last_name as customer_name,
	p.amount,
	date_trunc('month', p.payment_date) as payment_month
	from customer as c 
		join payment as p
		on p.customer_id  = c.customer_id 
),
payment_ratings as (
	select distinct customer_id, customer_name,
	amount, sum(amount) over(partition by payment_month order by customer_id) as customer_monthly_sum, payment_month
	from customer_payment 
),
highest_month as (
	select customer_id, customer_name,
	amount, customer_monthly_sum, 
	payment_month
	from payment_ratings 
)
select * from highest_month;

--unfinished
