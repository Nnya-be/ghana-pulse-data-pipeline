--For each customer who has made at least one payment, find the month 
--in which they spent the most (the total of their payments in that month).

/**Show the customer ID, that month (as the first day of the month), 
 * the amount spent in that month, and that amount as a percentage of the customer's total spend, 
 * rounded to 2 decimal places. If two months tie, take the earlier one. One row per customer.
 */

/**
 * 1)find every customer and their payments.
 * 2)For each customer, sum their monthly payment and the total of all the customers spend.
 * 3)Rank their sum and group by the customer to get one row for the customer.
 */
-- layer 1: one row per customer per month, with that month's total
with monthly_spend as (
    select p.customer_id,
           date_trunc('month', p.payment_date)::date as payment_month,
           sum(p.amount) as month_total
    from payment p
    group by p.customer_id, date_trunc('month', p.payment_date)::date
),
-- layer 2: the same rows, plus each month's rank within its customer, and the customer's total
ranked_months as (
    select customer_id, payment_month, month_total,
           row_number() over (partition by customer_id
                              order by month_total desc, payment_month) as month_rank,
           sum(month_total) over (partition by customer_id) as customer_total
    from monthly_spend
)
-- layer 3: keep only each customer's best month, with its share of their spend
select customer_id,
       payment_month,
       month_total,
       round(100.0 * month_total / customer_total, 2) as pct_of_customer_spend
from ranked_months
where month_rank = 1
order by customer_id;