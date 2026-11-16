--Show customers who have spent more than 150 in total, with their number of payments and average payment. 
--Filter the total with HAVING, and note why it can’t go in WHERE
with customer_spending_details as (
	select c.customer_id ,
	c.first_name || ' ' || c.last_name  as customer_name,
	sum(p.amount) as amount_total,
	round(avg(p.amount), 2) as average_spent,
	count(*) as payment_number
	from customer as c
		join payment as p 
		on c.customer_id = p.customer_id 
	group by c.customer_id
	having sum(p.amount) > 150
)
select * from customer_spending_details
order by customer_name;
--Can't use where becauses where is executed before the aggregations are performed, so we can't have the total, and we can't also use an aggregate function in where as well.
