# Analyzing Job Market Demand Using Web Scraping and Data Visualization Techniques

This is a local-first Python data pipeline for analyzing **general job market demand in Cambodia**. It collects public job posting data from multiple source websites, cleans and enriches the data, stores it in PostgreSQL when configured, and exports CSV datasets that are ready for Power BI.

The project is designed for a university data visualization course: simple enough to run locally, but structured cleanly enough for a portfolio.

## Scope

Target market: Cambodia general job market

Configured sources:

- LinkedIn
- BongThom
- CamHR
- Khmer24
- Talent.com
- Pelprek
- HRINC Jobs
- SeekFitJob
- Khmer Online Jobs
- Expertini Cambodia
- CamUp Job
- S&V Cambodia Job
- CamMA HR

LinkedIn is included as a public search source only. The scraper does not log in, bypass access controls, or scrape private pages. If LinkedIn or another site blocks scraping, the project uses realistic fallback records so the local pipeline still works.

## Problem Statement

Students and job seekers in Cambodia need a clear view of which job categories, companies, locations, salaries, and skills are most demanded. Job postings contain these signals, but they are scattered across many websites and are not immediately ready for analysis.

## Objectives

- Scrape public job listings from multiple Cambodia job websites.
- Build a larger multi-source dataset for Cambodia.
- Clean inconsistent job titles, companies, locations, salaries, and dates.
- Categorize jobs into broad market categories such as IT, finance, sales, HR, logistics, education, hospitality, NGO/development, healthcare, and manufacturing.
- Extract common skills and requirements from job descriptions.
- Store normalized data in PostgreSQL.
- Export Power BI-ready fact, dimension, and summary CSV files.
- Provide dashboard guidance and a university submission summary.

## Tools Used

- Python
- uv
- requests
- BeautifulSoup
- pandas
- PostgreSQL
- SQLAlchemy
- psycopg2
- Power BI
- CSV files
- Jupyter Notebook

## Folder Structure

```text
job-market-analysis/
├── data/
│   ├── raw/
│   ├── cleaned/
│   └── powerbi/
├── database/
│   ├── schema.sql
│   ├── seed.sql
│   └── load_postgres.py
├── scraper/
│   └── scrape_jobs.py
├── processing/
│   ├── clean_jobs.py
│   └── extract_skills.py
├── exports/
│   └── export_powerbi.py
├── powerbi/
│   ├── dax_measures.md
│   ├── model_setup.md
│   └── power_query_queries.pq
├── notebooks/
│   └── exploratory_analysis.ipynb
├── reports/
│   └── project_summary.md
├── requirements.txt
├── pyproject.toml
├── .env.example
├── README.md
└── main.py
```

## Data Fields

The cleaned job dataset includes:

- `job_id`
- `source_name`
- `job_title`
- `job_category`
- `company_name`
- `location`
- `salary`
- `salary_min`
- `salary_max`
- `salary_avg`
- `salary_currency`
- `employment_type`
- `experience_level`
- `job_description`
- `skills`
- `date_posted`
- `source_url`
- `scraped_at`

The skill relationship dataset includes:

- `job_id`
- `skill`

## Installation With uv

Create the virtual environment and install dependencies:

```bash
uv sync
```

Run the full local pipeline:

```bash
uv run python main.py --skip-database
```

Run the notebook:

```bash
uv run jupyter notebook notebooks/exploratory_analysis.ipynb
```

## Installation With pip

```bash
python -m venv .venv
```

Windows PowerShell:

```powershell
.\.venv\Scripts\Activate.ps1
```

macOS or Linux:

```bash
source .venv/bin/activate
```

Install dependencies:

```bash
pip install -r requirements.txt
```

## How to Run Locally

From the project folder:

```bash
uv run python main.py
```

The pipeline runs:

1. Scrape jobs and save `data/raw/raw_jobs.csv`.
2. Clean data and save `data/cleaned/cleaned_jobs.csv`.
3. Extract skills and save `data/cleaned/job_skills.csv`.
4. Load data to PostgreSQL when `.env` is configured.
5. Export Power BI-ready files to `data/powerbi/`.

To skip PostgreSQL:

```bash
uv run python main.py --skip-database
```

To force sample data only:

```powershell
$env:SCRAPER_MODE="sample"
uv run python main.py --skip-database
```

By default, the local pipeline targets about `12,000` rows:

```text
SCRAPER_TARGET_TOTAL_RECORDS=12000
```

To generate a different dataset size, change the total target:

```powershell
$env:SCRAPER_TARGET_TOTAL_RECORDS="15000"
uv run python main.py --skip-database
```

The pipeline spreads that target across all configured sources and tops up with clean generated Cambodia records when live scraping is blocked.

To reuse an existing raw CSV:

```bash
uv run python main.py --skip-scrape --skip-database
```

## Web Scraping Notes

The scraper is configured for these public sources:

- `https://www.linkedin.com/jobs/jobs-in-cambodia`
- `https://www.bongthom.com/`
- `https://www.camhr.com/default.aspx`
- `https://www.khmer24.com/en/jobs.html`
- `https://www.talent.com/jobs?k=&l=Phnom+Penh%2C+Cambodia`
- `https://pelprek.com/`
- `https://www.hrincjobs.com/`
- `https://www.seekfitjob.com/`
- `https://www.khmeronlinejobs.com/`
- `https://kh.expertini.com/`
- `https://camupjob.com/`
- `https://camsvjob.com/`
- `https://cammahr.com/`

Polite scraping practices:

- Uses a browser-like user agent.
- Adds a delay between requests.
- Requests only public pages.
- Does not access private, login-required, or paid pages.
- Handles request and parsing errors.
- Uses fallback sample records when a source blocks requests or returns dynamic content.

## PostgreSQL Setup

Create a PostgreSQL database:

Option A: use the included Docker database:

```bash
docker compose up -d postgres
```

The Docker database runs on host port `5433` to avoid conflicting with a native PostgreSQL service.

Option B: use your native PostgreSQL:

```sql
CREATE DATABASE cambodia_job_market_analysis;
```

Copy the environment file:

```powershell
Copy-Item .env.example .env
```

Update `.env`:

```text
DB_HOST=localhost
DB_PORT=5433
DB_NAME=cambodia_job_market_analysis
DB_USER=postgres
DB_PASSWORD=postgres
```

The pipeline automatically runs:

- `database/schema.sql`
- `database/seed.sql`

Tables:

- `jobs`
- `skills`
- `job_skills`

Views for analysis:

- `location_summary`
- `source_summary`
- `category_summary`
- `skill_demand_summary`
- `company_hiring_summary`
- `salary_summary`

To load PostgreSQL, run the pipeline without `--skip-database`:

```bash
uv run python main.py
```

To load the latest CSVs into PostgreSQL without scraping again:

```bash
uv run python main.py --skip-scrape
```

More details are in `database/README.md`.

If `.env` is missing or incomplete, the PostgreSQL step is skipped and CSV exports are still created.

## Power BI CSV Exports

The following files are created in `data/powerbi/`:

- `jobs.csv`
- `skills.csv`
- `job_skills.csv`
- `location_summary.csv`
- `source_summary.csv`
- `category_summary.csv`
- `skill_demand_summary.csv`
- `company_hiring_summary.csv`
- `salary_summary.csv`

## Importing into Power BI

Option 1: CSV import

1. Open Power BI Desktop.
2. Select **Get Data**.
3. Choose **Text/CSV**.
4. Import all CSV files from `data/powerbi/`.
5. Use `powerbi/model_setup.md` to create relationships and set data types.

Option 2: Power Query setup

1. Open Power BI Desktop.
2. Select **Transform data**.
3. Create a blank query.
4. Use `powerbi/power_query_queries.pq` as the Power Query M reference.
5. Use `powerbi/dax_measures.md` for starter dashboard measures.

Option 3: PostgreSQL direct connection

1. Load PostgreSQL with `uv run python main.py` or `uv run python main.py --skip-scrape`.
2. Open Power BI Desktop.
3. Select **Get Data > PostgreSQL database**.
4. Server: `localhost:5433` for Docker, or `localhost:5432` for native PostgreSQL.
5. Database: `cambodia_job_market_analysis`.
6. Load base tables (`jobs`, `skills`, `job_skills`) or the summary views.
7. Use `powerbi/postgresql_power_query.pq` as a Power Query reference if you prefer M code.
8. If Power BI shows table names like `public jobs`, use DAX formulas from `powerbi/dax_measures_postgresql.md`.

Create relationships:

   - `jobs[job_id]` to `job_skills[job_id]`
   - `skills[skill_id]` to `job_skills[skill_id]`

Set salary fields as decimal numbers and `date_posted` as a date field.

## Suggested Dashboard Plan

### Page 1: Job Market Overview

Visuals:

- Total job postings
- Total companies
- Total locations
- Total sources
- Average salary in USD
- Jobs by category
- Jobs by location

### Page 2: Source and Category Analysis

Visuals:

- Jobs by website source
- Job categories by source
- Top categories in Cambodia
- Category and location matrix

Useful tables:

- `source_summary.csv`
- `category_summary.csv`
- `jobs.csv`

### Page 3: Skill Demand Analysis

Visuals:

- Top 10 most demanded skills
- Skill frequency bar chart
- Skills by job category
- Skills by experience level

Useful fields:

- `skills[skill_name]`
- `skill_demand_summary[job_count]`
- `job_skills[job_id]`
- `jobs[job_category]`

### Page 4: Salary Analysis

Visuals:

- Average salary by job title
- Average salary by job category
- Salary by location
- Salary by skill

Useful fields:

- `salary_summary[summary_type]`
- `salary_summary[category]`
- `salary_summary[salary_avg]`
- `jobs[salary_min]`
- `jobs[salary_max]`

### Page 5: Company and Location Analysis

Visuals:

- Top hiring companies
- Jobs by city or province
- Map visualization
- Company category mix

Useful fields:

- `company_hiring_summary[company_name]`
- `company_hiring_summary[job_count]`
- `location_summary[location]`
- `location_summary[job_count]`

### Page 6: Recommendations

Visuals and insights:

- Most valuable skills to learn
- Best job categories for entry-level applicants
- Best locations for job opportunities
- Websites with the most useful postings
- Common requirements across the Cambodia job market

## Expected Insights

Possible insights from the generated or scraped data:

- Phnom Penh is likely to dominate job postings because many companies are headquartered there.
- Sales, finance, administration, IT, customer service, and operations roles often appear across many sources.
- English, communication, Excel, customer service, sales, reporting, and Microsoft Office are common cross-market requirements.
- IT and data-related jobs tend to mention SQL, Python, dashboards, APIs, Git, or network support.
- NGO/development postings often emphasize project coordination, reporting, monitoring, evaluation, and stakeholder communication.

## Limitations

- Live scraping depends on public website availability and page structure.
- LinkedIn and some job sites may block automated requests or show limited public data.
- Some job boards use dynamic JavaScript content that requests and BeautifulSoup may not fully capture.
- Salary information is often missing or inconsistent.
- Skill extraction uses keyword matching, so it may miss synonyms or context.
- Sample fallback data is realistic for demonstration, but it is not a substitute for a full live market scrape.

## Future Improvements

- Add Selenium or Playwright for JavaScript-rendered job listings.
- Add more Cambodia-specific job sources.
- Store raw HTML snapshots for auditability.
- Improve skill extraction with NLP.
- Add historical scraping to analyze job market trends over time.
- Add a Power BI `.pbix` template.
- Add geocoding for more accurate map visuals.

## Ethical and Legal Notes

Only scrape public pages, keep request volume low, and respect each website's terms and robots guidance. Do not scrape private, login-required, or personal data pages.
