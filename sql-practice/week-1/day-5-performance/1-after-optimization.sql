create index customer_id_idx on perf.transactions (customer_id); 
-- run after adding index on customer_id
explain (analyze, buffers) 
select * from perf.transactions
where customer_id = 4242 
and to_char(created_at::date, 'YYYY-MM') = '2026-03'
order by created_at desc;

--Execution Time: 0.731 ms

-- comparing without casting and converting
explain (analyze, buffers) 
select * from perf.transactions
where customer_id = 4242 
and created_at >= '2026-03-01' and created_at < '2026-04-01'
order by created_at desc;

--Execution Time: 0.309 ms
create index comp_id_date_idx on perf.transactions (customer_id, created_at);
drop index customer_id_idx;
-- running with composite index.

explain (analyze, buffers) 
select * from perf.transactions
where customer_id = 4242 
and created_at >= '2026-03-01' and created_at < '2026-04-01'
order by created_at desc;

--Execution Time: 0.168 ms
