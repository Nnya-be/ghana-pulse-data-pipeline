--For each customer with more than 60 rentals, show the number of rentals, 
--the number of different films they rented, and the date of their latest rental.

select c.customer_id ,
c.first_name || ' ' || c.last_name as customer_name,
count(*) as number_of_rentals,
count(distinct i.film_id ) as different_films_number,
max(r.rental_date)::date as latest_rental -- for readability sake, it's casted to date.
from customer as c
	join rental as r
	on r.customer_id  = c.customer_id 
		join inventory i 
		on i.inventory_id  = r.inventory_id 
group by c.customer_id 
having count(*) > 60
order by number_of_rentals desc, customer_id