"""Scrape general job postings for Cambodia from multiple public sources.

The scraper targets public search/listing pages only and never logs in. Some
job boards, especially LinkedIn, often block automated requests or render data
with JavaScript. For that reason, each source has a realistic sample fallback so
the local pipeline still creates a useful dataset for coursework and Power BI.
"""

from __future__ import annotations

import hashlib
import os
import re
import time
from dataclasses import dataclass
from datetime import datetime, timedelta, timezone
from pathlib import Path
from typing import Iterable
from urllib.parse import urljoin

import pandas as pd

try:
    import requests
except ImportError:  # pragma: no cover - local fallback path.
    requests = None

try:
    from bs4 import BeautifulSoup
except ImportError:  # pragma: no cover - local fallback path.
    BeautifulSoup = None


PROJECT_ROOT = Path(__file__).resolve().parents[1]
RAW_OUTPUT_PATH = PROJECT_ROOT / "data" / "raw" / "raw_jobs.csv"


@dataclass(frozen=True)
class JobSource:
    source_name: str
    url: str
    base_url: str
    card_selectors: tuple[str, ...]
    title_selectors: tuple[str, ...]
    company_selectors: tuple[str, ...]
    location_selectors: tuple[str, ...]
    salary_selectors: tuple[str, ...]
    date_selectors: tuple[str, ...]
    description_selectors: tuple[str, ...]


@dataclass
class JobRecord:
    job_id: str
    source_name: str
    job_title: str
    company_name: str
    location: str
    salary: str
    employment_type: str
    experience_level: str
    job_category: str
    job_description: str
    skills: str
    date_posted: str
    source_url: str
    scraped_at: str


JOB_SOURCES: list[JobSource] = [
    JobSource(
        source_name="LinkedIn",
        url="https://www.linkedin.com/jobs/jobs-in-cambodia",
        base_url="https://www.linkedin.com",
        card_selectors=(
            ".base-card",
            ".job-search-card",
            "li.jobs-search__results-list",
            "li",
        ),
        title_selectors=(
            ".base-search-card__title",
            ".job-search-card__title",
            "h3",
            "a",
        ),
        company_selectors=(
            ".base-search-card__subtitle",
            ".job-search-card__subtitle",
            "h4",
        ),
        location_selectors=(".job-search-card__location", ".job-result-card__location"),
        salary_selectors=(".job-search-card__salary-info",),
        date_selectors=("time",),
        description_selectors=(".job-search-card__snippet", "p"),
    ),
    JobSource(
        source_name="BongThom",
        url="https://www.bongthom.com/",
        base_url="https://www.bongthom.com",
        card_selectors=("tr", "li", ".job-list", ".job-item", "[class*='job']"),
        title_selectors=("a", "td:first-child", "h3", "h4"),
        company_selectors=("td:nth-child(2)", ".company", "[class*='company']"),
        location_selectors=(".location", "[class*='location']", "td:nth-child(3)"),
        salary_selectors=(".salary", "[class*='salary']", "td:nth-child(4)"),
        date_selectors=("time", "td:last-child"),
        description_selectors=("td", "p"),
    ),
    JobSource(
        source_name="CamHR",
        url="https://www.camhr.com/default.aspx",
        base_url="https://www.camhr.com",
        card_selectors=("tr", "li", ".job-item", ".joblist", "[class*='job']"),
        title_selectors=("a", "h3", "h4", "[class*='title']"),
        company_selectors=("[class*='company']", ".comname", "td:nth-child(2)"),
        location_selectors=("[class*='location']", "td:nth-child(3)"),
        salary_selectors=("[class*='salary']", "td:nth-child(4)"),
        date_selectors=("time", "td:last-child"),
        description_selectors=("p", "td"),
    ),
    JobSource(
        source_name="Khmer24",
        url="https://www.khmer24.com/en/jobs.html",
        base_url="https://www.khmer24.com",
        card_selectors=(".item", ".item-list", ".list-item", "article", "li", "[class*='job']"),
        title_selectors=(".title", "h2", "h3", "a"),
        company_selectors=(".company", "[class*='company']"),
        location_selectors=(".location", "[class*='location']", "[class*='address']"),
        salary_selectors=(".price", ".salary", "[class*='salary']", "[class*='price']"),
        date_selectors=("time", ".date", "[class*='date']"),
        description_selectors=(".description", ".detail", "p"),
    ),
    JobSource(
        source_name="Talent.com",
        url="https://www.talent.com/jobs?k=&l=Phnom+Penh%2C+Cambodia",
        base_url="https://www.talent.com",
        card_selectors=(".card", ".job-card", ".job", "article", "li", "[class*='job']"),
        title_selectors=("[class*='title']", "h2", "h3", "a"),
        company_selectors=("[class*='company']", ".company"),
        location_selectors=("[class*='location']", ".location"),
        salary_selectors=("[class*='salary']", ".salary"),
        date_selectors=("time", "[class*='date']"),
        description_selectors=("[class*='description']", "p"),
    ),
    JobSource(
        source_name="Pelprek",
        url="https://pelprek.com/",
        base_url="https://pelprek.com",
        card_selectors=(".job-item", ".job-list", ".vacancy", "article", "tr", "li", "[class*='job']"),
        title_selectors=("[class*='title']", "h2", "h3", "h4", "a"),
        company_selectors=("[class*='company']", ".company", "td:nth-child(2)"),
        location_selectors=("[class*='location']", ".location", "td:nth-child(3)"),
        salary_selectors=("[class*='salary']", ".salary", "td:nth-child(4)"),
        date_selectors=("time", "[class*='date']", "td:last-child"),
        description_selectors=("[class*='description']", ".detail", "p", "td"),
    ),
    JobSource(
        source_name="HRINC Jobs",
        url="https://www.hrincjobs.com/",
        base_url="https://www.hrincjobs.com",
        card_selectors=(".job-item", ".job-card", ".vacancy", "article", "tr", "li", "[class*='job']"),
        title_selectors=("[class*='title']", "h2", "h3", "h4", "a"),
        company_selectors=("[class*='company']", ".company", "td:nth-child(2)"),
        location_selectors=("[class*='location']", ".location", "td:nth-child(3)"),
        salary_selectors=("[class*='salary']", ".salary", "td:nth-child(4)"),
        date_selectors=("time", "[class*='date']", "td:last-child"),
        description_selectors=("[class*='description']", ".detail", "p", "td"),
    ),
    JobSource(
        source_name="SeekFitJob",
        url="https://www.seekfitjob.com/",
        base_url="https://www.seekfitjob.com",
        card_selectors=(".job-item", ".job-card", ".card", "article", "li", "[class*='job']"),
        title_selectors=("[class*='title']", "h2", "h3", "h4", "a"),
        company_selectors=("[class*='company']", ".company"),
        location_selectors=("[class*='location']", ".location"),
        salary_selectors=("[class*='salary']", ".salary"),
        date_selectors=("time", "[class*='date']"),
        description_selectors=("[class*='description']", ".detail", "p"),
    ),
    JobSource(
        source_name="Khmer Online Jobs",
        url="https://www.khmeronlinejobs.com/",
        base_url="https://www.khmeronlinejobs.com",
        card_selectors=(".job-item", ".job-card", ".post", "article", "li", "[class*='job']"),
        title_selectors=("[class*='title']", "h1", "h2", "h3", "a"),
        company_selectors=("[class*='company']", ".company", "[class*='employer']"),
        location_selectors=("[class*='location']", ".location"),
        salary_selectors=("[class*='salary']", ".salary"),
        date_selectors=("time", "[class*='date']"),
        description_selectors=("[class*='description']", ".entry-content", "p"),
    ),
    JobSource(
        source_name="Expertini Cambodia",
        url="https://kh.expertini.com/",
        base_url="https://kh.expertini.com",
        card_selectors=(".job-item", ".job-card", ".card", "article", "li", "[class*='job']"),
        title_selectors=("[class*='title']", "h2", "h3", "h4", "a"),
        company_selectors=("[class*='company']", ".company"),
        location_selectors=("[class*='location']", ".location"),
        salary_selectors=("[class*='salary']", ".salary"),
        date_selectors=("time", "[class*='date']"),
        description_selectors=("[class*='description']", ".detail", "p"),
    ),
    JobSource(
        source_name="CamUp Job",
        url="https://camupjob.com/",
        base_url="https://camupjob.com",
        card_selectors=(".job-item", ".job-card", ".card", "article", "li", "[class*='job']"),
        title_selectors=("[class*='title']", "h2", "h3", "h4", "a"),
        company_selectors=("[class*='company']", ".company"),
        location_selectors=("[class*='location']", ".location"),
        salary_selectors=("[class*='salary']", ".salary"),
        date_selectors=("time", "[class*='date']"),
        description_selectors=("[class*='description']", ".detail", "p"),
    ),
    JobSource(
        source_name="S&V Cambodia Job",
        url="https://camsvjob.com/",
        base_url="https://camsvjob.com",
        card_selectors=(".job-item", ".job-card", ".card", "article", "tr", "li", "[class*='job']"),
        title_selectors=("[class*='title']", "h2", "h3", "h4", "a"),
        company_selectors=("[class*='company']", ".company", "td:nth-child(2)"),
        location_selectors=("[class*='location']", ".location", "td:nth-child(3)"),
        salary_selectors=("[class*='salary']", ".salary", "td:nth-child(4)"),
        date_selectors=("time", "[class*='date']", "td:last-child"),
        description_selectors=("[class*='description']", ".detail", "p", "td"),
    ),
    JobSource(
        source_name="CamMA HR",
        url="https://cammahr.com/",
        base_url="https://cammahr.com",
        card_selectors=(".job-item", ".job-card", ".card", "article", "li", "[class*='job']"),
        title_selectors=("[class*='title']", "h2", "h3", "h4", "a"),
        company_selectors=("[class*='company']", ".company"),
        location_selectors=("[class*='location']", ".location"),
        salary_selectors=("[class*='salary']", ".salary"),
        date_selectors=("time", "[class*='date']"),
        description_selectors=("[class*='description']", ".detail", "p"),
    ),
]


HEADERS = {
    "User-Agent": (
        "Mozilla/5.0 (compatible; UniversityDataVisualizationProject/1.0; "
        "+https://example.edu/local-course-project)"
    ),
    "Accept-Language": "en-US,en;q=0.9,km;q=0.7",
}

REJECT_TITLE_PHRASES = {
    "login",
    "register",
    "privacy policy",
    "terms",
    "contact us",
    "download",
    "follow",
    "job seeker",
    "employer",
    "search",
    "home",
    "about us",
    "useful information",
}

NON_CAMBODIA_LOCATION_PHRASES = (
    "united states",
    "remote, us",
    " ny,",
    " ca,",
    " tx,",
    " fl,",
    " nj,",
    " nc,",
    " minnesota",
    "california",
    "new york",
    "chicago",
    "houston",
    "milwaukee",
    "rochester",
)

CAMBODIA_LOCATION_PHRASES = (
    "cambodia",
    "phnom penh",
    "siem reap",
    "battambang",
    "sihanouk",
    "kampot",
    "kandal",
    "takeo",
    "kampong",
    "remote, cambodia",
)


def ensure_output_directories() -> None:
    """Create expected data folders if they do not already exist."""

    for folder in [
        PROJECT_ROOT / "data" / "raw",
        PROJECT_ROOT / "data" / "cleaned",
        PROJECT_ROOT / "data" / "powerbi",
    ]:
        folder.mkdir(parents=True, exist_ok=True)


def clean_inline_text(value: object, default: str = "") -> str:
    """Normalize whitespace without losing Khmer or accented text."""

    if value is None:
        return default
    text = re.sub(r"\s+", " ", str(value)).strip()
    return text or default


def stable_job_id(*values: str) -> str:
    """Create a stable identifier from visible job attributes."""

    joined = "|".join(value.strip().lower() for value in values if value)
    digest = hashlib.sha1(joined.encode("utf-8")).hexdigest()[:12]
    return f"JOB-{digest}"


def polite_get(url: str, delay_seconds: float = 2.0, timeout: int = 20) -> str:
    """Fetch a public page with a delay and a browser-like user agent."""

    if requests is None:
        raise RuntimeError("The requests package is not installed.")

    time.sleep(max(delay_seconds, 0))
    response = requests.get(url, headers=HEADERS, timeout=timeout)
    response.raise_for_status()
    return response.text


def first_text(element, selectors: Iterable[str], default: str = "") -> str:
    """Return text from the first matching CSS selector in a job card."""

    for selector in selectors:
        match = element.select_one(selector)
        if match:
            text = clean_inline_text(match.get_text(" ", strip=True))
            if text:
                return text
    return default


def card_text(element, limit: int = 600) -> str:
    """Return readable text from a listing card."""

    text = clean_inline_text(element.get_text(" ", strip=True))
    return text[:limit]


def first_link(element, source: JobSource) -> str:
    """Return a job detail link when the card exposes one."""

    for selector in ("a[href*='job']", "a[href*='career']", "a[href]"):
        link = element.select_one(selector)
        if link:
            href = clean_inline_text(link.get("href", ""))
            if href:
                return urljoin(source.base_url, href)
    return source.url


def is_probable_job_title(title: str) -> bool:
    """Filter out navigation labels and empty listing text."""

    lowered = title.lower()
    if len(title) < 4 or len(title) > 120:
        return False
    if any(phrase in lowered for phrase in REJECT_TITLE_PHRASES):
        return False
    return bool(re.search(r"[A-Za-z\u1780-\u17FF]", title))


def is_cambodia_relevant_location(location: str, strict: bool = False) -> bool:
    """Reject obvious non-Cambodia locations returned by broad job aggregators."""

    lowered = location.lower()
    if any(phrase in lowered for phrase in NON_CAMBODIA_LOCATION_PHRASES):
        return False
    if strict:
        return any(phrase in lowered for phrase in CAMBODIA_LOCATION_PHRASES)
    return True


def source_records_are_useful(records: list[JobRecord]) -> bool:
    """Detect source pages that returned navigation links or category pages."""

    if len(records) < 5:
        return False

    with_company_or_salary = [
        record
        for record in records
        if record.company_name != "Not specified" or clean_inline_text(record.salary)
    ]
    likely_detail_pages = [
        record
        for record in records
        if "c-jobs-" not in record.source_url
        and not record.source_url.endswith("/default.aspx")
        and not record.source_url.endswith("/a/job")
        and not record.source_url.endswith("/a/jobwanted")
        and not record.source_url.endswith("/a/adviser")
    ]
    return len(with_company_or_salary) / len(records) >= 0.35 and len(likely_detail_pages) / len(records) >= 0.5


def extract_salary_from_text(text: str) -> str:
    """Find a salary phrase inside card text when no salary selector exists."""

    patterns = [
        r"\$\s?\d[\d,]*(?:\s?[-+]\s?\$?\s?\d[\d,]*)?(?:\s?(?:per month|/month|monthly))?",
        r"USD\s?\d[\d,]*(?:\s?[-+]\s?\d[\d,]*)?",
        r"KHR\s?\d[\d,]*(?:\s?[-+]\s?\d[\d,]*)?",
    ]
    for pattern in patterns:
        match = re.search(pattern, text, flags=re.IGNORECASE)
        if match:
            return clean_inline_text(match.group(0))
    return ""


def infer_basic_employment_type(text: str) -> str:
    """Infer employment type from listing text."""

    lowered = text.lower()
    if "intern" in lowered:
        return "Internship"
    if "part-time" in lowered or "part time" in lowered:
        return "Part-time"
    if "contract" in lowered or "consultant" in lowered or "consultancy" in lowered:
        return "Contract"
    if "freelance" in lowered:
        return "Freelance"
    return "Not specified"


def infer_basic_experience_level(text: str) -> str:
    """Infer experience level from listing text."""

    lowered = text.lower()
    if "intern" in lowered:
        return "Internship"
    if "fresh graduate" in lowered or "entry level" in lowered or "junior" in lowered:
        return "Entry level"
    if "senior" in lowered or "manager" in lowered or "head of" in lowered:
        return "Senior level"
    return "Not specified"


def parse_source_cards(html: str, source: JobSource, max_records: int) -> list[JobRecord]:
    """Parse job cards from one configured source."""

    if BeautifulSoup is None:
        raise RuntimeError("The beautifulsoup4 package is not installed.")

    soup = BeautifulSoup(html, "lxml")
    seen_elements: set[int] = set()
    cards = []
    for selector in source.card_selectors:
        for element in soup.select(selector):
            element_id = id(element)
            if element_id not in seen_elements:
                seen_elements.add(element_id)
                cards.append(element)

    records: list[JobRecord] = []
    scraped_at = datetime.now(timezone.utc).isoformat()

    for card in cards:
        all_text = card_text(card)
        title = first_text(card, source.title_selectors)
        if not is_probable_job_title(title):
            continue

        company = first_text(card, source.company_selectors, default="Not specified")
        location = first_text(card, source.location_selectors, default="Cambodia")
        strict_location = source.source_name == "Talent.com"
        if not is_cambodia_relevant_location(location, strict=strict_location):
            continue

        salary = first_text(card, source.salary_selectors) or extract_salary_from_text(all_text)
        posted = first_text(card, source.date_selectors)
        description = first_text(card, source.description_selectors) or all_text or title
        source_url = first_link(card, source)

        records.append(
            JobRecord(
                job_id=stable_job_id(source.source_name, title, company, location, source_url),
                source_name=source.source_name,
                job_title=title,
                company_name=company,
                location=location or "Cambodia",
                salary=salary,
                employment_type=infer_basic_employment_type(all_text),
                experience_level=infer_basic_experience_level(all_text),
                job_category="Not specified",
                job_description=description,
                skills="",
                date_posted=posted,
                source_url=source_url,
                scraped_at=scraped_at,
            )
        )

        if len(records) >= max_records:
            break

    return records


def make_sample_description(
    category: str,
    tools: str,
    soft_skill: str,
    index: int = 0,
) -> str:
    """Build a compact but realistic fallback job description."""

    business_contexts = [
        "branch operations",
        "head office reporting",
        "customer growth",
        "digital transformation",
        "regional expansion",
        "daily service delivery",
        "compliance monitoring",
        "process improvement",
        "team coordination",
        "monthly performance review",
    ]
    requirements = [
        "English communication",
        "Khmer communication",
        "Microsoft Office",
        "Excel reporting",
        "time management",
        "attention to detail",
        "team collaboration",
        "problem solving",
        "customer focus",
        "basic data analysis",
    ]
    context = business_contexts[index % len(business_contexts)]
    requirement = requirements[(index * 2) % len(requirements)]
    return (
        f"Work in {category.lower()} for a Cambodia-based employer. "
        f"Daily work includes {tools}, {context}, and clear reporting. "
        f"Candidates should show {soft_skill}, {requirement}, "
        "and the ability to work with cross-functional teams."
    )


def source_slug(source_name: str) -> str:
    """Return a URL-safe source label for generated sample links."""

    return re.sub(r"[^a-z0-9]+", "-", source_name.lower()).strip("-")


def make_salary_variant(base_salary: str, index: int, source_index: int) -> str:
    """Create a deterministic salary variation around a base sample range."""

    numbers = [int(value.replace(",", "")) for value in re.findall(r"\d[\d,]*", base_salary)]
    if len(numbers) < 2:
        return base_salary

    factor = 0.84 + (((index * 11) + (source_index * 7)) % 35) / 100
    min_salary = max(150, int(round(numbers[0] * factor / 10) * 10))
    max_salary = max(min_salary + 100, int(round(numbers[1] * factor / 10) * 10))
    return f"${min_salary:,} - ${max_salary:,} per month"


def make_title_variant(base_title: str, index: int) -> str:
    """Create title variety without changing the core role too much."""

    prefixes = [
        "",
        "",
        "",
        "Junior",
        "Senior",
        "Assistant",
        "Branch",
        "Regional",
        "Lead",
        "Provincial",
        "Corporate",
        "Field",
    ]
    suffixes = [
        "",
        "",
        "",
        "Officer",
        "Specialist",
        "Coordinator",
        "Executive",
        "Associate",
        "Representative",
        "Supervisor",
    ]
    focus_areas = [
        "",
        "",
        "Retail",
        "Corporate",
        "SME",
        "Operations",
        "Digital",
        "Branch Network",
        "Customer Experience",
        "Compliance",
        "Reporting",
        "Field Operations",
        "Partnerships",
        "Product",
        "Service Delivery",
        "Quality",
        "Training",
        "Regional Office",
        "Head Office",
        "Community Programs",
        "Logistics",
        "Procurement",
        "Financial Services",
        "Hospitality",
        "Education",
        "Healthcare",
        "Manufacturing",
        "Technology",
        "Development Programs",
        "Business Support",
    ]
    prefix = prefixes[index % len(prefixes)]
    suffix = suffixes[(index // len(prefixes)) % len(suffixes)]
    focus = focus_areas[(index // (len(prefixes) * len(suffixes))) % len(focus_areas)]

    title = base_title
    if prefix and not title.lower().startswith(prefix.lower()):
        title = f"{prefix} {title}"
    if suffix and suffix.lower() not in title.lower():
        title = f"{title} {suffix}"
    if focus and focus.lower() not in title.lower():
        title = f"{title} - {focus}"
    return title


def fallback_sample_jobs(
    sources: list[JobSource] | None = None,
    records_per_source: int = 150,
    start_index: int = 1,
) -> list[JobRecord]:
    """Return realistic sample records for each configured source."""

    active_sources = sources or JOB_SOURCES
    scraped_at = datetime.now(timezone.utc).isoformat()
    base_date = datetime.now(timezone.utc).date()
    companies = [
        "ABA Bank",
        "ACLEDA Bank",
        "Wing Bank",
        "Smart Axiata",
        "Cellcard",
        "Chip Mong Group",
        "AEON Mall Cambodia",
        "Prince Bank",
        "Sathapana Bank",
        "Foodpanda Cambodia",
        "Manulife Cambodia",
        "RMA Cambodia",
        "Ezecom",
        "Canadia Bank",
        "Amret Microfinance",
        "Phnom Penh SEZ",
        "DHL Cambodia",
        "KPMG Cambodia",
        "Cambodia Airports",
        "Nham24",
        "CamboTicket",
        "Passerelles Numeriques Cambodia",
        "Angkor Hospital for Children",
        "World Vision Cambodia",
        "Sabay Digital",
    ]
    companies.extend(
        [
            "Vattanac Bank",
            "J Trust Royal Bank",
            "LOLC Cambodia",
            "Pi Pay",
            "Cambodia Post Bank",
            "Brown Coffee",
            "Lucky Supermarket",
            "Makro Cambodia",
            "Phnom Penh Commercial Bank",
            "BRED Bank Cambodia",
            "Toyota Cambodia",
            "Ford Cambodia",
            "Huawei Cambodia",
            "Metfone",
            "Grab Cambodia",
            "Heineken Cambodia",
            "Coca-Cola Cambodia",
            "Cambrew",
            "Pactics Cambodia",
            "ISPP",
            "CIA First International School",
            "Royal University of Phnom Penh",
            "PSE Cambodia",
            "CARE Cambodia",
            "Plan International Cambodia",
            "GIZ Cambodia",
            "UNDP Cambodia",
            "DKSH Cambodia",
            "Zuellig Pharma Cambodia",
            "Rosewood Phnom Penh",
            "Sofitel Phnom Penh Phokeethra",
            "Hyatt Regency Phnom Penh",
            "Angkor Enterprise",
            "Cambodia Securities Exchange",
            "MekongNet",
            "Digi Cambodia",
            "BookMeBus",
            "Pathmazing",
            "Codingate",
            "Clik Payment",
        ]
    )
    locations = [
        "Phnom Penh",
        "Siem Reap",
        "Battambang",
        "Sihanoukville",
        "Kampot",
        "Kandal",
        "Banteay Meanchey",
        "Kampong Cham",
        "Takeo",
        "Remote, Cambodia",
    ]
    locations.extend(
        [
            "Poipet, Banteay Meanchey",
            "Kep",
            "Koh Kong",
            "Pursat",
            "Kampong Speu",
            "Kampong Thom",
            "Kampong Chhnang",
            "Prey Veng",
            "Svay Rieng",
            "Kratie",
            "Ratanakiri",
            "Mondulkiri",
            "Stung Treng",
            "Oddar Meanchey",
            "Preah Vihear",
            "Tbong Khmum",
            "Pailin",
            "Multiple provinces, Cambodia",
            "Hybrid, Phnom Penh",
            "Phnom Penh - Daun Penh",
            "Phnom Penh - Toul Kork",
            "Phnom Penh - Chamkarmon",
            "Phnom Penh - Sen Sok",
            "Phnom Penh - Mean Chey",
            "Phnom Penh - Chbar Ampov",
            "Siem Reap City",
            "Battambang City",
            "Sihanoukville Special Economic Zone",
            "Kandal - Takhmao",
        ]
    )
    templates = [
        ("Sales Executive", "Sales / Marketing", "$300 - $700 per month", "Full-time", "Entry level", "customer service, lead generation, Excel sales reports, CRM updates", "communication and negotiation skills"),
        ("Digital Marketing Officer", "Sales / Marketing", "$400 - $900 per month", "Full-time", "Mid level", "social media campaigns, content planning, Google Analytics, Excel and digital marketing reporting", "creative communication"),
        ("Accountant", "Accounting / Finance", "$450 - $850 per month", "Full-time", "Mid level", "monthly closing, QuickBooks, Excel, tax documents and financial reporting", "accuracy and problem solving"),
        ("Finance Analyst", "Accounting / Finance", "$600 - $1,200 per month", "Full-time", "Mid level", "budget analysis, Excel models, Power BI dashboards and management reporting", "analytical thinking"),
        ("Customer Service Representative", "Customer Service", "$250 - $500 per month", "Full-time", "Entry level", "customer support, complaint handling, CRM updates and English communication", "patience and service mindset"),
        ("HR Officer", "Human Resources", "$400 - $800 per month", "Full-time", "Mid level", "recruitment, payroll coordination, employee records, Excel tracking and policy communication", "confidentiality and communication"),
        ("Admin Assistant", "Administration", "$250 - $450 per month", "Full-time", "Entry level", "document control, scheduling, Microsoft Office, email communication and office coordination", "organization skills"),
        ("Operations Supervisor", "Operations", "$600 - $1,100 per month", "Full-time", "Senior level", "daily operations planning, KPI tracking, Excel reporting and team supervision", "leadership"),
        ("IT Support Officer", "Information Technology", "$500 - $1,000 per month", "Full-time", "Mid level", "hardware support, network troubleshooting, Microsoft 365, Windows and user training", "problem solving"),
        ("Software Developer", "Information Technology", "$800 - $1,800 per month", "Full-time", "Mid level", "Python, JavaScript, SQL, Git, API development and database maintenance", "team collaboration"),
        ("Data Analyst", "Information Technology", "$700 - $1,500 per month", "Full-time", "Mid level", "SQL queries, Excel, Python, Power BI dashboards, data cleaning and statistics", "business communication"),
        ("Logistics Coordinator", "Logistics / Supply Chain", "$350 - $750 per month", "Full-time", "Entry level", "shipment tracking, warehouse coordination, Excel inventory reports and vendor communication", "attention to detail"),
        ("Warehouse Supervisor", "Logistics / Supply Chain", "$450 - $900 per month", "Full-time", "Mid level", "stock control, team scheduling, safety procedures and Excel reporting", "leadership"),
        ("Teacher", "Education / Training", "$500 - $1,200 per month", "Full-time", "Mid level", "lesson planning, classroom management, English communication and student assessment", "presentation skills"),
        ("Training Coordinator", "Education / Training", "$450 - $950 per month", "Full-time", "Mid level", "training schedules, learning materials, Excel tracking and stakeholder communication", "facilitation skills"),
        ("Hotel Front Office Supervisor", "Hospitality / Tourism", "$400 - $850 per month", "Full-time", "Mid level", "guest service, reservation systems, complaint handling and English communication", "customer focus"),
        ("Restaurant Manager", "Hospitality / Tourism", "$600 - $1,200 per month", "Full-time", "Senior level", "staff scheduling, inventory, customer service, sales tracking and operations control", "leadership"),
        ("Graphic Designer", "Creative / Design", "$400 - $900 per month", "Full-time", "Mid level", "Adobe Photoshop, Illustrator, branding, social media design and campaign support", "creativity"),
        ("Project Coordinator", "NGO / Development", "$600 - $1,300 per month", "Contract", "Mid level", "project planning, donor reporting, monitoring data, Excel and stakeholder communication", "coordination skills"),
        ("Monitoring and Evaluation Officer", "NGO / Development", "$700 - $1,500 per month", "Contract", "Mid level", "survey design, data collection, Excel, Power BI, statistics and report writing", "analytical thinking"),
        ("Business Development Manager", "Business Administration", "$900 - $2,000 per month", "Full-time", "Senior level", "partnership building, sales strategy, market research, CRM and proposal writing", "negotiation skills"),
        ("Procurement Officer", "Procurement", "$450 - $900 per month", "Full-time", "Mid level", "vendor sourcing, purchase orders, price comparison, Excel and compliance documentation", "integrity"),
        ("Bank Teller", "Banking / Finance", "$300 - $600 per month", "Full-time", "Entry level", "cash handling, customer service, banking systems and daily transaction reports", "accuracy"),
        ("Credit Officer", "Banking / Finance", "$400 - $900 per month", "Full-time", "Mid level", "loan assessment, field visits, risk checks, Excel reports and customer communication", "judgment"),
        ("Medical Sales Representative", "Healthcare", "$450 - $1,000 per month", "Full-time", "Mid level", "client visits, product presentation, sales reports and relationship management", "communication skills"),
        ("Nurse", "Healthcare", "$350 - $800 per month", "Full-time", "Mid level", "patient care, health records, shift coordination and clinical communication", "attention to detail"),
        ("Quality Control Officer", "Manufacturing", "$400 - $850 per month", "Full-time", "Mid level", "inspection reports, production data, Excel, safety standards and process improvement", "accuracy"),
        ("Factory Line Leader", "Manufacturing", "$350 - $750 per month", "Full-time", "Mid level", "team supervision, production targets, quality checks and shift reporting", "leadership"),
        ("Legal Assistant", "Legal / Compliance", "$450 - $900 per month", "Full-time", "Entry level", "document review, contract filing, Microsoft Office and compliance tracking", "confidentiality"),
        ("Executive Assistant", "Business Administration", "$500 - $1,000 per month", "Full-time", "Mid level", "calendar management, meeting notes, travel booking, Excel and English communication", "organization skills"),
    ]

    records: list[JobRecord] = []
    for source_index, source in enumerate(active_sources):
        slug = source_slug(source.source_name)
        for local_index in range(records_per_source):
            index = start_index + (source_index * records_per_source) + local_index
            template_index = (index * 17 + source_index * 11) % len(templates)
            company_index = (index * 37 + source_index * 13) % len(companies)
            location_index = (index * 29 + source_index * 7) % len(locations)
            base_title, category, base_salary, employment, experience, tools, soft_skill = templates[
                template_index
            ]
            title = make_title_variant(base_title, index)
            salary = make_salary_variant(base_salary, index, source_index)
            company = companies[company_index]
            location = locations[location_index]
            source_url = f"https://sample.local/{slug}/cambodia-job-{index:05d}"
            records.append(
                JobRecord(
                    job_id=f"SAMPLE-{slug.upper()}-{index:05d}",
                    source_name=source.source_name,
                    job_title=title,
                    company_name=company,
                    location=location,
                    salary=salary,
                    employment_type=employment,
                    experience_level=experience,
                    job_category=category,
                    job_description=make_sample_description(category, tools, soft_skill, index),
                    skills="",
                    date_posted=(base_date - timedelta(days=index % 45)).isoformat(),
                    source_url=source_url,
                    scraped_at=scraped_at,
                )
            )

    return records


def records_to_dataframe(records: list[JobRecord]) -> pd.DataFrame:
    """Convert job records to a consistently ordered DataFrame."""

    columns = [
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
    return pd.DataFrame([record.__dict__ for record in records], columns=columns)


def scrape_jobs(output_path: Path = RAW_OUTPUT_PATH, use_fallback: bool = True) -> pd.DataFrame:
    """Scrape jobs from configured sources and save raw results to CSV."""

    ensure_output_directories()
    delay = float(os.getenv("SCRAPER_DELAY_SECONDS", "2"))
    max_records_per_source = int(os.getenv("SCRAPER_MAX_RECORDS_PER_SOURCE", "50"))
    target_total_records = int(os.getenv("SCRAPER_TARGET_TOTAL_RECORDS", "12000"))
    target_records_per_source = int(
        os.getenv(
            "SCRAPER_TARGET_RECORDS_PER_SOURCE",
            str((target_total_records + len(JOB_SOURCES) - 1) // len(JOB_SOURCES)),
        )
    )
    mode = os.getenv("SCRAPER_MODE", "live_with_fallback").lower()

    records: list[JobRecord] = []

    for source in JOB_SOURCES:
        source_records: list[JobRecord] = []
        if mode != "sample":
            try:
                html = polite_get(source.url, delay_seconds=delay)
                source_records = parse_source_cards(
                    html,
                    source=source,
                    max_records=max_records_per_source,
                )
                if source_records and not source_records_are_useful(source_records):
                    print(
                        f"Parsed {len(source_records)} low-quality records from "
                        f"{source.source_name}; using fallback for that source."
                    )
                    source_records = []
                else:
                    print(f"Parsed {len(source_records)} records from {source.source_name}")
            except Exception as exc:  # noqa: BLE001 - fallback keeps the project runnable.
                print(f"Scraping warning: {source.source_name} unavailable. Reason: {exc}")

        if use_fallback and target_records_per_source > len(source_records):
            needed = target_records_per_source - len(source_records)
            print(
                f"Adding {needed} generated Cambodia records for {source.source_name} "
                f"to reach {target_records_per_source} rows."
            )
            source_records.extend(
                fallback_sample_jobs(
                    [source],
                    records_per_source=needed,
                    start_index=len(records) + len(source_records) + 1,
                )
            )

        records.extend(source_records)

    if not records and use_fallback:
        print("No records collected. Using full sample fallback dataset.")
        records = fallback_sample_jobs(records_per_source=target_records_per_source)

    df = records_to_dataframe(records)
    output_path.parent.mkdir(parents=True, exist_ok=True)
    df.to_csv(output_path, index=False, encoding="utf-8")
    print(f"Saved {len(df)} raw job records to {output_path}")
    return df


if __name__ == "__main__":
    scrape_jobs()
