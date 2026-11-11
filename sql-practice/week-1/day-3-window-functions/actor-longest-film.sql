with longest_film_rank as (
	select ac.actor_id ,
	concat( ac.first_name , ' ', ac.last_name ) as actor_name,
	f.length,
	f.title as film_title,
	row_number() over(partition by ac.actor_id order by f.length desc, f.title ) as longest_rank
	from actor as ac
	join film_actor as  fa
		 on fa.actor_id  = ac.actor_id 
		 join film as f 
		 	on fa.film_id = f.film_id 
) select actor_id , actor_name, film_title, length
from longest_film_rank 
where longest_rank = 1
order by actor_name ;