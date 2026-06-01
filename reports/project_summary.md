# Project Summary

## Title

Analyzing Job Market Demand Using Web Scraping and Data Visualization Techniques

## Project Overview

This project analyzes general job market demand in Cambodia using a local Python data pipeline. The system collects public job posting data from multiple source websites, cleans and standardizes it, extracts common skills and requirements, loads normalized data into PostgreSQL when configured, and exports CSV files for Power BI dashboards.

## Data Sources

The scraper is configured for:

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

If a website blocks scraping or loads content dynamically, the project uses fallback sample records for that source so the local pipeline can still run.

## Problem Statement

Cambodian job seekers and students need evidence-based guidance about which job categories, locations, companies, salaries, and skills are most in demand. Job postings contain useful signals, but the data is scattered across many websites and is not immediately ready for visualization.

## Objectives

- Collect multi-source job posting data for Cambodia.
- Clean raw job data into a structured dataset.
- Categorize jobs into broad market categories.
- Extract common skills such as communication, English, Excel, customer service, sales, accounting, digital marketing, SQL, Python, Power BI, and project management.
- Store cleaned data in a relational database.
- Export Power BI-ready datasets for dashboard creation.
- Produce insights that support career and learning recommendations.

## Methodology

1. **Web Scraping**
   - The scraper requests public job pages with polite delays.
   - Multiple Cambodia job websites are configured, including LinkedIn.
   - Private or login-required pages are not scraped.
   - If live scraping fails, source-specific fallback data is generated.

2. **Data Cleaning**
   - Duplicate records are removed.
   - Job titles, company names, and locations are standardized.
   - Salaries are parsed and normalized to estimated monthly USD values when possible.
   - Jobs are categorized into broad market categories.
   - Missing values are handled with consistent defaults.

3. **Skill Extraction**
   - Job descriptions are scanned for common skills and requirements.
   - A many-to-many `job_skills` dataset is created for Power BI and PostgreSQL.

4. **Database Storage**
   - PostgreSQL tables are created for jobs, skills, and job-skill relationships.
   - Data is loaded with upsert logic to avoid duplicates.

5. **Power BI Export**
   - Cleaned and summarized CSV files are exported for dashboard creation.

## Expected Dashboard Pages

1. **Job Market Overview**
   - Total jobs, companies, locations, sources, average salary, jobs by category, jobs by location.

2. **Source and Category Analysis**
   - Jobs by website source, job categories by source, and category-location mix.

3. **Skill Demand Analysis**
   - Top demanded skills, skill frequency, skills by category, and skills by experience level.

4. **Salary Analysis**
   - Average salary by job title, category, location, and skill.

5. **Company and Location Analysis**
   - Top hiring companies, jobs by city or province, and map visualization.

6. **Recommendations**
   - Most valuable skills, best locations, strongest categories, and common entry-level requirements.

## Expected Insights

- Phnom Penh is likely to show the highest concentration of job postings.
- Sales, finance, administration, IT, customer service, and operations roles are expected to appear frequently.
- English, communication, Microsoft Office, Excel, customer service, and reporting are common cross-market requirements.
- IT and data-related roles are more likely to mention SQL, Python, dashboards, APIs, and Git.
- NGO/development roles often emphasize project coordination, reporting, monitoring, evaluation, and stakeholder communication.

## Limitations

- Live scraping can be affected by website structure changes and anti-bot protection.
- LinkedIn may provide limited public data without login.
- Salary data may be missing or inconsistent.
- Keyword-based skill extraction may miss context or alternative phrasing.
- Fallback records are useful for demonstration but are not a substitute for a full live scrape.

## Future Improvements

- Add Selenium or Playwright for dynamic pages.
- Add more Cambodia-specific job boards.
- Improve skill extraction with NLP.
- Track postings over time for trend analysis.
- Build a finished Power BI report template.
- Add geocoding for Cambodian provinces and districts.

## Conclusion

The project demonstrates a complete data visualization workflow: data collection, cleaning, categorization, relational modeling, summarization, and dashboard preparation. It is suitable for a university data visualization course and can be extended into a portfolio project with more live sources and historical analysis.
