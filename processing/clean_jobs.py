"""Clean raw Cambodia job posting data for analysis and database loading."""

from __future__ import annotations

import re
from datetime import datetime, timedelta, timezone
from pathlib import Path

import pandas as pd


PROJECT_ROOT = Path(__file__).resolve().parents[1]
RAW_INPUT_PATH = PROJECT_ROOT / "data" / "raw" / "raw_jobs.csv"
CLEANED_OUTPUT_PATH = PROJECT_ROOT / "data" / "cleaned" / "cleaned_jobs.csv"
KHR_PER_USD = 4100


CATEGORY_KEYWORDS: dict[str, list[str]] = {
    "Information Technology": ["software", "developer", "data", "it ", "network", "system", "programmer", "helpdesk"],
    "Accounting / Finance": ["accountant", "account officer", "account receivable", "finance", "financial", "tax", "audit", "bookkeeper"],
    "Banking / Finance": ["bank", "teller", "credit", "loan", "microfinance", "risk"],
    "Sales / Marketing": ["sales", "marketing", "business development", "digital marketing"],
    "Customer Service": ["customer service", "call center", "support representative"],
    "Human Resources": ["human resources", "hr ", "recruit", "payroll"],
    "Administration": ["admin", "assistant", "secretary", "office"],
    "Operations": ["operation", "supervisor", "branch manager"],
    "Logistics / Supply Chain": ["logistics", "warehouse", "supply chain", "delivery", "procurement"],
    "Education / Training": ["teacher", "trainer", "training", "education", "lecturer"],
    "Hospitality / Tourism": ["hotel", "restaurant", "tourism", "front office", "guest"],
    "Creative / Design": ["designer", "graphic", "creative", "media", "video"],
    "NGO / Development": ["ngo", "development", "project coordinator", "monitoring", "evaluation"],
    "Healthcare": ["medical", "nurse", "health", "doctor", "pharmacy"],
    "Manufacturing": ["factory", "manufacturing", "production", "quality control"],
    "Legal / Compliance": ["legal", "compliance", "law", "contract"],
    "Business Administration": ["executive assistant", "management", "business administration"],
}


def clean_text(value: object, default: str = "Not specified") -> str:
    """Normalize whitespace and missing text values."""

    if value is None or pd.isna(value):
        return default
    text = re.sub(r"\s+", " ", str(value)).strip()
    return text if text else default


def standardize_job_title(title: object) -> str:
    """Normalize job title casing while preserving the actual role."""

    text = clean_text(title)
    text = re.sub(r"\s+", " ", text)
    text = text.strip(" -|")
    if not text:
        return "Not specified"

    replacements = {
        "Hr": "HR",
        "It": "IT",
        "Ui": "UI",
        "Ux": "UX",
        "Seo": "SEO",
        "Cfo": "CFO",
        "Ceo": "CEO",
    }
    title_cased = text.title()
    for original, replacement in replacements.items():
        title_cased = re.sub(rf"\b{original}\b", replacement, title_cased)
    return title_cased


def clean_company_name(company: object) -> str:
    """Remove common company suffix noise while keeping recognizable names."""

    text = clean_text(company)
    text = re.sub(r"\s+", " ", text)
    text = re.sub(r"^(company|employer)\s*:\s*", "", text, flags=re.IGNORECASE)
    return text.strip(" -|")


def clean_location(location: object) -> str:
    """Normalize Cambodia job locations for grouping in Power BI."""

    text = clean_text(location, default="Cambodia")
    text = re.sub(r"\s+", " ", text).strip(", ")
    replacements = {
        "Phnum Penh": "Phnom Penh",
        "PP": "Phnom Penh",
        "Siemreap": "Siem Reap",
        "Sihanouk Ville": "Sihanoukville",
        "Krong Preah Sihanouk": "Sihanoukville",
    }
    for original, replacement in replacements.items():
        text = re.sub(rf"\b{re.escape(original)}\b", replacement, text, flags=re.IGNORECASE)
    return text or "Cambodia"


def infer_job_category(title: str, description: str, existing_value: object) -> str:
    """Infer a broad job market category for dashboard grouping."""

    existing = clean_text(existing_value)
    if existing != "Not specified":
        return existing

    combined = f" {title} {description} ".lower()
    for category, keywords in CATEGORY_KEYWORDS.items():
        if any(keyword in combined for keyword in keywords):
            return category
    return "Other"


def infer_experience_level(title: str, description: str, existing_value: object) -> str:
    """Infer a broad experience level when the source does not provide one."""

    existing = clean_text(existing_value)
    if existing != "Not specified":
        return existing

    combined = f"{title} {description}".lower()
    if any(word in combined for word in ["intern", "internship"]):
        return "Internship"
    if any(word in combined for word in ["junior", "entry level", "fresh graduate", "assistant"]):
        return "Entry level"
    if any(word in combined for word in ["senior", "lead", "manager", "head of", "supervisor"]):
        return "Senior level"
    return "Mid level"


def infer_employment_type(description: str, existing_value: object) -> str:
    """Infer employment type when missing."""

    existing = clean_text(existing_value)
    if existing != "Not specified":
        return existing

    text = description.lower()
    if "intern" in text:
        return "Internship"
    if "contract" in text or "consultant" in text or "consultancy" in text:
        return "Contract"
    if "part-time" in text or "part time" in text:
        return "Part-time"
    if "freelance" in text:
        return "Freelance"
    return "Full-time"


def detect_salary_currency(salary_text: str) -> str:
    """Detect currency from a salary string."""

    lowered = salary_text.lower()
    if "$" in salary_text or "usd" in lowered:
        return "USD"
    if "khr" in lowered or "riel" in lowered or "៛" in salary_text:
        return "KHR"
    return "USD"


def parse_salary(salary: object) -> tuple[float | None, float | None, str]:
    """Extract monthly salary range and normalize it to USD where possible."""

    text = clean_text(salary, default="")
    if not text:
        return None, None, "Unknown"

    lower_text = text.lower().replace(",", "")
    currency = detect_salary_currency(text)
    numbers: list[float] = []
    for raw_number, suffix in re.findall(r"(\d+(?:\.\d+)?)\s*([kK]?)", lower_text):
        number = float(raw_number)
        if suffix.lower() == "k":
            number *= 1000
        numbers.append(number)

    if not numbers:
        return None, None, currency

    # Ignore small counts from unrelated fragments such as "2 years experience".
    numbers = [value for value in numbers if value >= 50]
    if not numbers:
        return None, None, currency

    salary_min = min(numbers)
    salary_max = max(numbers)

    if currency == "KHR":
        salary_min = salary_min / KHR_PER_USD
        salary_max = salary_max / KHR_PER_USD

    if "year" in lower_text or "annual" in lower_text or "annum" in lower_text:
        salary_min = salary_min / 12
        salary_max = salary_max / 12

    return round(salary_min, 2), round(salary_max, 2), currency


def parse_date_posted(value: object) -> str | None:
    """Convert source date text into ISO date format."""

    if value is None or pd.isna(value):
        return None

    text = str(value).strip()
    if not text:
        return None

    parsed = pd.to_datetime(text, errors="coerce", utc=True)
    if not pd.isna(parsed):
        return parsed.date().isoformat()

    lower_text = text.lower()
    today = datetime.now(timezone.utc).date()
    match = re.search(r"(\d+)\s+day", lower_text)
    if match:
        return (today - timedelta(days=int(match.group(1)))).isoformat()
    match = re.search(r"(\d+)\s+month", lower_text)
    if match:
        return (today - timedelta(days=30 * int(match.group(1)))).isoformat()
    if "today" in lower_text or "just posted" in lower_text:
        return today.isoformat()
    if "yesterday" in lower_text:
        return (today - timedelta(days=1)).isoformat()
    return None


def normalize_for_duplicate_key(value: object) -> str:
    """Normalize text for duplicate detection."""

    text = clean_text(value, default="").lower()
    text = re.sub(r"[^a-z0-9\u1780-\u17FF]+", " ", text)
    return re.sub(r"\s+", " ", text).strip()


def clean_jobs(
    input_path: Path = RAW_INPUT_PATH,
    output_path: Path = CLEANED_OUTPUT_PATH,
) -> pd.DataFrame:
    """Clean raw jobs and write a cleaned CSV."""

    if not input_path.exists():
        raise FileNotFoundError(
            f"Raw data file not found: {input_path}. Run scraper/scrape_jobs.py first."
        )

    df = pd.read_csv(input_path)

    expected_columns = [
        "job_id",
        "source_name",
        "job_title",
        "company_name",
        "location",
        "salary",
        "employment_type",
        "experience_level",
        "job_category",
        "job_description",
        "skills",
        "date_posted",
        "source_url",
        "scraped_at",
    ]
    for column in expected_columns:
        if column not in df.columns:
            df[column] = None

    df["source_name"] = df["source_name"].apply(lambda value: clean_text(value, "Unknown"))
    df["job_title"] = df["job_title"].apply(standardize_job_title)
    df["company_name"] = df["company_name"].apply(clean_company_name)
    df["location"] = df["location"].apply(clean_location)
    df["job_description"] = df["job_description"].apply(
        lambda value: clean_text(value, default="No description available")
    )
    df["salary"] = df["salary"].apply(lambda value: clean_text(value, default=""))

    salary_values = df["salary"].apply(parse_salary)
    df["salary_min"] = salary_values.apply(lambda values: values[0])
    df["salary_max"] = salary_values.apply(lambda values: values[1])
    df["salary_currency"] = salary_values.apply(lambda values: values[2])
    df["salary_avg"] = df[["salary_min", "salary_max"]].mean(axis=1)

    df["employment_type"] = df.apply(
        lambda row: infer_employment_type(row["job_description"], row["employment_type"]),
        axis=1,
    )
    df["experience_level"] = df.apply(
        lambda row: infer_experience_level(
            row["job_title"], row["job_description"], row["experience_level"]
        ),
        axis=1,
    )
    df["job_category"] = df.apply(
        lambda row: infer_job_category(row["job_title"], row["job_description"], row["job_category"]),
        axis=1,
    )
    df["date_posted"] = df["date_posted"].apply(parse_date_posted)
    df["scraped_at"] = pd.to_datetime(df["scraped_at"], errors="coerce", utc=True).dt.strftime(
        "%Y-%m-%dT%H:%M:%SZ"
    )
    df["source_url"] = df["source_url"].apply(lambda value: clean_text(value, default=""))
    df["skills"] = df["skills"].apply(lambda value: clean_text(value, default=""))

    row_count_before_dedupe = len(df)
    df = df.drop_duplicates(subset=["job_id"], keep="first")
    df = df.drop_duplicates(
        subset=["source_name", "job_title", "company_name", "location", "source_url"],
        keep="first",
    )
    df["_duplicate_key"] = (
        df["job_title"].apply(normalize_for_duplicate_key)
        + "|"
        + df["company_name"].apply(normalize_for_duplicate_key)
        + "|"
        + df["location"].apply(normalize_for_duplicate_key)
    )
    df = df.drop_duplicates(subset=["_duplicate_key"], keep="first")
    duplicates_removed = row_count_before_dedupe - len(df)

    output_columns = [
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
    df = df[output_columns].sort_values(["source_name", "job_category", "location", "job_title"])

    output_path.parent.mkdir(parents=True, exist_ok=True)
    df.to_csv(output_path, index=False, encoding="utf-8")
    print(
        f"Saved {len(df)} cleaned job records to {output_path} "
        f"({duplicates_removed} duplicate rows removed)"
    )
    return df


if __name__ == "__main__":
    clean_jobs()
