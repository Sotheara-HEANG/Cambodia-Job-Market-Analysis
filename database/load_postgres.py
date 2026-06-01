"""Load cleaned jobs and extracted skills into PostgreSQL."""

from __future__ import annotations

import os
from pathlib import Path
from urllib.parse import quote_plus

import pandas as pd
from dotenv import load_dotenv
from sqlalchemy import create_engine, text
from sqlalchemy.engine import Engine


PROJECT_ROOT = Path(__file__).resolve().parents[1]
SCHEMA_PATH = PROJECT_ROOT / "database" / "schema.sql"
SEED_PATH = PROJECT_ROOT / "database" / "seed.sql"
CLEANED_JOBS_PATH = PROJECT_ROOT / "data" / "cleaned" / "cleaned_jobs.csv"
JOB_SKILLS_PATH = PROJECT_ROOT / "data" / "cleaned" / "job_skills.csv"


def get_database_url() -> str | None:
    """Build a SQLAlchemy database URL from .env values."""

    load_dotenv(PROJECT_ROOT / ".env")
    required = ["DB_HOST", "DB_PORT", "DB_NAME", "DB_USER", "DB_PASSWORD"]
    values = {key: os.getenv(key) for key in required}

    missing = [key for key, value in values.items() if not value]
    if missing:
        print(f"PostgreSQL load skipped. Missing environment variables: {', '.join(missing)}")
        return None

    user = quote_plus(values["DB_USER"] or "")
    password = quote_plus(values["DB_PASSWORD"] or "")
    host = values["DB_HOST"]
    port = values["DB_PORT"]
    database = values["DB_NAME"]
    return f"postgresql+psycopg2://{user}:{password}@{host}:{port}/{database}"


def create_postgres_engine() -> Engine | None:
    """Create the database engine when environment variables are available."""

    database_url = get_database_url()
    if not database_url:
        return None
    return create_engine(database_url, pool_pre_ping=True)


def execute_sql_file(engine: Engine, path: Path) -> None:
    """Execute a SQL file using a raw DBAPI cursor for multi-statement SQL."""

    sql = path.read_text(encoding="utf-8")
    raw_connection = engine.raw_connection()
    try:
        cursor = raw_connection.cursor()
        cursor.execute(sql)
        raw_connection.commit()
    finally:
        raw_connection.close()


def dataframe_records(df: pd.DataFrame) -> list[dict]:
    """Convert NaN values to None before SQL insertion."""

    clean_df = df.astype(object).where(pd.notna(df), None)
    return clean_df.to_dict(orient="records")


def load_jobs(engine: Engine, jobs: pd.DataFrame) -> None:
    """Upsert job rows into PostgreSQL."""

    columns = [
        "job_id",
        "source_name",
        "job_title",
        "job_category",
        "company_name",
        "location",
        "salary",
        "salary_min",
        "salary_max",
        "salary_avg",
        "salary_currency",
        "employment_type",
        "experience_level",
        "job_description",
        "date_posted",
        "source_url",
        "scraped_at",
    ]
    records = dataframe_records(jobs[columns])
    if not records:
        return

    statement = text(
        """
        INSERT INTO jobs (
            job_id, source_name, job_title, job_category, company_name, location,
            salary, salary_min, salary_max, salary_avg, salary_currency, employment_type,
            experience_level, job_description, date_posted, source_url, scraped_at
        )
        VALUES (
            :job_id, :source_name, :job_title, :job_category, :company_name, :location,
            :salary, :salary_min, :salary_max, :salary_avg, :salary_currency, :employment_type,
            :experience_level, :job_description, :date_posted, :source_url, :scraped_at
        )
        ON CONFLICT (job_id) DO UPDATE SET
            source_name = EXCLUDED.source_name,
            job_title = EXCLUDED.job_title,
            job_category = EXCLUDED.job_category,
            company_name = EXCLUDED.company_name,
            location = EXCLUDED.location,
            salary = EXCLUDED.salary,
            salary_min = EXCLUDED.salary_min,
            salary_max = EXCLUDED.salary_max,
            salary_avg = EXCLUDED.salary_avg,
            salary_currency = EXCLUDED.salary_currency,
            employment_type = EXCLUDED.employment_type,
            experience_level = EXCLUDED.experience_level,
            job_description = EXCLUDED.job_description,
            date_posted = EXCLUDED.date_posted,
            source_url = EXCLUDED.source_url,
            scraped_at = EXCLUDED.scraped_at;
        """
    )
    with engine.begin() as connection:
        connection.execute(statement, records)


def clear_existing_job_data(engine: Engine) -> None:
    """Remove old fact rows so PostgreSQL mirrors the latest CSV outputs."""

    with engine.begin() as connection:
        connection.execute(text("DELETE FROM job_skills;"))
        connection.execute(text("DELETE FROM jobs;"))


def load_skills(engine: Engine, job_skills: pd.DataFrame) -> dict[str, int]:
    """Insert skills and return a skill-name to skill-id lookup."""

    unique_skills = sorted(job_skills["skill"].dropna().unique().tolist())
    if unique_skills:
        records = [{"skill_name": skill} for skill in unique_skills]
        with engine.begin() as connection:
            connection.execute(
                text(
                    """
                    INSERT INTO skills (skill_name)
                    VALUES (:skill_name)
                    ON CONFLICT (skill_name) DO NOTHING;
                    """
                ),
                records,
            )

    with engine.begin() as connection:
        rows = connection.execute(text("SELECT skill_id, skill_name FROM skills;")).fetchall()
    return {row.skill_name: row.skill_id for row in rows}


def load_job_skills(engine: Engine, job_skills: pd.DataFrame, skill_lookup: dict[str, int]) -> None:
    """Insert job-skill relationship rows."""

    records = []
    for _, row in job_skills.iterrows():
        skill_id = skill_lookup.get(row["skill"])
        if skill_id:
            records.append({"job_id": row["job_id"], "skill_id": skill_id})

    if not records:
        return

    with engine.begin() as connection:
        connection.execute(
            text(
                """
                INSERT INTO job_skills (job_id, skill_id)
                VALUES (:job_id, :skill_id)
                ON CONFLICT (job_id, skill_id) DO NOTHING;
                """
            ),
            records,
        )


def load_to_postgres(
    cleaned_jobs_path: Path = CLEANED_JOBS_PATH,
    job_skills_path: Path = JOB_SKILLS_PATH,
) -> bool:
    """Load cleaned CSV files into PostgreSQL.

    Returns True when a database load was attempted successfully and False when
    it was skipped because configuration or files were missing.
    """

    if not cleaned_jobs_path.exists() or not job_skills_path.exists():
        print("PostgreSQL load skipped. Cleaned CSV files are not available yet.")
        return False

    engine = create_postgres_engine()
    if engine is None:
        return False

    try:
        execute_sql_file(engine, SCHEMA_PATH)
        execute_sql_file(engine, SEED_PATH)
        jobs = pd.read_csv(cleaned_jobs_path)
        job_skills = pd.read_csv(job_skills_path)
        clear_existing_job_data(engine)
        load_jobs(engine, jobs)
        skill_lookup = load_skills(engine, job_skills)
        load_job_skills(engine, job_skills, skill_lookup)
        print(f"Loaded {len(jobs)} jobs and {len(job_skills)} job-skill links into PostgreSQL.")
        return True
    except Exception as exc:  # noqa: BLE001 - report and allow local CSV pipeline to continue.
        print(f"PostgreSQL load failed but the CSV pipeline will continue. Reason: {exc}")
        return False
    finally:
        engine.dispose()


if __name__ == "__main__":
    load_to_postgres()
