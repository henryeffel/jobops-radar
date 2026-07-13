# JobOps Radar

JobOps Radar는 비정형 채용공고를 구조화된 요구사항과 검토 가능한 준비 계획으로 바꾸는 FastAPI 백엔드입니다. 이 저장소는 공고 분석 도메인과 의도적으로 범위를 좁힌 내부 인증 기능을 함께 보여줍니다.

## 1. 문제

채용 요구사항은 자유 형식의 텍스트에 흩어져 있어 지원자가 요구 역량, 자신의 근거, 역량 차이를 체계적으로 비교하기 어렵습니다. 외부 채용 API 승인이 필요한 경우에는 제품 검증 자체가 지연될 수도 있습니다.

## 2. 해결 방법

공급자에 종속되지 않는 형태로 채용공고와 구조화된 요구사항을 저장합니다. 외부 승인 없이도 개발과 테스트를 이어갈 수 있도록 수동 fixture adapter를 사용합니다. 내부 인증 모듈은 회원가입부터 로그인, 현재 사용자 조회, 보안 감사 이벤트까지 하나의 작은 흐름을 완결합니다.

## 3. 현재 구현 범위

- `JobPosting` 저장·조회·페이지네이션과 `(source, external_id)` 기준 중복 방지
- `JobRequirement` 관계 모델과 1~5 범위의 중요도 검증
- 수동 fixture provider와 아직 구현하지 않은 Saramin provider의 격리된 경계
- `POST /auth/register`, `POST /auth/login`, `GET /users/me`
- Argon2 비밀번호 해싱과 수명이 짧은 PyJWT access token
- `USER_REGISTERED`, `LOGIN_SUCCESS`, `LOGIN_FAILURE` 감사 이벤트
- Karrot Identity Service 사례 연구와 인증 시스템 설계 문서

## 4. 아키텍처

현재 구조는 모듈러 모놀리스입니다. 하나의 배포 단위와 데이터베이스를 사용하되 채용공고, 인증, 감사 로그, 외부 연동의 경계를 명시적으로 나눴습니다. 이는 단일 개발자·낮은 현재 트래픽·도메인 검증 단계에 적합하며, 향후 소유권이나 확장 조건이 달라질 때 분리할 지점도 남깁니다.

[시스템 구조도](docs/architecture/system-overview.md)에서 전체 흐름을 확인할 수 있습니다.

## 5. 핵심 결정

- Saramin API 승인이 제품 검증을 막지 않도록 fixture/manual adapter를 사용합니다.
- 분산 운영 비용이 현재 가치보다 크므로 모듈러 모놀리스를 선택합니다.
- 내부 access token에만 PyJWT를 사용하고 비밀번호는 Argon2로 저장합니다.
- 안전성과 표준 준수를 증명할 수 없는 부분적인 OIDC Provider는 구현하지 않습니다.

관련 문서: [ADR 목록](docs/adr/README.md), [모듈러 모놀리스](docs/adr/0009-modular-monolith-over-microservices.md), [외부 API 분리](docs/adr/0010-decouple-saramin-api.md), [내부 JWT](docs/adr/0011-pyjwt-for-internal-auth.md), [OIDC 범위 제한](docs/adr/0012-limit-oidc-scope.md)

## 6. 검증

```powershell
python -m pip install -e ".[dev]"
python -m pytest -q -p no:cacheprovider
python -m alembic upgrade head
python -m alembic check
python -m compileall -q app tests alembic
```

테스트는 회원가입, 중복 이메일 거부, 평문 비밀번호 미저장, 정상·비정상 로그인, 계정 존재 여부를 숨기는 동일한 오류 응답, 정상·변조·만료 JWT, 현재 사용자 조회, 감사 이벤트 기록, 감사 데이터의 비밀번호·토큰 제외를 검증합니다. 기존 공고 및 요구사항 테스트도 같은 전체 테스트 묶음에 포함됩니다.

## 7. 한계

- 실제 운영 트래픽, 고가용성, 확장성을 검증하지 않았습니다.
- OIDC/OAuth Provider가 아니며 외부 연합 로그인도 제공하지 않습니다.
- Refresh token rotation, 로그아웃·폐기, MFA, 비밀번호 재설정, rate limiting은 구현하지 않았습니다.
- HS256은 하나의 공유 비밀 키를 사용하며 운영 환경의 키 관리·교체는 구현하지 않았습니다.
- Saramin 연동은 승인 대기 상태이며 fixture 데이터는 수동으로 관리합니다.

## 8. 로컬 실행

`.env.example`을 `.env`로 복사한 뒤 의존성을 설치하고 migration을 적용합니다. 예제 설정은 SQLite를 사용하며 `docker-compose.yml`을 통해 PostgreSQL도 실행할 수 있습니다.

```powershell
Copy-Item .env.example .env
python -m alembic upgrade head
python -m uvicorn app.main:app --reload
```

Swagger UI는 <http://127.0.0.1:8000/docs>, 상태 확인 API는 <http://127.0.0.1:8000/health>에서 확인합니다.

## 9. 산출물 안내

- [아키텍처](docs/architecture/system-overview.md)
- [Karrot 사례 연구](docs/case-studies/karrot-identity-service.md)
- [인증 시스템 설계](docs/identity/auth-system-design.md)
- [리스크 목록](docs/project/risk-register.md)
- [AI 협업 개발](docs/ai-assisted-development.md)
- [인증 테스트](tests/identity/test_auth_flow.py)

## 10. 로드맵

1. 요구사항 하위 API와 결정론적인 역량 차이 비교 기능을 추가합니다.
2. 공개 배포 전에 rate limiting과 운영 환경의 비밀 키 관리 방식을 추가합니다.
3. Rotation, 재사용 탐지, 폐기 테스트를 함께 설계할 수 있을 때만 refresh token을 도입합니다.
4. 공식 API 승인과 응답 계약 fixture가 준비된 뒤 Saramin adapter를 구현합니다.
5. ADR에 기록한 전환 조건이 발생했을 때만 서비스 분리를 다시 검토합니다.
