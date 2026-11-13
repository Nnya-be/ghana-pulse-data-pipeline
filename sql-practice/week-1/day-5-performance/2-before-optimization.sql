-- before optimizations
explain (analyze, buffers)
select count(*) as total_transactions,
sum(amount) as total_amount
from perf.transactions
where created_at::date = '2026-03-15';

--Execution Time: 111.838 ms