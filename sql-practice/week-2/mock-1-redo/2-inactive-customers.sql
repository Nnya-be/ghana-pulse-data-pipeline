--Find the customers who have rented films from at least 5 different categories, and whose most 
--recent rental was more than 90 days before the latest rental in the whole rental table.

/**
 * Show the customer ID, the number of different categories they've rented from, 
 * the date of their most recent rental (as a date), 
 * and the number of days between that date and the latest rental in the table. 
 * Order by that number of days, largest first.
 */

/**
 * 1) find all customers with their rented films and their categories.
 * 2) filter by distinct categories rented by a user.
 * 3) Order the date in desc and select the top one as the recent rental.
 * 4) find the max of all the recent rental dates.
 * 5) order by the diff in rental dates.
 */
-- layer 1: one row per customer, with the categories they rented from and their latest rental
with customer_activity as (
    select r.customer_id,
           count(distinct fc.category_id) as categories_rented,
           max(r.rental_date)::date as last_rental_date
    from rental r
    join inventory i on i.inventory_id = r.inventory_id
    join film_category fc on fc.film_id = i.film_id
    group by r.customer_id
),
-- layer 2: the same rows, plus the latest rental in the whole table (computed before any filter)
with_table_latest as (
    select customer_id, categories_rented, last_rental_date,
           (select max(rental_date)::date from rental) as table_latest_date
    from customer_activity
)
-- layer 3: keep the customers that match, with the gap in days
select customer_id,
       categories_rented,
       last_rental_date,
       table_latest_date - last_rental_date as days_inactive
from with_table_latest
where categories_rented >= 5
  and table_latest_date - last_rental_date > 90
order by days_inactive desc, customer_id;
