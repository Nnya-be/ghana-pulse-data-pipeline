--For rentals that have been returned, show per film category the average number of days a film was kept, 
--and how many rentals were returned late (kept longer than the film’s rental_duration)

with rental_with_categories as(
	select fc.category_id ,ren.rental_id,
	fc.film_id ,
	cat.name as category_name,
	ren.rental_date ,
	ren.return_date,
	fl.rental_duration ,
	(ren.return_date::date - ren.rental_date::date ) as days_kept
	from rental as ren 
		join inventory as inv
		on inv.inventory_id = ren.inventory_id
			join film_category as fc 
			on fc.film_id = inv.film_id 
				join film as fl 
				on fl.film_id = fc.film_id 
					join category as cat
					on cat.category_id = fc.category_id
	where ren.return_date is not null
),
average_rented_categories as (
	select category_id, category_name,
	count(*) filter(where days_kept > rental_duration) as late_count,
	round(avg(days_kept) , 2) as average_days_kept
	from rental_with_categories 
	group by category_id, category_name
)
select * from average_rented_categories
order by category_name;
