--For each payment, show the customer’s next payment amount, 
--and label it “higher”, “lower” or “same” compared with the current payment.
with next_payment_details as (
	select customer_id, payment_id,payment_date,
	amount,
	lead(amount) over(w) as next_payment
from payment
window w as (partition by customer_id order by payment_date, payment_id)
)
select customer_id, payment_id,
payment_date,amount, next_payment, 
case 
	when next_payment is null then 'last_payment'
	when next_payment > amount then 'higher'
	when next_payment < amount then 'lower'
	else 'same'
end as next_vs_current
from next_payment_details
order by customer_id, payment_date, payment_id;