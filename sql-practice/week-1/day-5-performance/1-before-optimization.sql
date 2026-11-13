explain (analyze, buffers) 
select * from perf.transactions
where customer_id = 4242 
and to_char(created_at::date, 'YYYY-MM') = '2026-03'
order by created_at desc;

--Execution Time: 94.513 ms