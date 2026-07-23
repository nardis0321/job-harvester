import unittest
from urllib.parse import parse_qs, urlparse

from src.collectors.saramin import build_saramin_category_url, parse_saramin_search_html
from src.main import collect_jobs


SARAMIN_SEARCH_HTML = """
<div id="recruit_info_list">
  <div class="item_recruit" value="54379324">
    <div class="area_job">
      <h2 class="job_tit">
        <a href="/zf_user/jobs/relay/view?view_type=search&amp;rec_idx=54379324"
           title="서버/백엔드 개발자 채용(주니어 신입~4년이하)">
          <span>서버/<b>백엔드</b> 개발자 채용(주니어 신입~4년이하)</span>
        </a>
      </h2>
      <div class="job_date">
        <span class="date">채용시</span>
      </div>
      <div class="job_condition">
        <span><a>서울</a> <a>강남구</a></span>
        <span>신입·경력</span>
        <span>대졸↑</span>
        <span>정규직</span>
      </div>
      <div class="job_sector">
        <b><a>백엔드/서버개발</a></b>, <a>Python</a>, <a>Docker</a>
        <span class="job_day">등록일 26/07/03</span>
      </div>
    </div>
    <div class="area_corp">
      <strong class="corp_name">
        <a>(주)무브먼츠</a>
      </strong>
    </div>
  </div>
</div>
"""


class CollectorTests(unittest.TestCase):
    def test_saramin_category_url_uses_configured_filters_and_page(self):
        url = build_saramin_category_url(3)
        parsed = urlparse(url)
        params = parse_qs(parsed.query)

        self.assertEqual(parsed.path, "/zf_user/jobs/list/job-category")
        self.assertEqual(params["cat_kewd"], ["84"])
        self.assertEqual(params["exp_cd"], ["1,2"])
        self.assertEqual(params["exp_max"], ["1"])
        self.assertEqual(params["exp_none"], ["y"])
        self.assertEqual(params["edu_max"], ["11"])
        self.assertEqual(params["edu_none"], ["y"])
        self.assertEqual(params["loc_mcd"], ["101000,102000,106000"])
        self.assertEqual(params["recruitPage"], ["3"])

    def test_saramin_parser_normalizes_search_result_item(self):
        postings = parse_saramin_search_html(SARAMIN_SEARCH_HTML)

        self.assertEqual(len(postings), 1)
        posting = postings[0]
        self.assertEqual(posting.source, "saramin")
        self.assertEqual(posting.external_id, "54379324")
        self.assertEqual(posting.title, "서버/백엔드 개발자 채용(주니어 신입~4년이하)")
        self.assertEqual(posting.company, "(주)무브먼츠")
        self.assertEqual(posting.location, "서울 강남구")
        self.assertEqual(posting.career_level, "신입·경력")
        self.assertEqual(posting.employment_type, "정규직")
        self.assertEqual(posting.posted_at, "등록일 26/07/03")
        self.assertIn("rec_idx=54379324", posting.url)
        self.assertIn("백엔드/서버개발", posting.tech_stack)
        self.assertIn("Python", posting.tech_stack)
        self.assertIn("Docker", posting.tech_stack)

    def test_collect_jobs_keeps_mock_source_available(self):
        postings = collect_jobs("mock")

        self.assertGreater(len(postings), 0)
        self.assertTrue(all(posting.source == "mock" for posting in postings))


if __name__ == "__main__":
    unittest.main()
