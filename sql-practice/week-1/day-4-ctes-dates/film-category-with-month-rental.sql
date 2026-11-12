--how one row per film category, with the number of rentals in 
---May, June, July and August 2022 as four separate columns.
with film_rental_details as (
	select c.category_id , c.name as category_name,
	r.rental_date 
	from rental as r 
		join inventory as i
		on r.inventory_id = i.inventory_id 
			join film_category as fc
			on fc.film_id   = i.film_id
				join category as c 
				on c.category_id = fc.category_id 
	where r.rental_date::date >= '2022-05-01'::date
	and r.rental_date::date <= '2022-08-31'::date
), 
film_category_group as (
	select category_id ,
	category_name,
	count(case when to_char(rental_date::date, 'YYYY-MM') = '2022-05' then rental_date end) as may_2022,
	count(case when to_char(rental_date::date, 'YYYY-MM') = '2022-06' then rental_date end) as june_2022,
	count(case when to_char(rental_date::date, 'YYYY-MM') = '2022-07' then rental_date end) as july_2022,
	count(case when to_char(rental_date::date, 'YYYY-MM') = '2022-08' then rental_date end) as august_2022
	from film_rental_details 
	group by category_id , category_name
)
select * from  film_category_group
order by category_name;


