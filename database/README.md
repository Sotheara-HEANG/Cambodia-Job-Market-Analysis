# PostgreSQL Setup

This project can run with CSV exports only, but PostgreSQL is supported for a proper relational database workflow.

## 1. Create Database

### Option A: Docker PostgreSQL

Start the included local PostgreSQL container:

```bash
docker compose up -d postgres
```

The Docker database uses:

```text
DB_HOST=localhost
DB_PORT=5433
DB_NAME=cambodia_job_market_analysis
DB_USER=postgres
DB_PASSWORD=postgres
```

This uses host port `5433` so it does not conflict with a native PostgreSQL service on `5432`.

### Option B: Native PostgreSQL

```sql
CREATE DATABASE cambodia_job_market_analysis;
```

## 2. Configure `.env`

Copy `.env.example` to `.env`:

```powershell
Copy-Item .env.example .env
```

Update these values:

```text
DB_HOST=localhost
DB_PORT=5433
DB_NAME=cambodia_job_market_analysis
DB_USER=postgres
DB_PASSWORD=postgres
```

## 3. Load Data

Run the full pipeline and load PostgreSQL:

```bash
uv run python main.py
```

Or load the latest cleaned CSVs without scraping again:

```bash
uv run python main.py --skip-scrape
```

The loader:

- Runs `schema.sql`
- Runs `seed.sql`
- Clears old `jobs` and `job_skills` rows
- Loads the latest `cleaned_jobs.csv`
- Loads the latest `job_skills.csv`
- Keeps the `skills` dimension up to date

## 4. Tables

- `jobs`
- `skills`
- `job_skills`

## 5. Power BI Views

`schema.sql` also creates these views:

- `location_summary`
- `source_summary`
- `category_summary`
- `skill_demand_summary`
- `company_hiring_summary`
- `salary_summary`

Power BI can connect directly to PostgreSQL and load either the base tables or these views.

## 6. Validate Row Counts

Run:

```bash
psql -d cambodia_job_market_analysis -f database/check_counts.sql
```
