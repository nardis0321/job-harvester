from __future__ import annotations

from pathlib import Path

from src.collectors.mock import MockJobCollector
from src.config import load_keywords
from src.dedupe import deduplicate_postings
from src.exporter import export_jobs_to_csv
from src.filters import filter_job_postings


OUTPUT_PATH = Path("data/jobs.csv")


def main() -> None:
    keywords = load_keywords()
    collector = MockJobCollector()

    collected = collector.collect()
    filtered = filter_job_postings(collected, keywords)
    unique_postings = deduplicate_postings(filtered)
    exported_count = export_jobs_to_csv(unique_postings, OUTPUT_PATH)

    print(f"Collected: {len(collected)}")
    print(f"Matched: {len(filtered)}")
    print(f"Exported: {exported_count}")
    print(f"CSV: {OUTPUT_PATH}")


if __name__ == "__main__":
    main()

