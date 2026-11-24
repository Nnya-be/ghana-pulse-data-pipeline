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

## Running dbt

The dbt project lives in [dbt/ghana_pulse/](dbt/ghana_pulse/).

1. Install dbt (pinned in `requirements-dev.txt`: `dbt-core==1.12.7`, `dbt-postgres==1.11.0`):

   ```bash
   pip install -r requirements-dev.txt
   ```

2. Add a `ghana_pulse` profile to `~/.dbt/profiles.yml`. It lives outside the repo, so it is never committed:

   ```yaml
   ghana_pulse:
     target: dev
     outputs:
       dev:
         type: postgres
         host: localhost
         port: 5433
         dbname: ghana_pulse
         user: your_user
         pass: your_password
         schema: dbt_dev
         threads: 4
   ```

3. Run every dbt command from `dbt/ghana_pulse/`, not from the repo root or `dbt/`. Running from the wrong folder fails to find `dbt_project.yml` and leaves a stray `logs/` folder behind.

   ```bash
   cd dbt/ghana_pulse
   dbt debug   # checks the profile and the database connection
   dbt run     # builds the staging views in the dbt_dev schema
   dbt test
   ```

Notes:

- The sources are the `raw.weather_daily` and `raw.fx_rates` tables. They hold the CSVs that `ingest/flatten.py` writes to `data/flat/`, so load those first or `dbt run` fails on missing relations.
- `flatten.py` keeps the source column names on purpose. The renaming happens in the staging models (`stg_weather`, `stg_fx`), so that is where to look for column mappings.
- Staging models are built as views (set in `dbt_project.yml`).
- `target/`, `logs/` and `dbt_packages/` are generated and gitignored. `dbt clean` removes `target/` and `dbt_packages/`.
- TODO dbt-state: <!-- add the dbt-state note here -->
