from __future__ import annotations

import logging
import re
import ssl
import time
from html.parser import HTMLParser
from typing import Dict, Iterable, List, Optional, Tuple
from urllib.error import HTTPError, URLError
from urllib.parse import parse_qs, parse_qsl, urlencode, urljoin, urlparse, urlunparse
from urllib.request import Request, urlopen

from src.collectors.base import BaseCollector
from src.models import JobPosting


LOGGER = logging.getLogger(__name__)

BASE_URL = "https://www.saramin.co.kr"
JOB_CATEGORY_URL = (
    f"{BASE_URL}/zf_user/jobs/list/job-category"
    "?cat_kewd=84"
    "&exp_cd=1%2C2"
    "&exp_max=1"
    "&exp_none=y"
    "&edu_max=11"
    "&edu_none=y"
    "&loc_mcd=101000%2C102000%2C106000"
)
DEFAULT_TIMEOUT_SECONDS = 10
DEFAULT_DELAY_SECONDS = 0.7

TECH_KEYWORDS = {
    "api",
    "aws",
    "backend",
    "back-end",
    "dbms",
    "docker",
    "fastapi",
    "git",
    "golang",
    "java",
    "javascript",
    "kotlin",
    "linux",
    "mariadb",
    "mysql",
    "nest",
    "nestjs",
    "node",
    "node.js",
    "php",
    "postgresql",
    "python",
    "rdbms",
    "redis",
    "spring",
    "sql",
    "백엔드",
    "서버",
    "웹개발",
}

VOID_TAGS = {
    "area",
    "base",
    "br",
    "col",
    "embed",
    "hr",
    "img",
    "input",
    "link",
    "meta",
    "param",
    "source",
    "track",
    "wbr",
}


class SaraminCollector(BaseCollector):
    source = "saramin"

    def __init__(
        self,
        timeout_seconds: int = DEFAULT_TIMEOUT_SECONDS,
        delay_seconds: float = DEFAULT_DELAY_SECONDS,
    ) -> None:
        self.timeout_seconds = timeout_seconds
        self.delay_seconds = delay_seconds

    def collect(self, query: str = "", max_pages: int = 1) -> List[JobPosting]:
        postings: List[JobPosting] = []

        if query:
            LOGGER.info("Saramin collector ignores query=%r and uses the configured job-category filters.", query)

        last_page = max(1, max_pages)
        for page in range(1, last_page + 1):
            try:
                html = self._fetch_search_page(page)
                postings.extend(parse_saramin_search_html(html))
            except (HTTPError, URLError, TimeoutError, OSError, UnicodeDecodeError) as error:
                LOGGER.warning("Saramin request failed for page=%s: %s", page, error)
                return []
            except Exception as error:
                LOGGER.warning("Saramin parsing failed for page=%s: %s", page, error)
                return []

            if page < last_page:
                time.sleep(self.delay_seconds)

        return postings

    def _fetch_search_page(self, page: int) -> str:
        request = Request(
            build_saramin_category_url(page),
            headers={
                "User-Agent": (
                    "Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) "
                    "AppleWebKit/537.36 (KHTML, like Gecko) "
                    "Chrome/126.0 Safari/537.36"
                ),
                "Accept-Language": "ko-KR,ko;q=0.9,en-US;q=0.7,en;q=0.6",
            },
        )

        try:
            return self._read_request(request)
        except URLError as error:
            if not _is_ssl_verification_error(error):
                raise
            LOGGER.warning("Saramin HTTPS certificate verification failed; retrying with unverified context.")
            context = ssl._create_unverified_context()
            return self._read_request(request, context=context)

    def _read_request(self, request: Request, context: Optional[ssl.SSLContext] = None) -> str:
        with urlopen(request, timeout=self.timeout_seconds, context=context) as response:
            charset = response.headers.get_content_charset() or "utf-8"
            return response.read().decode(charset, errors="replace")


def build_saramin_category_url(page: int) -> str:
    parsed = urlparse(JOB_CATEGORY_URL)
    params = [
        (key, value)
        for key, value in parse_qsl(parsed.query, keep_blank_values=True)
        if key != "recruitPage"
    ]
    params.append(("recruitPage", str(max(1, page))))
    return urlunparse(parsed._replace(query=urlencode(params)))


def parse_saramin_search_html(html: str) -> List[JobPosting]:
    parser = _SaraminSearchParser()
    parser.feed(html)
    parser.close()
    return [posting for posting in (_build_posting(item) for item in parser.items) if posting is not None]


def _build_posting(item: Dict[str, object]) -> Optional[JobPosting]:
    title = _clean_text(str(item.get("title") or ""))
    company = _clean_text(str(item.get("company") or ""))
    external_id = _clean_text(str(item.get("external_id") or ""))
    href = _clean_text(str(item.get("href") or ""))

    if not external_id:
        external_id = _extract_rec_idx(href)

    if not title or not company or not external_id:
        LOGGER.warning("Skipping Saramin posting with missing required fields: %s", item)
        return None

    url = urljoin(BASE_URL, href) if href else f"{BASE_URL}/zf_user/jobs/relay/view?rec_idx={external_id}"
    conditions = [_clean_text(value) for value in _string_list(item.get("conditions")) if _clean_text(value)]
    sectors = [_clean_text(value) for value in _string_list(item.get("sectors")) if _clean_text(value)]
    deadline = _clean_text(str(item.get("deadline") or ""))
    posted_at = _clean_text(str(item.get("posted_at") or ""))

    location = conditions[0] if len(conditions) >= 1 else ""
    career_level = conditions[1] if len(conditions) >= 2 else ""
    education = conditions[2] if len(conditions) >= 3 else ""
    employment_type = _find_employment_type(conditions)
    company_category = ", ".join(sectors[:3])
    tech_stack = _extract_tech_stack(sectors)
    sector_text = ", ".join(sectors)

    return JobPosting(
        source="saramin",
        external_id=external_id,
        title=title,
        company=company,
        company_category=company_category,
        location=location,
        career_level=career_level,
        employment_type=employment_type,
        url=url,
        posted_at=posted_at or deadline,
        responsibilities=_join_non_empty([title, sector_text]),
        qualifications=_join_non_empty([career_level, education, deadline]),
        preferred_qualifications="",
        tech_stack=tech_stack,
    )


def _extract_rec_idx(url: str) -> str:
    query = parse_qs(urlparse(url).query)
    values = query.get("rec_idx", [])
    return values[0] if values else ""


def _find_employment_type(conditions: Iterable[str]) -> str:
    for condition in conditions:
        if any(keyword in condition for keyword in ("정규직", "계약직", "인턴", "프리랜서", "파견직")):
            return condition
    return ""


def _extract_tech_stack(sectors: Iterable[str]) -> List[str]:
    tech_stack: List[str] = []
    seen = set()

    for sector in sectors:
        normalized = sector.casefold()
        if not any(keyword in normalized or keyword in sector for keyword in TECH_KEYWORDS):
            continue
        if normalized in seen:
            continue
        seen.add(normalized)
        tech_stack.append(sector)

    return tech_stack


def _join_non_empty(values: Iterable[str]) -> str:
    return " | ".join(value for value in (_clean_text(value) for value in values) if value)


def _string_list(value: object) -> List[str]:
    if isinstance(value, list):
        return [str(item) for item in value]
    return []


def _class_tokens(attrs: List[Tuple[str, Optional[str]]]) -> List[str]:
    attr_map = dict(attrs)
    return (attr_map.get("class") or "").split()


def _has_class(attrs: List[Tuple[str, Optional[str]]], class_name: str) -> bool:
    return class_name in _class_tokens(attrs)


def _attr(attrs: List[Tuple[str, Optional[str]]], name: str) -> str:
    value = dict(attrs).get(name)
    return value or ""


def _clean_text(value: str) -> str:
    return re.sub(r"\s+", " ", value).strip()


def _is_ssl_verification_error(error: URLError) -> bool:
    reason = getattr(error, "reason", None)
    return isinstance(reason, ssl.SSLCertVerificationError) or "CERTIFICATE_VERIFY_FAILED" in str(error)


class _SaraminSearchParser(HTMLParser):
    def __init__(self) -> None:
        super().__init__(convert_charrefs=True)
        self.items: List[Dict[str, object]] = []
        self._current: Optional[Dict[str, object]] = None
        self._item_depth = 0
        self._class_stack: List[List[str]] = []
        self._capture_name: Optional[str] = None
        self._capture_parts: List[str] = []

    def handle_starttag(self, tag: str, attrs: List[Tuple[str, Optional[str]]]) -> None:
        classes = _class_tokens(attrs)
        if tag not in VOID_TAGS:
            self._class_stack.append(classes)

        if tag == "div" and "item_recruit" in classes:
            self._current = {
                "external_id": _attr(attrs, "value"),
                "conditions": [],
                "sectors": [],
            }
            self._item_depth = 1
            return

        if self._current is None:
            return

        if tag not in VOID_TAGS:
            self._item_depth += 1

        if tag == "a" and self._inside("job_tit"):
            self._current["href"] = _attr(attrs, "href")
            title_attr = _clean_text(_attr(attrs, "title"))
            if title_attr:
                self._current["title"] = title_attr
            self._start_capture("title")
            return

        if tag == "a" and self._inside("corp_name"):
            self._start_capture("company")
            return

        if tag == "span" and self._inside("job_condition"):
            self._start_capture("condition")
            return

        if tag == "span" and _has_class(attrs, "date") and self._inside("job_date"):
            self._start_capture("deadline")
            return

        if tag == "span" and _has_class(attrs, "job_day"):
            self._start_capture("posted_at")
            return

        if tag == "a" and self._inside("job_sector"):
            self._start_capture("sector")

    def handle_endtag(self, tag: str) -> None:
        if self._current is not None and self._capture_name is not None:
            if self._capture_name == "title" and tag == "a":
                self._finish_capture()
            elif self._capture_name == "company" and tag == "a":
                self._finish_capture()
            elif self._capture_name in {"condition", "deadline", "posted_at"} and tag == "span":
                self._finish_capture()
            elif self._capture_name == "sector" and tag == "a":
                self._finish_capture()

        if self._current is not None:
            self._item_depth -= 1
            if self._item_depth <= 0:
                self.items.append(self._current)
                self._current = None

        if self._class_stack:
            self._class_stack.pop()

    def handle_data(self, data: str) -> None:
        if self._current is not None and self._capture_name is not None:
            self._capture_parts.append(data)

    def _inside(self, class_name: str) -> bool:
        return any(class_name in classes for classes in self._class_stack)

    def _start_capture(self, name: str) -> None:
        self._capture_name = name
        self._capture_parts = []

    def _finish_capture(self) -> None:
        if self._current is None or self._capture_name is None:
            return

        value = _clean_text("".join(self._capture_parts))
        name = self._capture_name

        if value:
            if name == "condition":
                self._append_current("conditions", value)
            elif name == "sector":
                self._append_current("sectors", value)
            else:
                self._current[name] = value

        self._capture_name = None
        self._capture_parts = []

    def _append_current(self, key: str, value: str) -> None:
        values = self._current.setdefault(key, [])
        if isinstance(values, list):
            values.append(value)
