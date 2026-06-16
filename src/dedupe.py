from __future__ import annotations

import re
from typing import Iterable, List, Tuple
from urllib.parse import urlsplit, urlunsplit

from src.models import JobPosting


def deduplicate_postings(postings: Iterable[JobPosting]) -> List[JobPosting]:
    seen: set[Tuple[str, ...]] = set()
    unique_postings: List[JobPosting] = []

    for posting in postings:
        key = _dedupe_key(posting)
        if key in seen:
            continue
        seen.add(key)
        unique_postings.append(posting)

    return unique_postings


def _dedupe_key(posting: JobPosting) -> Tuple[str, ...]:
    if posting.url:
        return ("url", _normalize_url(posting.url))

    if posting.source and posting.external_id:
        return ("source_id", _normalize_text(posting.source), _normalize_text(posting.external_id))

    return (
        "fallback",
        _normalize_text(posting.company),
        _normalize_text(posting.title),
        _normalize_text(posting.location),
    )


def _normalize_url(url: str) -> str:
    parsed = urlsplit(url.strip())
    path = parsed.path.rstrip("/")
    return urlunsplit((parsed.scheme.casefold(), parsed.netloc.casefold(), path, "", ""))


def _normalize_text(value: str) -> str:
    return re.sub(r"\s+", " ", value.casefold()).strip()

