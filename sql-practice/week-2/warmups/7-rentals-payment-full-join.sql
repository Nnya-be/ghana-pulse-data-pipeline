--For each month, show the number of rentals and the number of payments, 
--including months that have only one of the two.
with rentals_per_month as (
    select date_trunc('month', rental_date)::date as month,
           count(*) as number_of_rentals
    from rental
    group by month
),
payments_per_month as (
    select date_trunc('month', payment_date )::date as month,
           count(*) as number_of_payments
    from payment
    group by month
)
select coalesce(r.month, p.month) as month,
       coalesce(r.number_of_rentals, 0) as number_of_rentals,
       coalesce(p.number_of_payments, 0) as number_of_payments
from rentals_per_month r
full join payments_per_month p on r."month" = p."month" 
order by month;
