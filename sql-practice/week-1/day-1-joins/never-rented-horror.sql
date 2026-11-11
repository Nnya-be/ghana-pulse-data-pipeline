--List the customers who have never rented a Horror film. Use NOT EXISTS
select cus.customer_id ,
concat(cus.first_name , ' ', cus.last_name ) as customer_name
from customer as cus 
where not exists(
select 1 from  rental as ren  
	join inventory as inv
		on ren.inventory_id = inv.inventory_id 
		join film_category as fc
			on fc.film_id = inv.film_id 
			join category as cat 
				on cat.category_id = fc.category_id 
	where ren.customer_id = cus.customer_id 
	and cat.name = 'Horror'
)order by customer_name, cus.customer_id 