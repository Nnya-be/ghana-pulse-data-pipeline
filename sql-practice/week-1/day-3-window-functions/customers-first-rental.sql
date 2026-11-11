with customer_rentals as (
	select cus.customer_id , 
	concat(cus.first_name , ' ', cus.last_name ) as customer_name,
		row_number() over(partition by cus.customer_id order by r.rental_date , r.rental_id ) as date_rank,
	f.film_id , f.title ,
	r.rental_date  
	from rental as r
	join customer as cus
		on cus.customer_id  = r.customer_id
		join inventory as i
			on r.inventory_id = i.inventory_id
			join film as f
				on f.film_id = i.film_id 
)
select customer_id ,customer_name,title, rental_date
from customer_rentals 
where date_rank = 1
order by customer_name, title;