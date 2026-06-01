"""Run the complete local job market analysis pipeline."""

from __future__ import annotations

import argparse
from pathlib import Path

from database.load_postgres import load_to_postgres
from exports.export_powerbi import export_powerbi_datasets
from processing.clean_jobs import clean_jobs
from processing.extract_skills import extract_job_skills
from scraper.scrape_jobs import scrape_jobs


PROJECT_ROOT = Path(__file__).resolve().parent


def ensure_project_directories() -> None:
    """Ensure all pipeline output folders exist."""

    for path in [
        PROJECT_ROOT / "data" / "raw",
        PROJECT_ROOT / "data" / "cleaned",
        PROJECT_ROOT / "data" / "powerbi",
    ]:
        path.mkdir(parents=True, exist_ok=True)


def run_pipeline(skip_scrape: bool = False, skip_database: bool = False) -> None:
    """Run all project steps in order."""

    ensure_project_directories()

    print("Step 1: Scrape jobs")
    if skip_scrape:
        print("Scraping skipped by user option.")
    else:
        scrape_jobs()

    print("Step 2: Clean data")
    clean_jobs()

    print("Step 3: Extract skills")
    extract_job_skills()

    print("Step 4: Load to PostgreSQL")
    if skip_database:
        print("PostgreSQL load skipped by user option.")
    else:
        load_to_postgres()

    print("Step 5: Export Power BI datasets")
    export_powerbi_datasets()

    print("Pipeline finished.")


def parse_args() -> argparse.Namespace:
    """Read simple command-line switches."""

    parser = argparse.ArgumentParser(description="Run the job market analysis data pipeline.")
    parser.add_argument(
        "--skip-scrape",
        action="store_true",
        help="Use an existing data/raw/raw_jobs.csv file instead of scraping.",
    )
    parser.add_argument(
        "--skip-database",
        action="store_true",
        help="Skip PostgreSQL loading and only produce CSV outputs.",
    )
    return parser.parse_args()


if __name__ == "__main__":
    args = parse_args()
    run_pipeline(skip_scrape=args.skip_scrape, skip_database=args.skip_database)
