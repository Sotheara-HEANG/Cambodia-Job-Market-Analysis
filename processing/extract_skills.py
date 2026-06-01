"""Extract common requirements and skills from general job descriptions."""

from __future__ import annotations

import re
from pathlib import Path

import pandas as pd


PROJECT_ROOT = Path(__file__).resolve().parents[1]
CLEANED_JOBS_PATH = PROJECT_ROOT / "data" / "cleaned" / "cleaned_jobs.csv"
JOB_SKILLS_OUTPUT_PATH = PROJECT_ROOT / "data" / "cleaned" / "job_skills.csv"

SKILL_PATTERNS: dict[str, list[str]] = {
    "Communication": [r"\bcommunication\b", r"\bpresentation\b", r"\bpresent\b", r"\bstakeholder\b"],
    "English": [r"\benglish\b"],
    "Khmer": [r"\bkhmer\b"],
    "Microsoft Office": [r"\bmicrosoft office\b", r"\bms office\b", r"\bword\b", r"\bpowerpoint\b"],
    "Excel": [r"\bexcel\b", r"\bspreadsheet\b"],
    "Customer Service": [r"\bcustomer service\b", r"\bcustomer support\b", r"\bguest service\b"],
    "Sales": [r"\bsales\b", r"\blead generation\b", r"\bbusiness development\b"],
    "Digital Marketing": [r"\bdigital marketing\b", r"\bsocial media\b", r"\bgoogle analytics\b", r"\bseo\b"],
    "Accounting": [r"\baccounting\b", r"\bbookkeeping\b", r"\btax\b", r"\bmonthly closing\b"],
    "Finance": [r"\bfinance\b", r"\bfinancial\b", r"\bbudget\b"],
    "QuickBooks": [r"\bquickbooks\b"],
    "CRM": [r"\bcrm\b"],
    "Leadership": [r"\bleadership\b", r"\bteam supervision\b", r"\bsupervis", r"\bmanagement\b"],
    "Problem Solving": [r"\bproblem solving\b", r"\btroubleshooting\b"],
    "Project Management": [r"\bproject management\b", r"\bproject planning\b", r"\bproject coordinator\b"],
    "Procurement": [r"\bprocurement\b", r"\bpurchase order\b", r"\bvendor sourcing\b"],
    "Logistics": [r"\blogistics\b", r"\bshipment\b", r"\bwarehouse\b", r"\binventory\b"],
    "Teaching": [r"\bteaching\b", r"\bteacher\b", r"\blesson planning\b", r"\bclassroom\b"],
    "Graphic Design": [r"\bgraphic design\b", r"\bdesigner\b", r"\bphotoshop\b", r"\billustrator\b"],
    "Adobe Photoshop": [r"\bphotoshop\b"],
    "Adobe Illustrator": [r"\billustrator\b"],
    "Reporting": [r"\breporting\b", r"\breports\b", r"\breport writing\b"],
    "Data Collection": [r"\bdata collection\b", r"\bsurvey\b", r"\bmonitoring data\b"],
    "Python": [r"\bpython\b"],
    "SQL": [r"\bsql\b", r"\bquery\b", r"\bqueries\b"],
    "Power BI": [r"\bpower\s*bi\b", r"\bpowerbi\b"],
    "Tableau": [r"\btableau\b"],
    "Statistics": [r"\bstatistics\b", r"\bstatistical\b"],
    "Data Visualization": [r"\bdata visualization\b", r"\bdata visualisation\b", r"\bdashboard\b", r"\bdashboards\b"],
    "Data Cleaning": [r"\bdata cleaning\b", r"\bclean data\b", r"\bclean datasets\b"],
    "Machine Learning": [r"\bmachine learning\b", r"\bml\b"],
    "Git": [r"\bgit\b", r"\bgithub\b", r"\bgitlab\b"],
    "JavaScript": [r"\bjavascript\b", r"\bjs\b"],
    "API Development": [r"\bapi\b", r"\bapis\b"],
    "Network Support": [r"\bnetwork\b", r"\bwindows\b", r"\bmicrosoft 365\b", r"\bhardware\b"],
}


def extract_skills_from_text(text: object) -> list[str]:
    """Return canonical skills found in a text block."""

    if text is None or pd.isna(text):
        return []

    value = str(text)
    found: list[str] = []
    for skill, patterns in SKILL_PATTERNS.items():
        for pattern in patterns:
            if re.search(pattern, value, flags=re.IGNORECASE):
                found.append(skill)
                break
    return found


def extract_job_skills(
    cleaned_jobs_path: Path = CLEANED_JOBS_PATH,
    output_path: Path = JOB_SKILLS_OUTPUT_PATH,
    update_jobs_file: bool = True,
) -> pd.DataFrame:
    """Extract skills into a many-to-many CSV and update cleaned jobs."""

    if not cleaned_jobs_path.exists():
        raise FileNotFoundError(
            f"Cleaned data file not found: {cleaned_jobs_path}. Run processing/clean_jobs.py first."
        )

    jobs = pd.read_csv(cleaned_jobs_path)
    rows: list[dict[str, str]] = []
    skill_lists: list[str] = []

    for _, job in jobs.iterrows():
        combined_text = " ".join(
            [
                str(job.get("job_title", "")),
                str(job.get("job_category", "")),
                str(job.get("job_description", "")),
                str(job.get("skills", "")),
            ]
        )
        skills = extract_skills_from_text(combined_text)
        skill_lists.append("; ".join(skills))
        for skill in skills:
            rows.append({"job_id": job["job_id"], "skill": skill})

    job_skills = pd.DataFrame(rows, columns=["job_id", "skill"]).drop_duplicates()
    output_path.parent.mkdir(parents=True, exist_ok=True)
    job_skills.to_csv(output_path, index=False, encoding="utf-8")

    if update_jobs_file:
        jobs["skills"] = skill_lists
        jobs.to_csv(cleaned_jobs_path, index=False, encoding="utf-8")

    print(f"Saved {len(job_skills)} job-skill records to {output_path}")
    return job_skills


if __name__ == "__main__":
    extract_job_skills()
