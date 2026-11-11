--For every film, show how many copies are in the inventory, 
--including films with no copies.
--1 find all films  and all inventory
--2 count number film copies in inventory
select fl.film_id,
fl.title ,
count(inv.inventory_id ) as number_of_copies
from film as fl
left join inventory as inv
	on fl.film_id = inv.film_id 
group by fl.film_id 
order by title