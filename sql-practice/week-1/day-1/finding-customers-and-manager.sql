select 
	s.store_id, ci.city,
	count(c.store_id ) as customers,
	concat(m.first_name, ' ',  m.last_name) as manager_full_name
from store as s
join address as a
	on s.address_id  = a.address_id
	join city as ci
		on ci.city_id  = a.city_id 
		join staff as m
			on m.staff_id  = s.manager_staff_id 
			join customer as c
				on s.store_id  = c.store_id 
group by s.store_id, ci.city, m.first_name , m.last_name ;
				

SELECT store_id, COUNT(*) FROM customer GROUP BY store_id;