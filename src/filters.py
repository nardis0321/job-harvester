from __future__ import annotations

import re
from typing import Dict, Iterable, List

from src.models import JobPosting


KeywordConfig = Dict[str, Dict[str, List[str]]]


def filter_job_postings(postings: Iterable[JobPosting], keywords: KeywordConfig) -> List[JobPosting]:
    return [
        posting
        for posting in postings
        if is_backend_posting(posting, keywords) and is_entry_to_one_year_posting(posting, keywords)
    ]


def is_backend_posting(posting: JobPosting, keywords: KeywordConfig) -> bool:
    text = _normalize(posting.search_text())
    backend_keywords = keywords.get("backend", {})

    has_backend_signal = _contains_any(text, backend_keywords.get("include", []))
    has_excluded_signal = _contains_any(text, backend_keywords.get("exclude", []))

    return has_backend_signal and not has_excluded_signal


def is_entry_to_one_year_posting(posting: JobPosting, keywords: KeywordConfig) -> bool:
    text = _normalize(posting.search_text())
    experience_keywords = keywords.get("experience", {})

    if _contains_any(text, experience_keywords.get("senior_exclude", [])):
        return False

    if _mentions_two_or_more_years(text):
        return False

    return _contains_any(text, experience_keywords.get("junior_include", []))


def _contains_any(text: str, keywords: Iterable[str]) -> bool:
    return any(_keyword_matches(text, _normalize(keyword)) for keyword in keywords)


def _keyword_matches(text: str, keyword: str) -> bool:
    if not keyword:
        return False

    if _is_ascii_keyword(keyword):
        pattern = rf"(?<![a-z0-9]){re.escape(keyword)}(?![a-z0-9])"
        return re.search(pattern, text) is not None

    return keyword in text


def _is_ascii_keyword(keyword: str) -> bool:
    return keyword.isascii() and bool(re.search(r"[a-z0-9]", keyword))


def _mentions_two_or_more_years(text: str) -> bool:
    korean_years = [int(value) for value in re.findall(r"(\d+)\s*년", text)]
    english_years = [int(value) for value in re.findall(r"(\d+)\s*(?:year|years|yrs?)", text)]
    return any(year >= 2 for year in korean_years + english_years)


def _normalize(value: str) -> str:
    return re.sub(r"\s+", " ", value.casefold()).strip()
