with customer_rental_dates as (
select c.customer_id,
concat(c.first_name , ' ', c.last_name ) as customer_name,
 r.rental_date ,
 lag(r.rental_date ) over w as prev_rental_date,
r.rental_date::date -  lag(r.rental_date::date ) over w as days_since_previous,
r.rental_id 
from customer as c
join rental as r
	on c.customer_id  = r.customer_id 
window w as (partition by c.customer_id order by r.rental_date, r.rental_id )
) select * from customer_rental_dates
order by customer_id, rental_date, rental_id;
