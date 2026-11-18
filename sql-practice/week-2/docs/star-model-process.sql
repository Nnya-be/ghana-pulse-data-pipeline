select count(*) 
from rental;
--ans: 51,805

select r.rental_id ,
count(*) as rental_count
from rental r
	join payment p  on p.rental_id  = r.rental_id 
group by r.rental_id 
having count(*) >= 2;
--ans: rental 4,591 has 6 counts

select * from payment where rental_id = 4591 order by payment_date;

select *
from payment 
where rental_id is null;
-- ans: 0

select count(*) 
from rental 
where return_date is null
-- ans: 241

select count(*)
from rental r
	join payment p  on p.rental_id  = r.rental_id
where p.customer_id = r.customer_id 
-- ans: 51,056

/*
 * customer_key
 * customer_id
 * email
 * first_name
 * last_name
 * phone
 * country
 * city
 * district
 * address
 * postal_code
 * created_since
 * is_active
 */
select * from customer limit 1;
select count(*) from customer; -- 999

/**
 * dim_film
 * film_key, title, description, release_year, language, original_language,length, rating
 * rental_duration, rental_rate, replacement_cost,
 * 
 */

/**
 * dim_store
 * store_key
 * store_id
 * store_name(store_id and city)
 * manager_name(from staff first_name and last_name)
 * address
 * district 
 * city
 * postal_code   //Manager and phone can change. SCD type to be decided on Tuesday
 * country
 * phone
 */

/**
 * dim_staff
 * staff_key
 * staff_id
 * first_name
 * last_name
 * email //Email and active status can change. SCD type to be decided on Tuesday
 * is_active
 */

/**
 * dim_category
 * category_key
 * category_id 
 * category_name
 */
select count(*) from category; -- 16

/**
 * bridge_film_category
 * film_key
 * category_key
 */
select count(*) from film_category; ---2,367
/**
 * dim_date
 * date_key
 * full_date
 * day_of_week_number
 * day_name
 * month_number
 * month_name
 * day_of_month
 * calendar_year
 * quarter
 * is_weekend
 */

/**
 * fact_rental
 * rental_id
 * inventory_id
 * customer_key
 * film_key
 * store_key
 * staff_key
 * return_date_key
 * rental_date_key
 * measurements(rental_count, days_kept)
 */



