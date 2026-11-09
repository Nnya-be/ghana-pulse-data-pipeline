--get every film title with the name of it's language
select f.title  , l.name
from film as f
left join language as l
	on f.language_id = l.language_id ;
