import unittest

from src.filters import is_backend_posting, is_entry_to_one_year_posting
from src.models import JobPosting


KEYWORDS = {
    "backend": {
        "include": ["백엔드", "backend", "server", "api"],
        "exclude": ["프론트엔드", "ios"],
    },
    "experience": {
        "junior_include": ["신입", "junior", "entry", "1년 이하"],
        "senior_exclude": ["2년", "3년", "senior"],
    },
}


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


class FilterTests(unittest.TestCase):
    def test_backend_filter_accepts_backend_posting(self):
        posting = make_posting()

        self.assertTrue(is_backend_posting(posting, KEYWORDS))

    def test_backend_filter_rejects_frontend_posting(self):
        posting = make_posting(
            title="프론트엔드 개발자 신입",
            responsibilities="React UI를 개발합니다.",
            tech_stack=["React"],
        )

        self.assertFalse(is_backend_posting(posting, KEYWORDS))

    def test_backend_filter_does_not_match_short_keywords_inside_words(self):
        posting = make_posting(
            title="Junior Backend Engineer",
            career_level="Junior / Entry",
            responsibilities="Build backend services with Python.",
            tech_stack=["Python"],
        )

        self.assertTrue(is_backend_posting(posting, KEYWORDS))

    def test_experience_filter_accepts_entry_or_one_year(self):
        posting = make_posting(title="Backend Engineer", career_level="경력 1년 이하")

        self.assertTrue(is_entry_to_one_year_posting(posting, KEYWORDS))

    def test_experience_filter_rejects_two_plus_years(self):
        posting = make_posting(title="백엔드 개발자", career_level="경력 3년 이상")

        self.assertFalse(is_entry_to_one_year_posting(posting, KEYWORDS))


if __name__ == "__main__":
    unittest.main()
