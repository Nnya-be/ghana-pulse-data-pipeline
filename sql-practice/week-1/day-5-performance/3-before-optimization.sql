-- without the date index as before.
explain (analyze, buffers)
select * from perf.transactions
where status = 'failed'
order by created_at desc
limit 20;

--Execution Time: 94.010 ms