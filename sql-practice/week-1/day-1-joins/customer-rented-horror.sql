--List the customers who have rented at least one film in the Horror category. 
--Each customer appears once. Use EXISTS
--1, list all customers and their rental and the categories.
--2, filter the horror category.
--3, filter only customers with rental.
select cus.customer_id ,
concat(cus.first_name , ' ', cus.last_name ) as customer_name
from customer as cus 
where exists(
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