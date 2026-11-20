--For each film category, show how many films it has, 
--and how many of those films were never rented.
with film_rentals as (
    select f.film_id,
           count(r.rental_id) as rental_count
    from film f
    left join inventory i on i.film_id = f.film_id
    left join rental r on r.inventory_id = i.inventory_id
    group by f.film_id
)
select c.category_id,
       c.name as category_name,
       count(*) as number_of_films,
       count(*) filter(where rental_count = 0) as never_rented_films
from film_category fc
join film_rentals fr on fr.film_id = fc.film_id
join category c on c.category_id = fc.category_id
group by c.category_id
order by c.name;
