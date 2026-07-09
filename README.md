# Job Seeking Tool

신입~1년차 백엔드 개발자 채용공고를 수집하고 필터링해 CSV로 내보내는 작은 Python 프로젝트입니다.

현재 구현된 collector는 mock 데이터와 사람인(saramin) 검색 결과입니다. 로그인/캡차/차단 우회, 웹 UI, DB 저장, 자동화는 포함하지 않습니다.

## 구조

```text
config/keywords.yaml        # 백엔드/경력 필터 키워드
src/models.py               # JobPosting 데이터 모델
src/collectors/base.py      # collector 공통 인터페이스
src/collectors/mock.py      # mock 채용공고 collector
src/collectors/saramin.py   # 사람인 검색 결과 collector
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

기본값은 mock collector입니다. source를 직접 고를 수도 있습니다.

```bash
python3 -m src.main --source mock
python3 -m src.main --source saramin
python3 -m src.main --source saramin --query "백엔드 신입" --max-pages 1
python3 -m src.main --source all
```

실행하면 선택한 collector가 공고를 수집한 뒤 `config/keywords.yaml` 기준으로 백엔드 공고와 신입~1년차 공고만 남기고, 중복을 제거한 결과를 `data/jobs.csv`에 저장합니다.

## Collector

- `mock`: 네트워크 없이 고정된 샘플 공고를 반환합니다. 테스트와 CSV export 흐름 확인용입니다.
- `saramin`: 사람인 검색 페이지에서 `백엔드 신입`, `백엔드 주니어`, `backend junior` 검색 결과를 가져옵니다. `--query`를 지정하면 해당 검색어만 사용합니다.
- `all`: 현재 등록된 collector를 모두 실행합니다.

사람인 collector는 공개 검색 HTML을 `JobPosting` 모델로 정규화합니다. 사이트 HTML 구조 변경, 네트워크 오류, 인증서 설정, 봇 차단, 검색 결과 정책 변경이 있으면 빈 결과가 나올 수 있습니다. 요청 실패나 파싱 실패는 경고를 출력하고 프로그램 전체를 중단하지 않습니다.

## 테스트

```bash
python3 -m unittest
```

## 실제 사이트 collector를 붙이는 위치

실제 사이트 collector는 `src/collectors/` 아래에 새 파일로 추가하면 됩니다. 예를 들어 `src/collectors/some_site.py`에 collector 클래스를 만들고, `collect()` 메서드가 `list[JobPosting]`을 반환하게 구현합니다. 각 `JobPosting`에는 회사 분류인 `company_category`와 공고 상세인 `responsibilities`, `qualifications`, `preferred_qualifications`를 채워야 합니다.

이후 `src/main.py`의 `COLLECTORS`에 source 이름과 collector 인스턴스를 등록하면 됩니다. 필터, 중복 제거, CSV export는 같은 파이프라인을 그대로 사용할 수 있습니다.
