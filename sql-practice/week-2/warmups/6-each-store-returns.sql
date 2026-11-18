--For each store, count the rentals returned late (kept longer than the film’s rental_duration), 
--returned on time, and not returned yet, as three columns.

select i.store_id,
count(*) filter(where  (r.return_date::date - r.rental_date::date) > f.rental_duration) as returned_late_count,
count(*) filter(where  (r.return_date::date - r.rental_date::date) <= f.rental_duration) as returned_ontime_count,
count(*) filter(where  r.return_date is null) as not_returned_count
from store as s
	join inventory i
	on s.store_id  = i.store_id 
		join rental r 
		on r.inventory_id  = i.inventory_id 
			join film f 
			on f.film_id = i.film_id 
group by i.store_id