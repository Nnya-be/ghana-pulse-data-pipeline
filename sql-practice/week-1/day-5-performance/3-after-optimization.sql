-- with the date index as after.
explain (analyze, buffers)
select * from perf.transactions
where status = 'failed'
order by created_at desc
limit 20;
--Execution Time: 2.736 ms