"""Create Power BI-ready CSV files from cleaned pipeline outputs."""

from __future__ import annotations

from pathlib import Path

import pandas as pd


PROJECT_ROOT = Path(__file__).resolve().parents[1]
CLEANED_JOBS_PATH = PROJECT_ROOT / "data" / "cleaned" / "cleaned_jobs.csv"
JOB_SKILLS_PATH = PROJECT_ROOT / "data" / "cleaned" / "job_skills.csv"
POWERBI_OUTPUT_DIR = PROJECT_ROOT / "data" / "powerbi"


def build_skills_dimension(job_skills: pd.DataFrame) -> pd.DataFrame:
    """Create a small skills dimension table."""

    skills = sorted(job_skills["skill"].dropna().unique().tolist())
    return pd.DataFrame(
        [{"skill_id": index, "skill_name": skill} for index, skill in enumerate(skills, start=1)]
    )


def export_powerbi_datasets(
    cleaned_jobs_path: Path = CLEANED_JOBS_PATH,
    job_skills_path: Path = JOB_SKILLS_PATH,
    output_dir: Path = POWERBI_OUTPUT_DIR,
) -> dict[str, Path]:
    """Export fact, dimension, and summary CSV files for Power BI."""

    if not cleaned_jobs_path.exists() or not job_skills_path.exists():
        raise FileNotFoundError("Run cleaning and skill extraction before exporting Power BI files.")

    output_dir.mkdir(parents=True, exist_ok=True)
    jobs = pd.read_csv(cleaned_jobs_path)
    job_skills = pd.read_csv(job_skills_path)
    skills = build_skills_dimension(job_skills)
    skill_lookup = dict(zip(skills["skill_name"], skills["skill_id"]))

    jobs_export_columns = [
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
        "skills",
        "date_posted",
        "source_url",
        "scraped_at",
    ]
    jobs_export = jobs[jobs_export_columns].copy()

    job_skills_export = job_skills.copy()
    job_skills_export["skill_id"] = job_skills_export["skill"].map(skill_lookup)
    job_skills_export = job_skills_export[["job_id", "skill_id", "skill"]].sort_values(
        ["skill", "job_id"]
    )

    location_summary = (
        jobs.groupby("location", dropna=False)
        .agg(
            job_count=("job_id", "count"),
            company_count=("company_name", "nunique"),
            average_salary_usd=("salary_avg", "mean"),
        )
        .reset_index()
        .sort_values("job_count", ascending=False)
    )

    source_summary = (
        jobs.groupby("source_name", dropna=False)
        .agg(
            job_count=("job_id", "count"),
            company_count=("company_name", "nunique"),
            category_count=("job_category", "nunique"),
            average_salary_usd=("salary_avg", "mean"),
        )
        .reset_index()
        .sort_values("job_count", ascending=False)
    )

    category_summary = (
        jobs.groupby("job_category", dropna=False)
        .agg(
            job_count=("job_id", "count"),
            company_count=("company_name", "nunique"),
            location_count=("location", "nunique"),
            average_salary_usd=("salary_avg", "mean"),
        )
        .reset_index()
        .sort_values("job_count", ascending=False)
    )

    skill_demand_summary = (
        job_skills_export.groupby(["skill_id", "skill"], dropna=False)
        .agg(job_count=("job_id", "nunique"))
        .reset_index()
        .sort_values("job_count", ascending=False)
    )

    company_hiring_summary = (
        jobs.groupby("company_name", dropna=False)
        .agg(
            job_count=("job_id", "count"),
            unique_locations=("location", "nunique"),
            unique_categories=("job_category", "nunique"),
            average_salary_usd=("salary_avg", "mean"),
        )
        .reset_index()
        .sort_values("job_count", ascending=False)
    )

    salary_by_title = (
        jobs.groupby("job_title", dropna=False)
        .agg(
            job_count=("job_id", "count"),
            salary_min_avg=("salary_min", "mean"),
            salary_max_avg=("salary_max", "mean"),
            salary_avg=("salary_avg", "mean"),
        )
        .reset_index()
        .rename(columns={"job_title": "category"})
    )
    salary_by_title["summary_type"] = "job_title"

    salary_by_job_category = (
        jobs.groupby("job_category", dropna=False)
        .agg(
            job_count=("job_id", "count"),
            salary_min_avg=("salary_min", "mean"),
            salary_max_avg=("salary_max", "mean"),
            salary_avg=("salary_avg", "mean"),
        )
        .reset_index()
        .rename(columns={"job_category": "category"})
    )
    salary_by_job_category["summary_type"] = "job_category"

    salary_by_location = (
        jobs.groupby("location", dropna=False)
        .agg(
            job_count=("job_id", "count"),
            salary_min_avg=("salary_min", "mean"),
            salary_max_avg=("salary_max", "mean"),
            salary_avg=("salary_avg", "mean"),
        )
        .reset_index()
        .rename(columns={"location": "category"})
    )
    salary_by_location["summary_type"] = "location"

    salary_by_skill = (
        jobs[["job_id", "salary_min", "salary_max", "salary_avg"]]
        .merge(job_skills_export, on="job_id", how="inner")
        .groupby("skill", dropna=False)
        .agg(
            job_count=("job_id", "nunique"),
            salary_min_avg=("salary_min", "mean"),
            salary_max_avg=("salary_max", "mean"),
            salary_avg=("salary_avg", "mean"),
        )
        .reset_index()
        .rename(columns={"skill": "category"})
    )
    salary_by_skill["summary_type"] = "skill"

    salary_summary = pd.concat(
        [salary_by_title, salary_by_job_category, salary_by_location, salary_by_skill],
        ignore_index=True,
    )[
        [
            "summary_type",
            "category",
            "job_count",
            "salary_min_avg",
            "salary_max_avg",
            "salary_avg",
        ]
    ].sort_values(["summary_type", "salary_avg"], ascending=[True, False])

    outputs = {
        "jobs": output_dir / "jobs.csv",
        "skills": output_dir / "skills.csv",
        "job_skills": output_dir / "job_skills.csv",
        "location_summary": output_dir / "location_summary.csv",
        "source_summary": output_dir / "source_summary.csv",
        "category_summary": output_dir / "category_summary.csv",
        "skill_demand_summary": output_dir / "skill_demand_summary.csv",
        "company_hiring_summary": output_dir / "company_hiring_summary.csv",
        "salary_summary": output_dir / "salary_summary.csv",
    }

    jobs_export.to_csv(outputs["jobs"], index=False, encoding="utf-8")
    skills.to_csv(outputs["skills"], index=False, encoding="utf-8")
    job_skills_export.to_csv(outputs["job_skills"], index=False, encoding="utf-8")
    location_summary.to_csv(outputs["location_summary"], index=False, encoding="utf-8")
    source_summary.to_csv(outputs["source_summary"], index=False, encoding="utf-8")
    category_summary.to_csv(outputs["category_summary"], index=False, encoding="utf-8")
    skill_demand_summary.to_csv(outputs["skill_demand_summary"], index=False, encoding="utf-8")
    company_hiring_summary.to_csv(outputs["company_hiring_summary"], index=False, encoding="utf-8")
    salary_summary.to_csv(outputs["salary_summary"], index=False, encoding="utf-8")

    print(f"Exported Power BI datasets to {output_dir}")
    return outputs


if __name__ == "__main__":
    export_powerbi_datasets()
