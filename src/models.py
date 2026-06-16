from __future__ import annotations

from dataclasses import dataclass, field
from typing import Dict, List


@dataclass(frozen=True)
class JobPosting:
    source: str
    external_id: str
    title: str
    company: str
    company_category: str
    location: str
    career_level: str
    employment_type: str
    url: str
    posted_at: str
    responsibilities: str
    qualifications: str
    preferred_qualifications: str
    tech_stack: List[str] = field(default_factory=list)

    def search_text(self) -> str:
        return " ".join(
            [
                self.title,
                self.company,
                self.company_category,
                self.location,
                self.career_level,
                self.employment_type,
                self.responsibilities,
                self.qualifications,
                self.preferred_qualifications,
                " ".join(self.tech_stack),
            ]
        )

    def to_csv_row(self) -> Dict[str, str]:
        return {
            "source": self.source,
            "external_id": self.external_id,
            "title": self.title,
            "company": self.company,
            "company_category": self.company_category,
            "location": self.location,
            "career_level": self.career_level,
            "employment_type": self.employment_type,
            "url": self.url,
            "posted_at": self.posted_at,
            "업무내용": self.responsibilities,
            "지원자격": self.qualifications,
            "우대사항": self.preferred_qualifications,
            "tech_stack": ", ".join(self.tech_stack),
        }
