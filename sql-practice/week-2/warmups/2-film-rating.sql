--for each film rating, show the number of films, the average length, 
--and how many films are longer than 120 minutes, using FILTER for the last one.
with film_rating_details as (
	select  rating ,
	count(*) as number_of_films,
	round(avg(length), 2) as average_length,
	count(*) filter(where length > 120) as films_over_120_min
	from film
	group by rating
)
select * from film_rating_details 
order by number_of_films desc, rating;
