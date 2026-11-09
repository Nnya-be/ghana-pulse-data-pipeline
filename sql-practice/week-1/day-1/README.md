# Week 1 · Day 1: SQL Joins

Practice queries against the [Pagila](https://github.com/devrimgunduz/pagila) sample database (a DVD rental store).

A **join** combines rows from two tables by matching a column they share, usually a foreign key in one table pointing to a primary key in the other (for example `film.language_id` → `language.language_id`). The **type** of join decides what happens to rows that have no match.

## Types of joins covered

| Join | Keeps | Use it when |
|---|---|---|
| `INNER JOIN` (or just `JOIN`) | Only rows with a match in **both** tables | You only care about rows that are connected |
| `LEFT JOIN` | **Every** row from the left table; right-side columns are `NULL` when there's no match | You must not lose rows from the main table |
| Self-join | A table joined to **itself** under two aliases | Comparing rows within the same table |
| Anti-join | Rows from the left table that have **no** match on the right | Finding what's missing |

---

### 1. INNER JOIN

Returns only the rows where the join condition matches in both tables. Rows without a partner are dropped.

You can chain several joins to walk across tables. Each `ON` links the new table to one already in the query.

**File:** [finding-customers-and-manager.sql](finding-customers-and-manager.sql). For each store: its city, its number of customers, and its manager's name.

```sql
select
    s.store_id, ci.city,
    count(c.store_id) as customers,
    concat(m.first_name, ' ', m.last_name) as manager_full_name
from store as s
join address  as a  on s.address_id = a.address_id
join city     as ci on ci.city_id = a.city_id
join staff    as m  on m.staff_id = s.manager_staff_id
join customer as c  on s.store_id = c.store_id
group by s.store_id, ci.city, m.first_name, m.last_name;
```

Path: `store → address → city`, `store → staff` (manager), `store → customer`.

**Takeaways**
- When you join to a "many" table (`customer`), you get one row **per customer**. `GROUP BY` collapses them back to one row per store, and `COUNT` counts them.
- Every non-aggregated column in the `SELECT` must be in the `GROUP BY`.
- A table can be joined in a *role*: `staff` is aliased `m` because here it plays the part of the store's **manager** (`store.manager_staff_id`).
- ⚠️ An inner join drops stores with **zero** customers. To keep them with a count of 0, use `LEFT JOIN customer` instead.
- A quick sanity check: `SELECT store_id, COUNT(*) FROM customer GROUP BY store_id;` should give the same counts.

---

### 2. LEFT JOIN (LEFT OUTER JOIN)

Keeps **every** row from the left (first) table. If the right table has no matching row, its columns come back as `NULL`.

**File:** [list-title-and-language.sql](list-title-and-language.sql). Every film title with the name of its language.

```sql
select f.title, l.name
from film as f
left join language as l
    on f.language_id = l.language_id;
```

**Takeaways**
- "Left" means the table written **before** `LEFT JOIN` (`film`). All films are guaranteed to appear.
- In Pagila, `film.language_id` is `NOT NULL`, so every film has a language and an `INNER JOIN` would return the same rows. The `LEFT JOIN` is the safer habit when you need *all* rows from the main table no matter what.

---

### 3. Self-join

Join a table to **itself** by giving it two different aliases. The aliases act like two separate copies of the table.

**File:** [find-stars-without-penelope.sql](find-stars-without-penelope.sql). Actors who appeared in a film with PENELOPE GUINESS, and how many films they shared, excluding Penelope herself.

```sql
select a.actor_id, a.first_name, a.last_name,
       count(fa1.film_id) as film_together
from film_actor as fa1                       -- Penelope's film appearances
join film_actor as fa2 on fa1.film_id = fa2.film_id   -- everyone in those same films
join actor as a on fa2.actor_id = a.actor_id          -- the co-star's name
join actor as p on p.actor_id = fa1.actor_id          -- Penelope
where p.first_name = 'PENELOPE'
  and p.last_name  = 'GUINESS'
  and fa2.actor_id != p.actor_id             -- exclude Penelope herself
group by a.actor_id
order by 4 desc;
```

**Takeaways**
- `fa1` and `fa2` are both `film_actor`. Joining on `film_id` pairs every actor in a film with every *other* actor in the same film.
- Without `fa2.actor_id != p.actor_id`, Penelope would be paired with herself and appear in her own results.
- `actor` is also joined twice, with two roles: `p` (Penelope) and `a` (the co-star).
- `group by a.actor_id` alone is allowed because `actor_id` is the primary key, so Postgres knows the name columns are fixed for each id.
- `order by 4` sorts by the 4th column in the `SELECT` (`film_together`). It's quick to write, but `order by film_together desc` is clearer.

---

### 4. Anti-join: finding rows with no match

An anti-join returns rows from one table that have **no** related row in another. There are two common ways to write it.

**File:** [left-join-in-2-ways.sql](left-join-in-2-ways.sql). Films that have no copies in the inventory.

**Way 1: `LEFT JOIN` + `IS NULL`**

```sql
select f.film_id, f.title
from film as f
left join inventory as i
    on f.film_id = i.film_id
where i.film_id is null;
```

The `LEFT JOIN` keeps every film. Films with no inventory get `NULL` on the inventory side, and the `WHERE` keeps only those.

**Way 2: `NOT EXISTS`**

```sql
select f.film_id, f.title
from film as f
where not exists (
    select 1
    from inventory as i
    where i.film_id = f.film_id
);
```

For each film, the subquery checks whether any inventory row points to it. `select 1` is a convention, because `EXISTS` only cares whether a row exists, not what it contains.

**Takeaways**
- Both give the same result. `NOT EXISTS` states the intent ("films where no inventory exists") more directly and never creates duplicate rows.
- In the `IS NULL` version, test a column that can't normally be `NULL`, such as the join key or primary key of the right table.
- ⚠️ Avoid `NOT IN (select film_id from inventory)` for this. If the subquery ever returns a `NULL`, `NOT IN` returns no rows at all.
