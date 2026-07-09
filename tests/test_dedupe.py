import unittest

from src.dedupe import deduplicate_postings
from src.models import JobPosting


def make_posting(**overrides):
    values = {
        "source": "test",
        "external_id": "1",
        "title": "백엔드 개발자 신입",
        "company": "테스트컴퍼니",
        "company_category": "테스트",
        "location": "서울",
        "career_level": "신입",
        "employment_type": "정규직",
        "url": "https://example.com/jobs/1",
        "posted_at": "2026-06-16",
        "responsibilities": "API 서버를 개발합니다.",
        "qualifications": "신입 지원 가능",
        "preferred_qualifications": "Python 경험",
        "tech_stack": ["Python"],
    }
    values.update(overrides)
    return JobPosting(**values)


class DedupeTests(unittest.TestCase):
    def test_deduplicates_by_normalized_url(self):
        postings = [
            make_posting(external_id="1", url="https://example.com/jobs/1?utm_source=a"),
            make_posting(external_id="2", url="https://example.com/jobs/1/"),
        ]

        self.assertEqual(len(deduplicate_postings(postings)), 1)

    def test_deduplicates_by_source_and_external_id_when_url_missing(self):
        postings = [
            make_posting(url="", external_id="same-id"),
            make_posting(url="", external_id="same-id", title="다른 제목"),
        ]

        self.assertEqual(len(deduplicate_postings(postings)), 1)

    def test_preserves_distinct_stable_query_identifiers(self):
        postings = [
            make_posting(external_id="1", url="https://example.com/jobs/relay/view?rec_idx=1&utm_source=a"),
            make_posting(external_id="2", url="https://example.com/jobs/relay/view?rec_idx=2&utm_source=a"),
        ]

        self.assertEqual(len(deduplicate_postings(postings)), 2)

    def test_preserves_first_seen_order(self):
        first = make_posting(external_id="1", url="https://example.com/jobs/1")
        second = make_posting(external_id="2", url="https://example.com/jobs/2")

        self.assertEqual(deduplicate_postings([first, second]), [first, second])


if __name__ == "__main__":
    unittest.main()
