create schema if not exists perf;

create table if not exists perf.transactions(
	id integer primary key ,
	customer_id integer,
	amount numeric(10,2),
	status varchar,
	created_at timestamptz	
);

insert into perf.transactions (id, customer_id, amount, status, created_at)
select
    s.g,
    (floor(random() * 10000) + 1)::int,
    round((1 + random() * 499)::numeric, 2),
    case
        when s.r < 0.90 then 'completed'
        when s.r < 0.98 then 'failed'
        else 'refunded'
    end,
    now() - random() * interval '730 days'
from (
    select g, random() as r
    from generate_series(1, 1000000) as g
) as s;

select count(*) from perf.transactions;

analyze perf.transactions;
