--Find the customers who have rented at least one film in each of 
--three categories: Horror, Comedy and Action. Each customer appears once.
with customer_rental_details as (
	select c.customer_id, c2.name,
	c.first_name || ' ' || c.last_name as customer_name
	from customer c 
	join rental r 
	on r.customer_id  = c.customer_id 
		join inventory i 
		on r.inventory_id  = i.inventory_id 
			join film_category fc 
			on i.film_id  = fc.film_id 
				join category c2 
				on c2.category_id  = fc.category_id 
	where "name" = 'Horror' or "name" = 'Comedy' or "name" = 'Action'
)
select customer_id, customer_name
from customer_rental_details 
group by customer_id, customer_name 
having count(distinct name) = 3
order by customer_name, customer_id 
