# 작업 인계

## 현재 상태

- 프로젝트의 기준 설명은 한국어 [README](README.md)입니다.
- FastAPI는 `GET /health`, JobPosting API, `POST /auth/register`, `POST /auth/login`, `GET /users/me`를 제공합니다.
- `JobPosting`은 공급자에 중립적인 공고를 저장하고 `(source, external_id)` unique constraint로 중복을 방지합니다.
- `GET /job-postings`는 `limit=20&offset=0`을 기본값으로 사용하며 `created_at DESC, id DESC`로 정렬합니다.
- `JobRequirement`는 공고에 연결된 구조화 요구사항을 저장하고 중요도 1~5를 application과 DB에서 검증합니다. Requirement API route는 아직 없습니다.
- Identity module은 이메일을 정규화하고 Argon2로 비밀번호를 해싱하며 PyJWT access token을 발급합니다.
- 알 수 없는 이메일과 잘못된 비밀번호는 같은 401 응답을 사용합니다.
- Audit module은 `USER_REGISTERED`, `LOGIN_SUCCESS`, `LOGIN_FAILURE`를 기록하며 비밀번호·token·raw request는 저장하지 않습니다.
- Fixture provider로 외부 API 승인과 개발을 분리했습니다. Saramin provider는 경계만 있고 구현되지 않았습니다.
- SQLAlchemy 2.0과 Alembic을 사용하며 SQLite를 로컬 fallback, PostgreSQL을 운영 목표로 둡니다.
- 현재 migration은 `job_postings`, `job_requirements`, `users`, `audit_logs`를 생성합니다.
- 아키텍처, ADR, Karrot 사례 연구, 인증 설계, risk register, AI 협업 문서는 `docs/`에 있습니다.

## 검증 상태

- `python -m pytest -q -p no:cacheprovider`: 47개 test 통과
- 빈 SQLite DB에서 `python -m alembic upgrade head`: 통과
- `python -m alembic check`: model drift 없음
- `python -m compileall -q app tests alembic`: 통과
- 남은 warning은 FastAPI/Starlette TestClient의 upstream deprecation 1건입니다.

## 로컬 실행

```powershell
python -m venv .venv
.\.venv\Scripts\Activate.ps1
python -m pip install -e ".[dev]"
Copy-Item .env.example .env
python -m alembic upgrade head
python -m uvicorn app.main:app --reload
```

실제 비밀 키가 담긴 `.env`는 commit하지 않습니다. Docker Desktop 설치 후 PostgreSQL을 사용할 때는 `docker compose up -d`를 실행하고 `.env`의 `DATABASE_URL`을 변경한 뒤 migration을 다시 적용합니다.

## 명시적인 비목표

- 완전한 OIDC/OAuth Provider
- Refresh token rotation, logout/revocation, MFA, password reset
- 대규모 traffic 또는 고가용성 주장
- Production Kubernetes·Microservices 배포
- 승인 전 Saramin 자동 수집 또는 scraping

## 다음 권장 작업

1. 남아 있는 과거 영문 문서를 한국어화하고 오래된 상태 표현에는 시점 표시를 추가합니다.
2. Identity test를 register/login/current-user/password/audit 목적별 파일로 분리합니다.
3. Fixture를 읽어 JobPosting으로 저장하고 재입력 시 중복 row가 생기지 않는 통합 흐름을 구현합니다.
4. 검증된 service를 이용해 작은 nested JobRequirement 생성·목록 API를 추가합니다.

## 세션 기록 규칙

향후 작업 후에는 실제 작업일의 `docs/session-logs/YYYY-MM-DD.md`와 이 문서를 갱신합니다. Session entry에는 목표, 실제 변경, 파일, 검증 명령과 결과, 관련 개념, 설계 결정, 문제·경고, 다음 작은 작업을 기록합니다. 중요한 아키텍처 결정이 바뀌면 기존 ADR을 조용히 수정하지 않고 새 ADR로 대체합니다.
