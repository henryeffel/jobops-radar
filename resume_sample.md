## SUMMARY

Python을 중심으로 백엔드 API, 데이터 처리, 머신러닝 모델과 생성형 AI 기능을 구현해 왔습니다. Microsoft AI School 프로젝트 **IEUM**에서는 LLM이 회의 내용을 구조화해 반환한 JSON 데이터를 파싱·검증하고, 이를 RAG 검색 및 업무 자동화 파이프라인으로 전달하는 백엔드 흐름을 담당했습니다.

단순히 모델 API를 호출하는 데서 끝내지 않고, AI 출력이 다음 시스템에서 안정적으로 사용될 수 있도록 데이터 구조를 정의하고 서비스 사이의 연결을 구현하는 작업에 집중했습니다. 최근에는 FastAPI, SQLAlchemy, Alembic, 테스트를 기반으로 데이터 모델과 REST API를 설계하며 AI 기능을 실제 제품 구조 안에 넣을 수 있는 백엔드 역량을 강화하고 있습니다.

---

## SKILLS

- **Backend:** Python, FastAPI, SQLAlchemy, Alembic, REST API
- **Generative AI:** Azure OpenAI, RAG, Structured Output, JSON Parsing, Vector Search
- **Data:** Pandas, NumPy, scikit-learn
- **Tools:** Git, GitHub, Linux

---

# PROJECTS

## IEUM — RAG 기반 AI 회의 업무 자동화

**역할:** Backend · RAG Automation

**기술:** Python, Azure OpenAI, JSON, RAG, Azure AI Search, Azure Logic Apps

### 문제

LLM이 회의 내용을 요약해도 출력 결과가 곧바로 검색이나 자동화에 사용될 수 있는 상태는 아니었습니다. 응답 안에 요약, 결정사항, 담당자, 기한, 실행 항목이 함께 섞여 있었고, 필드가 누락되거나 형식이 달라지면 RAG 적재와 후속 자동화가 중단될 수 있었습니다.

특히 같은 회의 내용이라도 LLM 응답 구조가 달라질 수 있어, 생성 결과를 그대로 다음 서비스에 넘기는 방식은 안정성이 낮다고 판단했습니다.

### 해결

- LLM 응답을 `summary`, `decisions`, `actionItems`, `insights` 등 용도별 JSON 필드로 분리
- 필수값 누락, 잘못된 데이터 형식, 비어 있는 배열을 확인하는 파싱·검증 로직 구현
- 검색에 필요한 회의 맥락 데이터와 일정·메일 자동화에 필요한 실행 데이터를 분리
- 파싱된 회의 요약을 RAG 적재 형식으로 변환해 벡터 검색 파이프라인으로 전달
- Action Item에서 담당자, 업무 내용, 기한을 추출해 후속 자동화 시스템이 처리할 수 있는 구조로 변환
- AI 응답 형식과 백엔드 입력 형식이 맞지 않는 경우를 줄이기 위해 팀 내 데이터 계약을 정리

### 결과

- 자유 형식에 가까운 LLM 출력을 후속 시스템이 처리 가능한 구조화 데이터로 변환
- 회의 요약 결과를 단순 화면 출력에서 끝내지 않고, 과거 회의 검색에 재사용할 수 있는 데이터로 축적
- RAG 검색용 데이터와 업무 실행용 데이터를 분리해 각 기능의 입력 구조를 명확하게 만듦
- 회의 기록 → LLM 분석 → JSON 파싱 → RAG 적재 → 업무 자동화로 이어지는 파이프라인 구현

---

## JobOps Radar — 채용공고 데이터 관리 및 분석 백엔드

**Personal Project | Backend Developer**

**Tech Stack:** Python, FastAPI, SQLAlchemy, Alembic, Pydantic, SQLite, Pytest

채용공고와 공고별 요구사항을 구조화해 저장하고 조회하는 REST API 프로젝트입니다. 데이터 저장 자체보다 중복 방지, 관계 모델링, 입력값 검증과 테스트 가능한 서비스 구조에 초점을 맞췄습니다.

### 주요 구현

- `JobPosting`과 `JobRequirement` 모델 간 one-to-many 관계 설계
- `(source, external_id)` 복합 unique constraint를 통해 동일 공고 중복 저장 방지
- 중요도 범위를 데이터베이스 Check Constraint와 Pydantic 검증으로 이중 관리
- 모델·스키마·서비스·라우터 계층 분리
- Alembic을 이용한 데이터베이스 마이그레이션 관리
- 공고별 요구사항 생성 및 조회 REST API 구현
- 모델과 서비스 레이어 테스트 작성
- 기능 설계, API 흐름 및 trade-off를 README와 개발 문서에 기록

### 핵심 경험

- 데이터 무결성을 애플리케이션 코드에만 의존하지 않고 DB 제약조건까지 포함해 설계
- 외부 데이터를 반복 수집하는 환경에서 idempotency와 중복 저장 문제를 고려
- 기능 구현 전 Problem·Goal·Scope를 정의하고 PR 단위로 작업을 분리

---

## LEED Green Building Cost Predictor

**Machine Learning Project | ML · Data Developer**

**Tech Stack:** Python, Pandas, NumPy, scikit-learn, Streamlit, Matplotlib

건축 프로젝트의 LEED 점수, 비용과 등급을 예측하고 결과를 대시보드로 제공하는 머신러닝 애플리케이션입니다.

### 주요 구현

- 원천 데이터를 Pandas로 정제하고 모델 입력 데이터셋 구축
- 점수 및 비용 예측 회귀 모델과 등급 분류 모델 구현
- Linear Regression 및 Logistic Regression 기반 baseline 구축
- 클래스 불균형을 고려한 분류 모델 개선
- 예측 결과와 feature importance, confusion matrix 시각화
- Streamlit 기반 사용자 입력·예측 인터페이스 구현
- 실험 결과를 CSV 및 Excel 보고서로 출력

### 성과

- 점수 예측 MAE 약 38.2% 개선
- 비용 예측 MAE 약 79.0% 개선
- 등급 분류 Macro F1 약 20.6%p 개선
- 비용·점수·등급 모델의 성능과 한계를 각각 분리해 분석

---

## EDUCATION

### George Brown College

**Architectural Technician Diploma (T132)**

Toronto, Canada · 2023

- Building science, building systems, construction materials와 architectural drawing 교육 이수
- Sustainable design, energy-efficient design, green building 및 LEED 도메인 학습
- 건축 도메인 경험을 기반으로 반복적인 분석 업무를 데이터·AI 시스템으로 전환하는 프로젝트 수행

---

## CERTIFICATIONS & TRAINING

- **Microsoft AI School 8기 수료** — AI·데이터 기반 팀 프로젝트 수행
- **Microsoft Certified: Azure Fundamentals (AZ-900)**
- **Naver Boostcamp AI Tech Pre-Course 수료**