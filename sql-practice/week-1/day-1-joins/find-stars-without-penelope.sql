-- List actors who has appeared in a file with PENELOPE GUINESS but not herself.
select * from actor a 
where a.first_name = 'PENELOPE' and a.last_name = 'GUINESS'

select * 
from film_actor fa 
where fa.actor_id = 1

select a.actor_id , 
	a.first_name , a.last_name , count(fa1.film_id ) as film_together
from film_actor as fa1
join film_actor as fa2
	on fa1.film_id = fa2.film_id
	join actor as a
		on fa2.actor_id = a.actor_id 
		join actor  as p
			on p.actor_id = fa1.actor_id 
where p.first_name = 'PENELOPE' 
		and p.last_name = 'GUINESS'
		and fa2.actor_id != p.actor_id 
group by a.actor_id 
order by 4 desc;
