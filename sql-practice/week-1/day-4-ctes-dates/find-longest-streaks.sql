--For each customer, find their longest streak of consecutive calendar days with at least one rental. 
--Show the customer, the streak’s start date, its end date and its length in days.
--1, select distinct rental details of customer
--2, assign row numbers to each customers rentals 
--3, subtract row numbers from dates
--4, group and select lowest and highest day
--5, rank and select only top streaks.

with customer_rental_details as (
	select distinct cus.customer_id , cus.first_name || ' ' || cus.last_name as customer_name, 
	ren.rental_date::date  
	from customer as cus 
	join rental as ren 
		on ren.customer_id  = cus.customer_id 
), 
assign_ranks_to_rental as (
	select customer_id , customer_name, 
	rental_date,
	row_number() over(partition by customer_id order by rental_date) as rank_of_rent
	from customer_rental_details 
),
calculate_date_streak as (
	select customer_id ,
	customer_name , rental_date , rank_of_rent, 
	rental_date - rank_of_rent::int  as streak_key
	from assign_ranks_to_rental
	),
streaks as (
	 select customer_id,
	 customer_name,
	 min(rental_date ) as streak_start,
	 max(rental_date) as streak_end,
	 count(*) as streak_days
	 from calculate_date_streak 
	 group by streak_key, customer_id, customer_name
),
top_streaks as (
	select customer_id,
	customer_name,
	streak_start ,
	streak_end,
	streak_days,
	rank() over(partition by customer_id order by streak_days desc, streak_start) as streak_ranks
	from streaks
)
select customer_id,
	customer_name,
	streak_start ,
	streak_end,
	streak_days
from top_streaks 
where streak_ranks = 1
order by customer_name, customer_id;

