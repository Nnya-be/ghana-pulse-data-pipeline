--For every customer, 
--show how many rentals they made in July 2022, 
--including customers who made none.
--1, all customers with all rentals
--2, filter rental dates to only july 2022
--3, count each customers rentals on that day.
select cu.customer_id ,
concat(cu.first_name , ' ', cu.last_name ) as customer_name,
count(ren.rental_id ) as number_of_rents
from customer as cu 
left join rental as ren
	on ren.customer_id  = cu.customer_id 
	and to_char(ren.rental_date::date, 'YYYY-MM') = '2022-07'
group by cu.customer_id 
order by number_of_rents desc