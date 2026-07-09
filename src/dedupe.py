from __future__ import annotations

import re
from typing import Iterable, List, Tuple
from urllib.parse import parse_qsl, urlencode, urlsplit, urlunsplit

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
        return ("source_id", posting.source, posting.external_id)


def _normalize_url(url: str) -> str:
    parsed = urlsplit(url.strip())
    path = parsed.path.rstrip("/")
    query = _normalize_query(parsed.query)
    return urlunsplit((parsed.scheme.casefold(), parsed.netloc.casefold(), path, query, ""))


def _normalize_query(query: str) -> str:
    stable_params = [
        (key, value)
        for key, value in parse_qsl(query, keep_blank_values=False)
        if key in {"rec_idx"}
    ]
    return urlencode(stable_params)