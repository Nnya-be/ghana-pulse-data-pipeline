# Ghana Pulse Data Pipeline

A data engineering learning project: SQL practice, data modelling, and (in progress) a full pipeline with ingestion, Spark, dbt and Airflow.

## Project layout

| Folder | What's in it |
| --- | --- |
| [sql-practice/](sql-practice/) | Weekly SQL exercises and solutions (joins, aggregations, window functions, CTEs, performance, modelling) |
| [pagila/](pagila/) | The Pagila sample database used by the SQL exercises |
| [ingest/](ingest/) | Scripts that pull raw data into the database |
| [spark/](spark/) | Spark jobs for larger transformations |
| [dbt/](dbt/) | dbt models that build the warehouse tables |
| [dags/](dags/) | Airflow DAGs that schedule the pipeline |
| [infra/](infra/) | Infrastructure and environment setup |

## Getting started

The database runs in Docker (Postgres 18 with pgvector).

1. Create a `.env` file in the project root:

   ```env
   POSTGRES_USER=your_user
   POSTGRES_PASSWORD=your_password
   POSTGRES_DB=your_db
   ```

2. Start the database:

   ```bash
   docker compose -f docker-compose-data.yml up -d
   ```

3. Connect on `localhost:5433` with the credentials from `.env`.

`.env` is in `.gitignore`, so your credentials are never committed.
