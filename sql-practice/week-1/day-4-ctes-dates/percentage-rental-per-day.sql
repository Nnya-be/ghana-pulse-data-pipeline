-- Show the number of rentals for each day of the week, 
-- Monday first, with each day’s share of all rentals as a percentage.
-- 1, show all rentals with the day of the week showing
-- 2, group by the day of the weeks and count the number of entires.
-- 3, calculate percentage of each day.

with all_rentals_days as (
	select rental_id , 
	rental_date ,
	extract (isodow from rental.rental_date) as day_number,
	to_char( rental_date ,'FMDay') as day_ofw
	from rental
), 
sum_days_rentals as (
	select  day_ofw,
	day_number,
	count(*) as total_rents
	from all_rentals_days
	group by day_number, day_ofw
)
select *,
round((100.0 * total_rents)/ sum(total_rents) over (), 2) as rental_pctg
from sum_days_rentals 
order by day_number
;
