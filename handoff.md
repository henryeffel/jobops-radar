# 작업 인계

## 현재 상태

- 프로젝트의 기준 설명은 한국어 [README](README.md)입니다.
- FastAPI는 `GET /health/live`, DB readiness를 확인하는 `GET /health/ready`, 호환용 `GET /health`, JobPosting API, `POST /auth/register`, `POST /auth/login`, `GET /users/me`, 사용자 프로필 API를 제공합니다.
- 모든 HTTP 요청에는 검증된 외부 값 또는 서버 생성 UUID 기반 `X-Request-ID`가 부여되고 응답 header와 JSON 완료 로그에 포함됩니다. 로그에는 query string, request body, credential을 포함하지 않습니다.
- `JobPosting`은 공급자에 중립적인 공고를 저장하고 `(source, external_id)` unique constraint로 중복을 방지합니다.
- `GET /job-postings`는 `company_name` 정확 일치, `is_active` filter와 `sort=created_at|expiration_date`를 지원합니다. 기본값은 `limit=20&offset=0`, `created_at DESC, id DESC`이며 마감일 정렬은 오름차순, `NULL` 마지막, `id DESC` tie-break를 사용합니다.
- `JobRequirement`는 공고에 연결된 구조화 요구사항을 저장하고 중요도 1~5를 application과 DB에서 검증합니다. Requirement API route는 아직 없습니다.
- `create_job_posting_with_requirements`는 공고와 요구사항 묶음을 flush한 뒤 한 번만 commit하며, constraint 또는 중간 처리 오류 시 전체 rollback합니다. 이 기능은 현재 service 경계이며 별도 HTTP route는 없습니다.
- PostgreSQL query plan용 script는 실제 공고 목록 service statement를 공유하며 5만 건 seed, `EXPLAIN (ANALYZE, BUFFERS, FORMAT JSON)`과 전용 row cleanup을 제공합니다. PostgreSQL이 아니면 실행을 거부합니다.
- Identity module은 이메일을 정규화하고 Argon2로 비밀번호를 해싱하며 PyJWT access token을 발급합니다.
- 인증된 사용자는 `PUT /users/me/profile`에 Markdown 이력서를 저장·갱신하고 `GET /users/me/profile`로 조회할 수 있습니다. 프로필은 요약, 기술, 프로젝트, 교육, 자격 항목으로 결정론적으로 구조화되며 사용자별로 격리됩니다.
- `DELETE /users/me/profile`은 현재 사용자의 이력서 원문과 구조화 프로필을 삭제합니다. 삭제 후 조회는 404, 분석은 409입니다.
- `POST /job-analyses`는 공개 채용공고 URL 또는 직접 전달한 HTML·본문을 추출해 사용자 프로필과 비교하고, 가중 적합도, 근거, 일치·부족 기술과 준비 계획을 반환합니다. URL fetch에는 SSRF 방어와 redirect·크기·timeout 제한이 적용됩니다.
- `LLM_MOCK_MODE=false`에서는 NVIDIA OpenAI-compatible endpoint를 통해 구조화된 요구사항을 추출합니다. 공고와 이력서는 section ID JSON으로 전달되며 존재하지 않는 evidence ID는 거부합니다. 실패 시 결정론적 분석으로 fallback합니다. `llm_api.py` import에는 네트워크 부작용이 없습니다.
- 외부 LLM은 요청의 `consent_to_external_llm=true`일 때만 사용하며, fallback 응답에는 안정적인 `fallback_reason`을 포함합니다. LLM 동시성은 프로세스당 기본 2개로 제한됩니다.
- 알 수 없는 이메일과 잘못된 비밀번호는 같은 401 응답을 사용합니다.
- Audit module은 `USER_REGISTERED`, `LOGIN_SUCCESS`, `LOGIN_FAILURE`를 기록하며 비밀번호·token·raw request는 저장하지 않습니다.
- Fixture provider로 외부 API 승인과 개발을 분리했습니다. Saramin provider는 경계만 있고 구현되지 않았습니다.
- SQLAlchemy 2.0과 Alembic을 사용하며 SQLite를 로컬 fallback, PostgreSQL을 운영 목표로 둡니다.
- 현재 migration은 `job_postings`, `job_requirements`, `users`, `user_profiles`, `audit_logs`를 생성합니다.
- 아키텍처, ADR, Karrot 사례 연구, 인증 설계, risk register, AI 협업 문서는 `docs/`에 있습니다.

## 검증 상태

- `python -m pytest -q -p no:cacheprovider`: 103개 test 통과
- 공고·요구사항 묶음의 정상 commit, check·unique constraint 실패, 예상치 못한 중간 flush 오류의 전체 rollback과 rollback 후 session 재사용을 검증했습니다.
- 현재 개발 환경에는 Docker, PostgreSQL server와 `psql`이 없어 PostgreSQL migration과 실제 query plan은 아직 검증하지 못했습니다. SQLite 결과를 PostgreSQL 성능 근거로 사용하지 않습니다.
- DB 정상·장애 상태의 liveness와 readiness 분리, 장애 응답·로그의 credential 및 내부 예외 비노출을 검증했습니다.
- 빈 SQLite DB에서 `python -m alembic upgrade head`: 통과
- `python -m alembic check`: model drift 없음
- `python -m compileall -q app tests alembic`: 통과
- 남은 warning은 FastAPI/Starlette TestClient의 upstream deprecation 1건입니다.
- 실제 `resume_sample.md`와 Karrot 분석 문서를 사용한 NVIDIA 호출이 17.1초에 LLM 경로로 성공해 16개 요구사항과 서버 계산 점수를 반환했습니다. 이전 호출에서는 `503 ResourceExhausted`, schema 오류와 timeout도 관찰됐으므로 안전한 fallback은 계속 유지합니다.
- 실제 HTTP API end-to-end 호출도 20.2초에 LLM 경로로 성공했습니다. 가입→로그인→프로필 등록→명시적 동의 분석→프로필 삭제가 완료됐고, 요구사항 20개, matched 13개, missing 7개, warning 0개를 반환했습니다.
- 공개 Greenhouse 채용공고 URL 3개의 fetch를 검증했고 모두 text document 추출에 성공했습니다. 그중 한 URL은 가입→프로필→URL 분석 API 여정에서 200 응답, 본문 11,844자와 요구사항 9개를 반환했습니다.

## 로컬 실행

```powershell
python -m venv .venv
.\.venv\Scripts\Activate.ps1
python -m pip install -e ".[dev]"
Copy-Item .env.example .env
python -m alembic upgrade head
python -m uvicorn app.main:app --reload
```

실제 비밀 키가 담긴 `.env`는 commit하지 않습니다. PostgreSQL은 Docker 대신 기존 Ubuntu EC2에서 우선 검증하기로 했습니다. EC2 SSH key와 host 정보도 저장소에 기록하거나 commit하지 않습니다.

## 명시적인 비목표

- 완전한 OIDC/OAuth Provider
- Refresh token rotation, logout/revocation, MFA, password reset
- 대규모 traffic 또는 고가용성 주장
- Production Kubernetes·Microservices 배포
- 승인 전 Saramin 자동 수집 또는 scraping

## 다음 권장 작업

1. AWS 콘솔에서 기존 EC2의 실행 상태, 현재 public IPv4와 SSH Security Group을 확인합니다.
2. SSH가 복구되면 EC2 OS·자원·서비스를 읽기 전용 점검한 뒤 PostgreSQL 설치 여부를 결정합니다.
3. PostgreSQL migration, 5만 건 seed와 index 적용 전 `EXPLAIN ANALYZE`를 실행합니다.
4. baseline 근거가 있을 때만 index migration과 적용 후 비교를 진행합니다.
5. 이후 systemd·Nginx 배포 파일과 Linux 장애 runbook을 완성합니다.

## 세션 기록 규칙

향후 작업 후에는 실제 작업일의 `docs/session-logs/YYYY-MM-DD.md`와 이 문서를 갱신합니다. Session entry에는 목표, 실제 변경, 파일, 검증 명령과 결과, 관련 개념, 설계 결정, 문제·경고, 다음 작은 작업을 기록합니다. 중요한 아키텍처 결정이 바뀌면 기존 ADR을 조용히 수정하지 않고 새 ADR로 대체합니다.
