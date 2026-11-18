# Week 1 · Day 4: CTEs and Dates

Practice with common table expressions (`WITH`), recursive CTEs and date functions on the Pagila database.

| File | What it does |
| --- | --- |
| [all-non-rental-dates.sql](all-non-rental-dates.sql) | Builds a calendar with a recursive CTE and lists dates with no rentals |
| [film-category-with-month-rental.sql](film-category-with-month-rental.sql) | One row per category with rentals for May–August 2022 as columns |
| [film-with-month-rental-filter-version.sql](film-with-month-rental-filter-version.sql) | Same pivot, written with `FILTER` |
| [find-longest-streaks.sql](find-longest-streaks.sql) | Each customer's longest streak of consecutive rental days (gaps and islands) |
| [percentage-rental-per-day.sql](percentage-rental-per-day.sql) | Rentals per day of the week and each day's share as a percentage |
| [rental-session.sql](rental-session.sql) | Groups rentals into sessions split by gaps of more than 7 days |
| [returned-rentals-avg.sql](returned-rentals-avg.sql) | Average days kept and late returns per film category |
| [stores-month-highest-revenue.sql](stores-month-highest-revenue.sql) | Each store's best month and how far it was above its average |
