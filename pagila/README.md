# Pagila

[Pagila](https://github.com/devrimgunduz/pagila) is a sample PostgreSQL database for a DVD rental store (films, actors, customers, rentals, payments, stores). Most of the exercises in [sql-practice/](../sql-practice/) run against it.

## Loading it

With the database from the project root running:

```bash
git clone https://github.com/devrimgunduz/pagila.git
psql -h localhost -p 5433 -U <user> -d <db> -f pagila/pagila-schema.sql
psql -h localhost -p 5433 -U <user> -d <db> -f pagila/pagila-data.sql
```
