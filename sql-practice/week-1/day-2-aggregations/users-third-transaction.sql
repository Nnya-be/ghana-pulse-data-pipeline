WITH ranked_date AS (
  SELECT t.user_id, 
  t.spend, t.transaction_date, 
  ROW_NUMBER() OVER(PARTITION BY t.user_id ORDER BY t.transaction_date) as number
FROM transactions AS t
)
SELECT user_id, spend, transaction_date
FROM ranked_date
WHERE number = 3;