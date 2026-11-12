--Generate every date from the first rental date to the last, using a recursive CTE. 
--Then list the dates on which no rentals were made.
with recursive calendar as (
	select min(rental_date)::date as day from rental -- start condition
	union all 
	select day + 1 -- incremantal condition
	from calendar 
	where day < (select max(rental_date)::date from rental) -- end condition
),
merge_calendar as (
	select day from calendar as can
	left join rental as ren
		on can.day = ren.rental_date::date 
	where ren.rental_id is null	
)
select * from merge_calendar
	order by day;
