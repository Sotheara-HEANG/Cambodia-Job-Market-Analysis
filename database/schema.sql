CREATE TABLE IF NOT EXISTS jobs (
    job_id TEXT PRIMARY KEY,
    source_name TEXT,
    job_title TEXT NOT NULL,
    job_category TEXT,
    company_name TEXT,
    location TEXT,
    salary TEXT,
    salary_min NUMERIC(12, 2),
    salary_max NUMERIC(12, 2),
    salary_avg NUMERIC(12, 2),
    salary_currency TEXT,
    employment_type TEXT,
    experience_level TEXT,
    job_description TEXT,
    date_posted DATE,
    source_url TEXT,
    scraped_at TIMESTAMPTZ
);

ALTER TABLE jobs ADD COLUMN IF NOT EXISTS source_name TEXT;
ALTER TABLE jobs ADD COLUMN IF NOT EXISTS job_category TEXT;
ALTER TABLE jobs ADD COLUMN IF NOT EXISTS salary TEXT;
ALTER TABLE jobs ADD COLUMN IF NOT EXISTS salary_avg NUMERIC(12, 2);
ALTER TABLE jobs ADD COLUMN IF NOT EXISTS salary_currency TEXT;

CREATE TABLE IF NOT EXISTS skills (
    skill_id SERIAL PRIMARY KEY,
    skill_name TEXT NOT NULL UNIQUE
);

CREATE TABLE IF NOT EXISTS job_skills (
    job_id TEXT NOT NULL REFERENCES jobs(job_id) ON DELETE CASCADE,
    skill_id INTEGER NOT NULL REFERENCES skills(skill_id) ON DELETE CASCADE,
    PRIMARY KEY (job_id, skill_id)
);

CREATE INDEX IF NOT EXISTS idx_jobs_location ON jobs(location);
CREATE INDEX IF NOT EXISTS idx_jobs_company ON jobs(company_name);
CREATE INDEX IF NOT EXISTS idx_jobs_source_name ON jobs(source_name);
CREATE INDEX IF NOT EXISTS idx_jobs_category ON jobs(job_category);
CREATE INDEX IF NOT EXISTS idx_jobs_date_posted ON jobs(date_posted);
CREATE INDEX IF NOT EXISTS idx_job_skills_job_id ON job_skills(job_id);
CREATE INDEX IF NOT EXISTS idx_job_skills_skill_id ON job_skills(skill_id);

CREATE OR REPLACE VIEW location_summary AS
SELECT
    location,
    COUNT(*) AS job_count,
    COUNT(DISTINCT company_name) AS company_count,
    AVG(salary_avg) AS average_salary_usd
FROM jobs
GROUP BY location;

CREATE OR REPLACE VIEW source_summary AS
SELECT
    source_name,
    COUNT(*) AS job_count,
    COUNT(DISTINCT company_name) AS company_count,
    COUNT(DISTINCT job_category) AS category_count,
    AVG(salary_avg) AS average_salary_usd
FROM jobs
GROUP BY source_name;

CREATE OR REPLACE VIEW category_summary AS
SELECT
    job_category,
    COUNT(*) AS job_count,
    COUNT(DISTINCT company_name) AS company_count,
    COUNT(DISTINCT location) AS location_count,
    AVG(salary_avg) AS average_salary_usd
FROM jobs
GROUP BY job_category;

CREATE OR REPLACE VIEW skill_demand_summary AS
SELECT
    s.skill_id,
    s.skill_name,
    COUNT(DISTINCT js.job_id) AS job_count
FROM skills s
JOIN job_skills js ON js.skill_id = s.skill_id
GROUP BY s.skill_id, s.skill_name;

CREATE OR REPLACE VIEW company_hiring_summary AS
SELECT
    company_name,
    COUNT(*) AS job_count,
    COUNT(DISTINCT location) AS unique_locations,
    COUNT(DISTINCT job_category) AS unique_categories,
    AVG(salary_avg) AS average_salary_usd
FROM jobs
GROUP BY company_name;

CREATE OR REPLACE VIEW salary_summary AS
SELECT
    'job_title' AS summary_type,
    job_title AS category,
    COUNT(*) AS job_count,
    AVG(salary_min) AS salary_min_avg,
    AVG(salary_max) AS salary_max_avg,
    AVG(salary_avg) AS salary_avg
FROM jobs
GROUP BY job_title
UNION ALL
SELECT
    'job_category' AS summary_type,
    job_category AS category,
    COUNT(*) AS job_count,
    AVG(salary_min) AS salary_min_avg,
    AVG(salary_max) AS salary_max_avg,
    AVG(salary_avg) AS salary_avg
FROM jobs
GROUP BY job_category
UNION ALL
SELECT
    'location' AS summary_type,
    location AS category,
    COUNT(*) AS job_count,
    AVG(salary_min) AS salary_min_avg,
    AVG(salary_max) AS salary_max_avg,
    AVG(salary_avg) AS salary_avg
FROM jobs
GROUP BY location
UNION ALL
SELECT
    'skill' AS summary_type,
    s.skill_name AS category,
    COUNT(DISTINCT j.job_id) AS job_count,
    AVG(j.salary_min) AS salary_min_avg,
    AVG(j.salary_max) AS salary_max_avg,
    AVG(j.salary_avg) AS salary_avg
FROM jobs j
JOIN job_skills js ON js.job_id = j.job_id
JOIN skills s ON s.skill_id = js.skill_id
GROUP BY s.skill_name;

CREATE OR REPLACE VIEW powerbi_jobs AS
SELECT
    job_id,
    source_name,
    job_title,
    job_category,
    company_name,
    location,
    salary,
    salary_min,
    salary_max,
    salary_avg,
    salary_currency,
    employment_type,
    experience_level,
    job_description,
    date_posted,
    source_url,
    scraped_at
FROM jobs;

CREATE OR REPLACE VIEW powerbi_skills AS
SELECT
    skill_id,
    skill_name
FROM skills;

CREATE OR REPLACE VIEW powerbi_job_skills AS
SELECT
    js.job_id,
    js.skill_id,
    s.skill_name AS skill
FROM job_skills js
JOIN skills s ON s.skill_id = js.skill_id;
