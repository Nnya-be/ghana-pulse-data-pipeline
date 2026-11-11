

with rented_film_with_cat as (
select 
f.film_id ,
f.title, c.category_id  , c.name,
count(r.rental_id ) as rental_count
from rental as r
join inventory as i 
on i.inventory_id  = r.inventory_id 
	join film_category as fc
	 on fc.film_id  = i.film_id 
	 	join film as f
	 	on f.film_id  = i.film_id 
	 		join category as c
	 		on fc.category_id = c.category_id
group by f.film_id, c.category_id  
),
rental_rank as (
select *,
dense_rank() over(partition by category_id order by rental_count desc) as film_ranks
from rented_film_with_cat 
)
select * from rental_rank 
where film_ranks <=3
order by name , film_ranks ;