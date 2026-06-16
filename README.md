# Job Seeking Tool

신입~1년차 백엔드 개발자 채용공고를 수집하고 필터링해 CSV로 내보내는 작은 Python 프로젝트입니다.

현재 구현 범위는 mock 데이터 collector입니다. 실제 구인 사이트 크롤링, 로그인/캡차/차단 우회, 웹 UI, DB 저장, 자동화는 포함하지 않습니다.

## 구조

```text
config/keywords.yaml        # 백엔드/경력 필터 키워드
src/models.py               # JobPosting 데이터 모델
src/collectors/mock.py      # mock 채용공고 collector
src/filters.py              # 백엔드 및 신입~1년차 필터
src/dedupe.py               # 중복 제거
src/exporter.py             # CSV export
src/main.py                 # CLI 진입점
tests/                      # 필터와 중복 제거 테스트
data/jobs.csv               # 실행 후 생성되는 결과 CSV
```

CSV에는 `company` 바로 뒤에 `company_category`가 나오고, 공고 설명은 `업무내용`, `지원자격`, `우대사항` 세 컬럼으로 나뉘어 저장됩니다.

## 실행 방법

Python 3.8 이상에서 동작합니다.

```bash
python -m src.main
```

환경에 따라 `python` 명령이 Python 3을 가리키지 않으면 다음처럼 실행합니다.

```bash
python3 -m src.main
```

실행하면 mock collector가 공고를 수집한 뒤 `config/keywords.yaml` 기준으로 백엔드 공고와 신입~1년차 공고만 남기고, 중복을 제거한 결과를 `data/jobs.csv`에 저장합니다.

## 테스트

```bash
python -m unittest
```

## 실제 사이트 collector를 붙이는 위치

실제 사이트 collector는 `src/collectors/` 아래에 새 파일로 추가하면 됩니다. 예를 들어 `src/collectors/some_site.py`에 collector 클래스를 만들고, `collect()` 메서드가 `list[JobPosting]`을 반환하게 구현합니다. 각 `JobPosting`에는 회사 분류인 `company_category`와 공고 상세인 `responsibilities`, `qualifications`, `preferred_qualifications`를 채워야 합니다.

이후 `src/main.py`에서 `MockJobCollector` import와 인스턴스 생성 부분을 새 collector로 교체하면 됩니다. 필터, 중복 제거, CSV export는 같은 파이프라인을 그대로 사용할 수 있습니다.
