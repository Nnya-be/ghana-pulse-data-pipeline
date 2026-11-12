--Group each customer’s rentals into sessions, where a new session starts 
--when more than 7 days have passed since their previous rental. For each customer, 
--show the number of sessions and the average number of rentals per session.
with customer_rental_details as (
	select cus.customer_id , cus.first_name || ' ' || cus.last_name as customer_name, 
	ren.rental_id ,
	ren.rental_date
	from customer as cus 
	join rental as ren 
		on ren.customer_id  = cus.customer_id 
),
session_groups as (
	select *,
	lag(rental_date) over w previous_date,
	rental_date::date - (lag(rental_date) over w)::date as days_interval
	from customer_rental_details 
	window w as (partition by customer_id order by rental_date, rental_id)
),
flag_new_sessions as (
	select *,
	(case when days_interval > 7 or days_interval is null then 1 else 0 end) as new_session
	from session_groups
),
sessions_sum as (
	select *,
	sum(new_session) over(
	partition by customer_id order by rental_date, rental_id
	rows between unbounded preceding and current row
	) as session_number
	from flag_new_sessions
),
number_rentals as(
	select customer_id ,
	customer_name,
	session_number,
	count(*) as rental
	from sessions_sum
	group by customer_id, session_number, customer_name
)
select customer_id,
customer_name,
count(session_number) as sessions,
round(avg(rental ), 2) as avg_rentals_per_session
from number_rentals
group by customer_id, customer_name
order by customer_name, customer_id



