-- find films without copies in inventory in 2 ways.
select f.film_id , f.title 
from film as f
left join  inventory as i
	on f.film_id = i.film_id
where i.film_id is null;

select f.film_id, f.title
from film as f 
where not exists (
	select 1
	from inventory as i
	where i.film_id  = f.film_id 
)

