# JobOps Radar

[English README](README.md)

## 프로젝트 한눈에 보기

JobOps Radar는 실제 채용공고를 저장하고, JD 요구 역량을 구조화하여 지원자의
경험과 비교하고, 설명 가능한 역량 차이와 준비 로드맵을 제공하는 FastAPI
백엔드 프로젝트입니다.

현재는 채용공고 저장 API와 데이터베이스 기반을 구현한 단계입니다. JD 분석,
지원자 프로필, Auth/OIDC, LLM 연동은 아직 구현하지 않았으며 로드맵에서
명확하게 분리하고 있습니다.

첫 사례 연구는 Carrot Identity Service Backend 공고입니다. 이 공고에서
도출한 OIDC, B2B 조직 계정, 보안·개인정보, 고가용성, 인증 UX 요구사항을
향후 도메인 설계와 학습 로드맵의 근거로 사용합니다.

## 만들게 된 이유

채용공고에는 단순 기술 키워드뿐 아니라 팀이 중요하게 보는 시스템 특성,
보안 기준, 운영 책임과 협업 방식이 포함되어 있습니다. 하지만 링크나
메모로만 저장하면 다음 질문에 일관되게 답하기 어렵습니다.

- 이 공고가 실제로 요구하는 역량은 무엇인가?
- 내가 이미 증명할 수 있는 역량은 무엇인가?
- 부족한 것은 지식인지, 구현 경험인지, 운영 근거인지?
- 제한된 준비 시간을 어떤 순서로 사용해야 하는가?

JobOps Radar는 공고 원문, 구조화된 요구사항, 지원자 근거, 비교 결과를
분리해 저장하고 최종 결과가 왜 나왔는지 설명할 수 있도록 만드는 것을
목표로 합니다.

## 현재 구현 상태

| 영역 | 상태 | 구현 내용 |
| --- | --- | --- |
| API 기반 | 완료 | FastAPI 앱, `/health`, OpenAPI, Swagger UI |
| 채용공고 저장 | 완료 | SQLAlchemy `JobPosting`, 생성 및 단건 조회 |
| 중복 방지 | 완료 | `(source, external_id)` DB unique constraint |
| 목록 조회 | 완료 | bounded limit/offset 페이지네이션 |
| 정렬 안정성 | 완료 | `created_at DESC, id DESC` 결정적 정렬 |
| 스키마 변경 | 완료 | Alembic 초기 migration |
| 테스트 | 완료 | 서비스·라우트·모델·스키마·설정·DB 테스트 |
| CI | 완료 | GitHub Actions 테스트, migration, compile 검증 |
| JD 요구사항 분석 | 미구현 | 다음 구현 단계 |
| 지원자 프로필/비교 | 미구현 | 후속 단계 |
| Auth/OIDC/AuditLog | 미구현 | Carrot 사례 기반 미래 확장 |
| LLM/AWS 배포 | 미구현 | 현재 범위 밖 |

현재 기능과 미래 계획을 구분하는 이유는 구현하지 않은 기능을 포트폴리오
성과처럼 과장하지 않고, 각 기능의 도입 근거와 검증 수준을 명확히 설명하기
위해서입니다.

## 현재 구조

```text
HTTP request
    ↓
FastAPI route / validation
    ↓
JobPosting service
    ↓
SQLAlchemy session
    ↓
SQLite(local) / PostgreSQL(target)
```

- 라우트는 HTTP 입력 검증과 응답 변환을 담당합니다.
- 서비스는 조회 쿼리와 transaction 동작을 담당합니다.
- 데이터베이스는 중복 방지 같은 최종 불변조건을 보장합니다.
- Alembic은 데이터베이스 스키마 변경 이력을 관리합니다.

## 기술 스택

- Python 3.11+
- FastAPI
- Pydantic, `pydantic-settings`
- SQLAlchemy 2.0
- Alembic
- SQLite: 가벼운 로컬 개발 환경
- PostgreSQL: 목표 운영 데이터베이스
- pytest, FastAPI `TestClient`
- GitHub Actions

## API

| Method | Path | 설명 |
| --- | --- | --- |
| `GET` | `/health` | 애플리케이션 기본 상태 확인 |
| `POST` | `/job-postings` | 공고 생성 또는 기존 source identity 반환 |
| `GET` | `/job-postings` | 페이지네이션된 최신 공고 목록 |
| `GET` | `/job-postings/{job_posting_id}` | DB ID로 단건 조회 |
| `GET` | `/job-postings/by-source/{source}/{external_id}` | 외부 source identity로 조회 |
| `GET` | `/docs` | Swagger UI |

목록 조회의 기본값은 `limit=20&offset=0`입니다. `limit`은 1~100,
`offset`은 0 이상만 허용합니다.

정렬은 `created_at DESC, id DESC`입니다. 생성 시각이 같은 레코드가 있어도
고유한 `id`를 두 번째 기준으로 사용하므로, 데이터가 변경되지 않은 상태에서
페이지 순서가 결정적으로 유지됩니다.

## 로컬 실행

가상환경을 생성하고 활성화합니다.

```powershell
python -m venv .venv
.\.venv\Scripts\Activate.ps1
```

프로젝트와 개발 의존성을 설치합니다.

```powershell
python -m pip install --upgrade pip
pip install -e ".[dev]"
```

환경 파일을 만들고 migration을 적용합니다.

```powershell
Copy-Item .env.example .env
python -m alembic upgrade head
```

서버를 실행합니다.

```powershell
python -m uvicorn app.main:app --reload
```

- API 문서: <http://127.0.0.1:8000/docs>
- Health check: <http://127.0.0.1:8000/health>

macOS/Linux에서는 가상환경 활성화에 `source .venv/bin/activate`,
환경 파일 복사에 `cp .env.example .env`를 사용합니다.

## 환경 변수

| 변수 | 용도 | 현재 상태 |
| --- | --- | --- |
| `APP_NAME`, `APP_VERSION` | FastAPI 메타데이터 | 사용 중 |
| `APP_ENV`, `DEBUG` | 실행 환경 설정 | 설정만 존재 |
| `DATABASE_URL` | SQLAlchemy 연결 주소 | 사용 중 |
| `JWT_SECRET_KEY`, `JWT_ALGORITHM` | 미래 Auth 설정 | placeholder |
| `ACCESS_TOKEN_EXPIRE_MINUTES` | 미래 token 만료 설정 | placeholder |
| `SARAMIN_ACCESS_KEY`, `SARAMIN_API_BASE_URL` | 미래 채용공고 연동 | 미구현 |
| `LLM_API_KEY`, `LLM_MOCK_MODE` | 미래 LLM 연동 | 미구현 |

`.env.example`을 복사해 `.env`로 사용합니다. 실제 secret이 포함된 `.env`와
로컬 `jobops.db`는 Git에 커밋하지 않습니다.

## 테스트와 CI

로컬 검증 명령:

```powershell
python -m pytest -q -p no:cacheprovider
python -m compileall -q app tests alembic
python -m alembic current
```

GitHub Actions는 `main`과 `dev` 대상 push 및 pull request에서 실행됩니다.
CI도 로컬과 동일하게 다음 명령으로 의존성을 설치합니다.

```powershell
pip install -e ".[dev]"
```

`pyproject.toml`을 의존성의 단일 기준으로 사용하므로 로컬과 CI의 패키지
목록이 서로 달라지는 문제를 줄입니다.

## Carrot Identity Service 사례 연구

[Carrot Identity Service Backend 사례 문서](docs/job-analysis/carrot-identity-backend.md)는
다음 요구사항을 프로젝트 로드맵과 연결합니다.

- Identity/Auth 공통 플랫폼 백엔드
- OIDC 기반 로그인 플랫폼
- 사용자·조직·멤버십·역할을 구분하는 B2B 계정 모델
- 개인정보 최소화, token/secret 보호, 보안 이벤트 추적
- 인증 플랫폼의 고가용성과 예측 가능한 장애 처리
- 안전하면서 이해하기 쉬운 로그인·복구 UX
- 검토 가능성을 전제로 한 AI-assisted engineering workflow

이 문서는 Auth나 OIDC가 구현되었다는 의미가 아닙니다. 향후 기능을 추가할
때 “왜 필요한가”를 설명하는 요구사항 근거입니다.

## 로드맵

1. 실제 채용공고 저장과 사례 문서화
2. 수동으로 검토한 구조화 JD 요구사항 모델·migration·service 구현
3. 지원자 프로필과 경험 근거 모델 구현
4. 결정적이고 설명 가능한 skill-gap 비교
5. 준비 우선순위와 학습 로드맵 생성
6. Carrot 사례에 근거한 B2B 조직 계정·보안·AuditLog 설계
7. 위협 모델과 protocol 경계를 문서화한 후 Auth/OIDC 구현
8. PostgreSQL 운영 검증과 고가용성 설계 후 AWS 배포 검토
9. 검토 가능한 보조 계층으로 LLM 도입 여부 평가

다음 PR은 LLM 없이 수동으로 구조화한 JD 요구사항을 저장하는 최소 모델,
Alembic migration, Pydantic schema, service와 테스트를 추가하는 단계입니다.

## 면접에서 설명할 핵심

- 기능 수보다 데이터 불변조건, 경계 분리, 검증 가능한 동작을 우선했습니다.
- 중복 방지는 애플리케이션 pre-check뿐 아니라 DB unique constraint로
  보장합니다.
- 페이지네이션은 응답 크기를 제한하고 unique tie-breaker로 순서를
  결정적으로 만듭니다.
- CI와 로컬은 `pyproject.toml`의 동일한 dependency definition을 사용합니다.
- SQLite는 현재 개발 편의용이며 PostgreSQL이 목표 운영 DB입니다.
- Carrot 사례는 Auth 기능을 성급히 추가하기 위한 명분이 아니라, 요구사항과
  설계 근거를 연결하기 위한 첫 분석 데이터입니다.
- 구현하지 않은 Auth/OIDC/LLM/AWS 기능은 명시적으로 미구현 상태로
  표시했습니다.

아키텍처 결정은 [ADR](docs/adr/README.md), 현재 개발 상태와 다음 작업은
[handoff 문서](handoff.md)에서 확인할 수 있습니다.
