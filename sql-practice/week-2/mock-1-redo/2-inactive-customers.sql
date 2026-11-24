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
with all_customer_rental_details as (
	select c.customer_id, fc.category_id,
	r.rental_date
	from customer c 
		join rental r 
		on c.customer_id = r.customer_id 
			join inventory i 
			on r.inventory_id = i.inventory_id 
				join film_category fc 
				on i.film_id = fc.film_id 
),
customer_with_more_categories as (
	select  category_id, customer_id,rental_date
	from all_customer_rental_details
)
select * from customer_with_more_categories
order by customer_id

