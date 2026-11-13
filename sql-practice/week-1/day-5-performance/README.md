# Week 1 · Day 5: Query Performance

Practice speeding up slow queries on the `perf.transactions` table. Each query was run with `EXPLAIN (ANALYZE, BUFFERS)` before and after a change, and the execution time is written under each query in the files.

## Results

| Query | Before | After | What I changed | Why it worked |
| --- | --- | --- | --- | --- |
| **1.** One customer's transactions for March 2026, newest first ([before](1-before-optimization.sql) / [after](1-after-optimization.sql)) | 94.513 ms | 0.731 ms | Added an index on `customer_id`. | Without an index, Postgres reads every row in the table (a sequential scan) to find customer 4242. With the index it jumps straight to that customer's few rows, then runs the `to_char(...)` month check only on those rows. |
| **1b.** Same query, month filter rewritten | 0.731 ms | 0.309 ms | Replaced `to_char(created_at::date, 'YYYY-MM') = '2026-03'` with the range `created_at >= '2026-03-01' and created_at < '2026-04-01'`. | `to_char` and the `::date` cast had to be computed for every matching row before the comparison. A plain range compares the raw `created_at` value directly, which is cheaper and can also use an index on `created_at`. |
| **1c.** Same query, composite index | 0.309 ms | 0.168 ms | Replaced the `customer_id` index with a composite index on `(customer_id, created_at)`. | The index stores rows sorted by customer, then by date. Postgres finds customer 4242, reads only the March part of that customer's entries, and reads them backwards to get `order by created_at desc`, so no separate sort is needed. |
| **2.** Count and total amount for 15 March 2026 ([before](2-before-optimization.sql) / [after](2-after-optimization.sql)) | 111.838 ms | 113.373 ms | Added an index on `created_at`, but kept `where created_at::date = '2026-03-15'`. | It didn't work. The index stores `created_at` values, not `created_at::date` values. Because the filter wraps the column in a cast, Postgres can't use the index and still scans the whole table. |
| **2b.** Same query, filter rewritten | 113.373 ms | 3.494 ms | Changed the filter to the range `created_at >= '2026-03-15' and created_at < '2026-03-16'`. | The column is no longer wrapped in a function, so the `created_at` index can be used. Postgres reads only the one day's rows from the index instead of the whole table. |
| **3.** Latest 20 failed transactions ([before](3-before-optimization.sql) / [after](3-after-optimization.sql)) | 94.010 ms | 2.736 ms | Kept the query text the same and ran it with the `created_at` index from query 2 in place. | Before, Postgres had to scan every row, keep the failed ones, and sort them by date. With the `created_at` index, it walks the index from the newest row backwards, checks `status = 'failed'` on each, and stops as soon as it has 20 rows. |

## Takeaways

- **Index the columns you filter on.** Query 1 went from about 94 ms to under 1 ms just by indexing `customer_id`.
- **Don't wrap an indexed column in a function or cast** in the `WHERE` clause (`::date`, `to_char`, etc.). Query 2 shows an index does nothing if the filter is `created_at::date = ...`. Use a range on the raw column instead: `>= start and < next_start`.
- **Composite indexes can cover both the filter and the sort.** Putting the equality column first (`customer_id`) and the range/sort column second (`created_at`) lets Postgres skip the sort step.
- **`ORDER BY ... LIMIT` benefits from an index on the sort column.** Postgres can read rows already in order and stop early instead of sorting the whole table (query 3).
- **Always measure.** Compare `EXPLAIN (ANALYZE, BUFFERS)` output before and after. Adding an index is not guaranteed to help, as query 2 shows.
