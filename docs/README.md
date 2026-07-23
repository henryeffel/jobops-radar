# JobOps Radar 문서 안내

이 디렉터리는 현재 제품 상태, API 사용법, 설계 결정, 실험 결과와 역사 기록을 목적별로 분리합니다. 현재 사실은 루트 `README.md`, `handoff.md`와 아래의 MVP 상태 문서를 우선합니다. 날짜가 있는 session·daily log는 당시 상태를 보존한 snapshot입니다.

## 제품과 사용법

- [운영 배포 현황](operations/production-deployment.md): 공개 도메인, EC2·Nginx·PostgreSQL·HTTPS 구성, 검증과 운영 과제
- [1차 통합 MVP 후기 및 개선 방향](project/first-integrated-mvp-retrospective.md): 초기 제품 의도, 현재 한계, 지원 판단·로드맵·지원 산출물·GitHub 연동 방향
- [지원 의사결정부터 지원 관리까지의 제품 로드맵](project/decision-to-application-roadmap.md): Decision, Assets, Tracking, Comparison 단계와 완료 조건
- [Linux 운영과 관계형 DB 기본기 개발 계획](project/linux-operations-and-relational-db-development.md): health check, 운영 로그, systemd·Nginx, 쿼리·인덱스·트랜잭션과 2026-07-22 작업 상태
- [PostgreSQL 공고 조회 실행 계획 실험](experiments/postgresql-query-plan.md): 실제 API query, 5만 건 seed·EXPLAIN 도구, 환경 blocker와 측정 절차

- [프론트엔드 MVP 계획](frontend/mvp-plan.md): 화면 범위, UX 상태와 완료 조건
- [Swagger 백엔드 MVP 상태](project/mvp-status.md): 완료 조건, 검증 근거, 남은 범위
- [MVP API 사용 가이드](api/mvp-api-guide.md): 가입부터 분석·삭제까지 실행 순서
- [시스템 구조](architecture/system-overview.md): 모듈과 데이터 흐름
- [리스크 목록](project/risk-register.md): 현재 위험과 대응 상태

## 데이터와 보안

- [사용자 데이터 처리 범위](privacy/data-handling.md): 저장, 외부 전송, 삭제와 로그 정책
- [인증 시스템 설계](identity/auth-system-design.md): 비밀번호, JWT, 인증 경계
- [비밀번호 검증 동시성 실험](experiments/auth-login-baseline.md): 부하 문제와 완화 근거

## 채용공고와 LLM 분석

- [LLM 구조화 분석 오류 개선 기록](experiments/llm-structured-analysis-troubleshooting.md): 실패 분류, evidence ID 전환과 실제 성공 과정
- [Karrot Identity Backend 분석](job-analysis/carrot-identity-backend.md): 공고 도메인 해석
- [Karrot Identity Service 사례 연구](case-studies/karrot-identity-service.md): 인증 도메인 설계 사례
- [AI 협업 개발](ai-assisted-development.md): AI 사용 범위와 검증 원칙

## 설계 결정

- [ADR 목록](adr/README.md): FastAPI, DB, 모듈러 모놀리스, 인증, 사용자 제공 공고와 LLM fallback 결정

승인된 결정을 바꿀 때는 기존 ADR을 조용히 다시 쓰지 않고 새 ADR에서 대체 관계를 기록합니다.

## 작업 기록

- [2026-07-21 세션 로그](session-logs/2026-07-21.md): 프로필·공고 분석·LLM·MVP 완료 작업
- [2026-07-22 세션 로그](session-logs/2026-07-22.md): health, request tracing, 공고 query, transaction과 PostgreSQL 측정 준비
- [2026-07-23 세션 로그](session-logs/2026-07-23.md): PostgreSQL 전환, query plan, EC2·Nginx·도메인·HTTPS 배포
- `session-logs/`, `daily-logs/`: 날짜별 historical snapshot
- [과거 작업 요약](work-summary.md): Identity/Auth 구현 전 누적 상태

## 학습과 인터뷰 준비

- `learning-notes/`: 구현에서 사용한 backend·CS 개념
- `interview-prep/`: 프로젝트 설명과 예상 질문

## 문서 갱신 원칙

1. 현재 기능이 바뀌면 `README.md`, `handoff.md`, MVP 상태와 API 가이드를 함께 확인합니다.
2. 실제 검증 결과는 해당 날짜의 session log에 명령과 결과를 기록합니다.
3. provider 실험 수치는 성공과 실패를 모두 남기며 제품 성능 지표처럼 표현하지 않습니다.
4. API key, token, 이력서 원문 전체와 LLM reasoning은 문서에 기록하지 않습니다.
