select
    c.name as category,
    f.title,
    f.rental_rate,
    round(avg(f.rental_rate) over (partition by c.category_id ), 2) as category_avg_rate,
    round(f.rental_rate - avg(f.rental_rate) over (partition by c.category_id ), 2) as diff_from_avg
from film as f
join film_category as fc on f.film_id  = fc.film_id 
join category as c on c.category_id = fc.category_id 
order by c.name , f.title  ;