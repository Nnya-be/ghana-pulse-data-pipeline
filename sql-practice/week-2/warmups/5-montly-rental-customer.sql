--For each month, show the number of rentals, the number of different 
--customers who rented, and the average number of rentals per customer.

select
    date_trunc('month', r.rental_date)::date as rental_month,
    count(*) as number_of_rentals,
    count(distinct r.customer_id) as distinct_customers,
    round( count(*)::numeric / count(distinct r.customer_id) , 2) as avg_rentals_per_customer
from rental as r
group by rental_month
order by rental_month;
