with customer_payment as
(select cus.customer_id, concat(cus.first_name , ' ', cus.last_name ) as customer_name, 
sum(pay.amount) as payment_sum,
cus.store_id 
from payment as pay
join customer as cus
	on cus.customer_id = pay.customer_id
group by cus.customer_id 
),
customer_rank as (
select *, 
rank() over(partition by store_id order by payment_sum desc) as cus_rank
from customer_payment)
select * from customer_rank
where cus_rank <= 3
order by store_id , cus_rank 
;

