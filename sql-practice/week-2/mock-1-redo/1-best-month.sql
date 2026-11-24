--For each customer who has made at least one payment, find the month 
--in which they spent the most (the total of their payments in that month).

/**Show the customer ID, that month (as the first day of the month), 
 * the amount spent in that month, and that amount as a percentage of the customer's total spend, 
 * rounded to 2 decimal places. If two months tie, take the earlier one. One row per customer.
 */

/**
 * 1)find every customer and their payments.
 * 2)For each customer, sum their monthly payment and the total of all the customers spend.
 * 3)Rank their sum and group by the customer to get one row for the customer.
 */
with customer_payment_details as (
	select c.customer_id , p.amount ,
	date_trunc('month', p.payment_date ) as payment_date
	from customer c 
		join payment p 
		on c.customer_id  = p.customer_id 
),
customer_payment_sum as (
	select distinct customer_id,
	sum(amount) over(partition by customer_id order by payment_date) as montly_sum,
	payment_date
	from customer_payment_details 
),
customer_montly_total_ranks as (
	select customer_id, payment_date,montly_sum,
	rank() over(partition by customer_id order by montly_sum desc) as payment_rank,
	sum(montly_sum) over(partition by customer_id) as customer_total_spend
	from customer_payment_sum 
)
select customer_id, montly_sum, customer_total_spend,
round(100 * (montly_sum/customer_total_spend),2) as customer_spend_avg
from customer_montly_total_ranks  
where payment_rank = 1
order by customer_id
