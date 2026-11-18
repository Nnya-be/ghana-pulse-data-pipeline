# Week 1 · Day 3: Window Functions

Window functions calculate a value across a set of related rows (a "window") without collapsing them like `GROUP BY` does. These exercises run against the Pagila database.

| File | What it does |
| --- | --- |
| [raking-film-by-length.sql](raking-film-by-length.sql) | Ranks films by length within each rating using `RANK` |
| [actor-longest-film.sql](actor-longest-film.sql) | Finds each actor's longest film |
| [customers-first-rental.sql](customers-first-rental.sql) | Finds each customer's first rental with `ROW_NUMBER` |
| [find-top-3-customers-payment.sql](find-top-3-customers-payment.sql) | Top 3 paying customers per store |
| [running-total-customer.sql](running-total-customer.sql) | Running total of each customer's payments |
| [daily-revenue-average.sql](daily-revenue-average.sql) | Daily revenue with a 7-day moving average |
| [total-montly-revenue.sql](total-montly-revenue.sql) | Monthly revenue and % change from the previous month using `LAG` |
| [diff-average-rating.sql](diff-average-rating.sql) | Compares each film's rental rate with its category average |
| [most-rented-categories.sql](most-rented-categories.sql) | Top 3 most-rented films in each category using `DENSE_RANK` |
| [customers-rentals-between-days.sql](customers-rentals-between-days.sql) | Days between each customer's rentals using `LAG` |
| [maximum-rental-interval.sql](maximum-rental-interval.sql) | Each customer's longest gap between rentals |
