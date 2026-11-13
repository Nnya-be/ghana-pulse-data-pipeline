create index create_at_idx on perf.transactions (created_at);

-- running after creating the index on the created.
explain (analyze, buffers)
select count(*) as total_transactions,
sum(amount) as total_amount
from perf.transactions
where created_at::date = '2026-03-15';

--Execution Time: 113.373 ms
-- created the query to check on the created at itself.
explain (analyze, buffers)
select count(*) as total_transactions,
sum(amount) as total_amount
from perf.transactions
where created_at  >= '2026-03-15' and created_at < '2026-03-16';
--Execution Time: 3.494 ms
