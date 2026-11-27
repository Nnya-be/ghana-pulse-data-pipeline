/**
 * For each film category, find the most-rented film. A film's rentals are the number of rentals of 
 * all its copies. If two films tie, take the one that comes first alphabetically by title.
 * Show the category name, the film title, its number of rentals, and that number as a percentage 
 * of all rentals of films in that category, rounded to 2 decimal places. One row per category.
 * A film that belongs to several categories counts in each of them.
*/

/**
 * Plan:
 * 1)Find all rented films and their categories.
 * 2)Sum each films rental, group by the category and select the highest and sum all the films in that category.
 * 3)Calculate it's percentage and round to 2 decimal places.
 */
with film_details as (
	select  fc.category_id ,f.film_id, f.title  , r.rental_id 
	from film f
		join inventory i 
		on i.film_id  = f.film_id 
			join rental r 
			on r.inventory_id = i.inventory_id 
				join film_category fc 
				on fc.film_id  = i.film_id 
),
film_rental_count as (
	select category_id ,
	film_id , title, 
	count(*) as film_count
	from film_details
	group by film_id, title, category_id 
)
select  *
from film_rental_count
join category c 
on c.category_id  = c.category_id 
				
				
