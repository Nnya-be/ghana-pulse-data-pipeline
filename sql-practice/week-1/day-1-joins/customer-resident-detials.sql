--List every customer with their city and country
-- 1, list all customers with their addresses
-- 2, list all customers with their addresses and their cities
-- 3, list all customers with their addresses and their countries with cities
with customer_resident_details as (
select cus.customer_id , 
concat(cus.first_name , ' ', cus.last_name ) as customer_name,
ci.city, cn.country 
from customer as cus
join address as ad
	on ad.address_id = cus.address_id  
	join city as ci
		on ci.city_id = ad.city_id 
		join country as cn
			on cn.country_id  = ci.country_id 
)
select * from customer_resident_details 
order by customer_name 
