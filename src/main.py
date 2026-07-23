from __future__ import annotations

import argparse
from pathlib import Path
from typing import Dict, List

from src.collectors.base import BaseCollector
from src.collectors.mock import MockJobCollector
from src.collectors.saramin import SaraminCollector
from src.config import load_keywords
from src.dedupe import deduplicate_postings
from src.exporter import export_jobs_to_csv
from src.filters import filter_job_postings
from src.models import JobPosting


OUTPUT_PATH = Path("data/jobs.csv")
COLLECTORS: Dict[str, BaseCollector] = {
    "mock": MockJobCollector(),
    "saramin": SaraminCollector(),
}


def main() -> None:
    args = parse_args()
    keywords = load_keywords()

    collected = collect_jobs(args.source, args.query, args.max_pages)
    filtered = filter_job_postings(collected, keywords)
    unique_postings = deduplicate_postings(filtered)
    exported_count = export_jobs_to_csv(unique_postings, OUTPUT_PATH)

    print(f"Source: {args.source}")
    print(f"Collected: {len(collected)}")
    print(f"Matched: {len(filtered)}")
    print(f"Exported: {exported_count}")
    print(f"CSV: {OUTPUT_PATH}")


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(description="Collect and export entry-level backend job postings.")
    parser.add_argument(
        "--source",
        choices=["mock", "saramin", "all"],
        default="mock",
        help="Collector source to run. Defaults to mock.",
    )
    parser.add_argument(
        "--query",
        default="",
        help="Optional search query for collectors that support one. Saramin ignores this and uses category filters.",
    )
    parser.add_argument(
        "--max-pages",
        type=int,
        default=1,
        help="Maximum search result pages per query for real collectors.",
    )
    return parser.parse_args()


def collect_jobs(source: str, query: str = "", max_pages: int = 1) -> List[JobPosting]:
    if source == "all":
        postings: List[JobPosting] = []
        for collector in COLLECTORS.values():
            postings.extend(collector.collect(query=query, max_pages=max_pages))
        return postings

    return COLLECTORS[source].collect(query=query, max_pages=max_pages)


if __name__ == "__main__":
    main()
