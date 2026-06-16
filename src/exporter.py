from __future__ import annotations

import csv
from pathlib import Path
from typing import Iterable

from src.models import JobPosting


CSV_COLUMNS = [
    "source",
    "external_id",
    "title",
    "company",
    "company_category",
    "location",
    "career_level",
    "employment_type",
    "url",
    "posted_at",
    "업무내용",
    "지원자격",
    "우대사항",
    "tech_stack",
]


def export_jobs_to_csv(postings: Iterable[JobPosting], path: Path) -> int:
    rows = [posting.to_csv_row() for posting in postings]
    path.parent.mkdir(parents=True, exist_ok=True)

    with path.open("w", encoding="utf-8", newline="") as file:
        writer = csv.DictWriter(file, fieldnames=CSV_COLUMNS)
        writer.writeheader()
        writer.writerows(rows)

    return len(rows)
