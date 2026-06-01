# Power BI Model Setup

Use **Get Data > Text/CSV** and import every file from `data/powerbi/`, or use `power_query_queries.pq` as a Power Query reference.

For a database workflow, load PostgreSQL first and use **Get Data > PostgreSQL database**. The PostgreSQL setup is documented in `database/README.md`, and `postgresql_power_query.pq` provides Power Query M references.

If Power BI imports PostgreSQL objects with names like `public jobs`, use `dax_measures_postgresql.md`. DAX requires single quotes around table names that contain spaces:

```DAX
Total Jobs = DISTINCTCOUNT('public jobs'[job_id])
```

## Tables

- `jobs`
- `skills`
- `job_skills`
- `location_summary`
- `source_summary`
- `category_summary`
- `skill_demand_summary`
- `company_hiring_summary`
- `salary_summary`

## Relationships

Create these relationships:

- `jobs[job_id]` one-to-many `job_skills[job_id]`
- `skills[skill_id]` one-to-many `job_skills[skill_id]`

Recommended filter direction:

- Single direction from `jobs` to `job_skills`
- Single direction from `skills` to `job_skills`

The summary tables can stay disconnected and be used directly for simple dashboard visuals.

If you connect to PostgreSQL, the same summary datasets are available as views:

- `location_summary`
- `source_summary`
- `category_summary`
- `skill_demand_summary`
- `company_hiring_summary`
- `salary_summary`

## Data Types

- `jobs[date_posted]`: Date
- `jobs[scraped_at]`: Date/Time
- `jobs[salary_min]`: Decimal number
- `jobs[salary_max]`: Decimal number
- `jobs[salary_avg]`: Decimal number
- Count fields: Whole number

## Refresh

After rerunning the Python pipeline:

```bash
uv run python main.py --skip-database
```

Open Power BI Desktop and select **Refresh**. The CSV paths stay the same.
