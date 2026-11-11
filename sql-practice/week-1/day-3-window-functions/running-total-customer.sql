
select c.customer_id, p.payment_id, 
concat(c.first_name, ' ', c.last_name) as customer_name,
p.payment_date, p.amount,
sum(p.amount) over(partition by c.customer_id order by p.payment_date , p.payment_id
rows between unbounded preceding and current row
) as running_total
from payment as p
join customer as c 
	on p.customer_id = c.customer_id 
order by c.customer_id , p.payment_date, p.payment_id 
