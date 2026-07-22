# Swagger 기반 백엔드 MVP 상태

## 현재 판정

**완료 — Swagger 기반 backend MVP**

이 판정은 제품의 핵심 backend 흐름을 API 문서 화면에서 실행할 수 있다는 의미입니다. 일반 사용자를 위한 별도 웹 UI나 production 운영 준비가 완료됐다는 뜻은 아닙니다.

## 해결하려는 문제

사용자가 관심 있는 채용공고와 자신의 이력서를 비교하려면 자유 형식 문서에서 요구사항과 근거를 직접 찾아야 합니다. JobOps Radar는 공고 URL 또는 본문과 Markdown 이력서를 구조화하고, 일치·부족 역량과 준비 계획을 설명 가능한 근거와 함께 반환합니다.

## 완료된 핵심 여정

```text
회원가입·로그인
  → Markdown 이력서 저장
  → 공개 채용공고 URL 또는 본문 입력
  → HTML·문서 section 추출
  → LLM evidence-ID 분석 또는 결정론적 fallback
  → 서버 점수·근거·준비 계획 반환
  → 이력서 삭제
```

## 완료된 범위

| 영역 | 상태 | 구현 근거 |
| --- | --- | --- |
| 인증 | 완료 | register, login, current user, Argon2, JWT |
| 보안 감사 | 완료 | 가입·로그인 성공·실패 이벤트, credential 제외 |
| 사용자 프로필 | 완료 | Markdown 저장·구조화·조회·교체·삭제 |
| 공고 입력 | 완료 | 공개 URL fetch와 HTML·본문 fallback |
| URL 안전성 | MVP 완료 | SSRF 기본 방어, redirect·크기·시간 제한 |
| LLM 분석 | MVP 완료 | section JSON, evidence ID 검증, 실제 전체 이력서 성공 |
| 장애 복구 | 완료 | reason code와 결정론적 fallback |
| LLM 자원 제한 | 완료 | 50초 provider timeout, 무재시도, 프로세스당 동시 2개 |
| 외부 전송 동의 | 완료 | 요청별 explicit opt-in, 기본 false |
| DB migration | 완료 | users, profiles, postings, requirements, audit logs |
| 테스트 | 완료 | 103개 pytest 및 전체 사용자 여정 |
| 문서 | 완료 | API, architecture, ADR, privacy, risk, experiment, session log |

## 실제 검증 근거

- `resume_sample.md`와 Karrot 분석 문서의 실제 NVIDIA 호출이 17.1초에 성공했습니다.
- LLM은 16개 요구사항을 반환했고 evidence ID 검증을 통과했습니다.
- 이전 실험에서 503, schema 오류와 timeout도 관찰했으며 fallback을 유지했습니다.
- 공개 Greenhouse 채용공고 URL 3개에서 text document를 추출했습니다.
- 실제 URL API 여정에서 가입 `201`, 프로필 `200`, 분석 `200`을 확인했습니다.
- 해당 URL 분석은 본문 11,844자와 결정론적 요구사항 9개를 반환했습니다.
- 실제 HTTP API end-to-end LLM 여정에서 가입, `resume_sample.md` 등록, 명시적 LLM 동의 분석과 프로필 삭제를 검증했습니다.
- LLM API 분석은 20.2초에 성공해 `analysis_method=llm`, `fallback_reason=null`, 요구사항 20개, matched 13개, missing 7개와 warning 0개를 반환했습니다.
- 동일 여정을 sandbox outbound 제한 안에서 실행했을 때는 `provider_request_failed` fallback이 정상 반환됐고, 네트워크 허용 서버에서 LLM 성공 경로를 확인했습니다.
- `python -m pytest -q -p no:cacheprovider`: 103 passed.
- 빈 SQLite DB의 Alembic upgrade와 model drift check가 통과했습니다.
- `python -m compileall -q app tests alembic`: passed.

실험 점수는 규칙 보정과 공고 품질에 따라 달라지므로 제품 정확도 또는 후보자 능력의 절대 지표로 해석하지 않습니다.

## 완료 조건과 결과

| 완료 조건 | 결과 |
| --- | --- |
| 새 사용자 가입·로그인 | 충족 |
| 이력서 등록과 사용자별 격리 | 충족 |
| 실제 공개 URL 입력 | 충족 |
| LLM 또는 fallback 분석 결과 | 충족 |
| 약 1분 내 종료 | 50초 provider timeout과 무재시도로 경계 설정 |
| 분석 방법·실패 원인 표시 | 충족 |
| 외부 LLM 전송 동의 | 충족 |
| 이력서 삭제 | 충족 |
| 전체 여정 자동 테스트 | 충족 |

## 현재 비목표

- 일반 사용자용 frontend
- 완전한 OIDC/OAuth provider
- refresh token, MFA, password reset
- 계정 전체 삭제
- 공식 Saramin API 연동과 대량 공고 수집
- 로그인·CAPTCHA·JavaScript 렌더링 우회
- Kubernetes·microservices production 배포
- 고가용성·대규모 traffic 주장

## MVP 이후 우선순위

1. [프론트엔드 MVP 계획](../frontend/mvp-plan.md)에 따라 로그인, 이력서 입력, URL 분석과 결과 화면을 제공합니다.
2. fallback reason과 latency를 structured log·metrics로 집계합니다.
3. PostgreSQL 환경에서 migration과 동시 요청을 검증합니다.
4. 계정 삭제, backup 보존 기간과 정식 개인정보 처리방침을 정의합니다.
5. 실제 다양한 공고를 이용해 요구사항 중복 제거와 결과 품질을 평가합니다.

## 관련 문서

- [API 사용 가이드](../api/mvp-api-guide.md)
- [시스템 구조](../architecture/system-overview.md)
- [사용자 데이터 처리](../privacy/data-handling.md)
- [LLM 오류 개선 기록](../experiments/llm-structured-analysis-troubleshooting.md)
- [ADR-0014](../adr/0014-user-supplied-job-input-and-validated-llm-fallback.md)
- [2026-07-21 세션 로그](../session-logs/2026-07-21.md)
