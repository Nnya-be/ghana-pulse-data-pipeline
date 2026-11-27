/** 
 * For each month in which at least one rental happened, show the number of new customers and 
 * the number of returning customers.
 * A new customer is one whose first-ever rental was in that month.
 * A returning customer rented in that month, but their first-ever rental was in an earlier month.
 * Count each customer once per month. Show the month as the first day of the month, and order by month.
*/

/**
 * Plan:
 * 1) Find each customer and their rental dates.
 * 2) Take each customer and the very first retals of them.
 * 3) Group each month and check if the users first rental is before then it's a returning customer.
 */
with customer_rental_details as (
	select c.customer_id , r.rental_date , r.rental_id  ,
	min(r.rental_date ) over (partition by c.customer_id order by r.rental_date asc) as customer_first_rental
	from customer c 
		join rental r 
		on r.customer_id  = c.customer_id 
),
customer_new_or_old as (
	select  customer_id, rental_date, customer_first_rental ,
	min(rental_date) over(partition by rental_date order by rental_date) as month_dates
	from customer_rental_details
)
select customer_id, month_dates, rental_date
from customer_new_or_old
group by month_dates, customer_id,rental_date
order by rental_date

