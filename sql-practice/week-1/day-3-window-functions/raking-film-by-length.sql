select title, rating, length,
rank() over(partition by rating order by length  desc) as length_rank
from film ;


select title, rating, length,
dense_rank() over(partition by rating order by length desc) as length_rank
from film;

select title, rating, length,
row_number() over(partition by rating order by length desc) as length_rank
from film;