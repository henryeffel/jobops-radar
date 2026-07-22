# Swagger 백엔드 MVP API 가이드

## 목적

별도 frontend 없이 Swagger UI에서 JobOps Radar의 핵심 사용자 여정을 실행하는 방법을 설명합니다.

```text
회원가입 → 로그인 → 인증 설정 → 이력서 등록 → 공고 분석 → 이력서 삭제
```

## 실행

```powershell
python -m pip install -e ".[dev]"
Copy-Item .env.example .env
python -m alembic upgrade head
python -m uvicorn app.main:app --reload
```

- Swagger UI: <http://127.0.0.1:8000/docs>
- 프로세스 상태: <http://127.0.0.1:8000/health/live>
- DB 준비 상태: <http://127.0.0.1:8000/health/ready>
- 호환 endpoint: <http://127.0.0.1:8000/health>

`/health/live`는 FastAPI process가 요청에 응답할 수 있는지만 확인합니다. `/health/ready`는 `SELECT 1`로 DB 연결을 확인하며, DB 장애 시 내부 연결 정보 없이 `503`과 `{"status":"not_ready"}`를 반환합니다.

모든 HTTP 응답은 처리되지 않은 500 오류를 포함해 `X-Request-ID` header를 포함합니다. client가 영숫자와 `._-`로 구성된 1~128자의 값을 보내면 서버가 재사용하고, 값이 없거나 안전하지 않으면 UUID를 생성합니다. 서버 완료 로그에는 request ID, method, query string을 제외한 path, status code와 latency가 JSON으로 기록됩니다. 처리되지 않은 예외는 generic 500 응답으로 변환하며 stack frame과 exception type은 기록하되 예외 원문은 redaction합니다.

## 공고 목록 조회

`GET /job-postings`는 다음 query parameter를 지원합니다.

| parameter | 기본값 | 동작 |
| --- | --- | --- |
| `company_name` | 없음 | 회사명 정확 일치 |
| `is_active` | 없음 | `true` 또는 `false` filter |
| `sort` | `created_at` | `created_at` 또는 `expiration_date` |
| `limit` | `20` | 1~100 |
| `offset` | `0` | 0 이상 |

`created_at`은 최신 생성순과 `id` 역순으로 정렬합니다. `expiration_date`는 가까운 마감일 우선이며 마감일이 없는 공고는 마지막에 두고 `id` 역순으로 순서를 고정합니다. filter와 sort를 적용한 뒤 pagination합니다.

## 1. 회원가입

`POST /auth/register`

```json
{
  "email": "user@example.com",
  "password": "at-least-12-characters"
}
```

성공 시 `201`과 사용자 ID·이메일을 반환합니다. 이메일은 lowercase로 정규화되며 비밀번호는 Argon2 hash로만 저장됩니다.

## 2. 로그인과 Swagger 인증

`POST /auth/login`에 같은 계정 정보를 보내 access token을 받습니다.

```json
{
  "access_token": "<JWT>",
  "token_type": "bearer"
}
```

Swagger 상단의 `Authorize` 버튼을 누르고 token을 입력합니다. 이후 `/users/me`로 현재 사용자를 확인할 수 있습니다.

잘못된 이메일과 비밀번호는 계정 존재 여부를 노출하지 않도록 동일한 `401` 응답을 사용합니다. 비밀번호 검증 용량이 부족하면 `503`을 반환할 수 있습니다.

## 3. 사용자 프로필 등록

`PUT /users/me/profile`

```json
{
  "resume_markdown": "## SUMMARY\nPython backend developer\n\n## SKILLS\n- Python\n- FastAPI"
}
```

서버는 Markdown 원문과 다음 구조화 필드를 사용자별로 저장합니다.

- `summary`
- `skills`
- `projects`
- `education`
- `certifications`

`GET /users/me/profile`로 현재 프로필을 조회할 수 있습니다.

## 4. 채용공고 분석

`POST /job-analyses`

### 공개 URL 입력

```json
{
  "source_url": "https://public-job-board.example/jobs/123",
  "consent_to_external_llm": true
}
```

### 본문 fallback

사이트가 JavaScript, 로그인, CAPTCHA 또는 정책상 자동 fetch를 허용하지 않으면 HTML·본문을 직접 전달합니다.

```json
{
  "source_url": "https://public-job-board.example/jobs/123",
  "content": "## Required\nPython and FastAPI experience",
  "consent_to_external_llm": false
}
```

`content`가 있으면 URL fetch 대신 전달된 내용을 분석합니다.

### 외부 LLM 동의

`consent_to_external_llm`의 기본값은 `false`입니다.

- `true`: 설정이 활성화된 경우 공고·이력서 section JSON을 외부 LLM에 전송할 수 있습니다.
- `false`: 외부 전송 없이 결정론적 분석을 사용합니다.
- `LLM_MOCK_MODE=true`: 동의 여부와 관계없이 실제 LLM을 호출하지 않습니다.

### 주요 응답 필드

```json
{
  "analysis_method": "llm",
  "fallback_reason": null,
  "match_score": 61,
  "requirements": [],
  "matched_skills": [],
  "missing_skills": [],
  "action_plan": [],
  "warnings": []
}
```

- `analysis_method`: `llm` 또는 `deterministic`
- `fallback_reason`: fallback이 없으면 `null`, 있으면 안정적인 reason code
- `requirements`: 공고 근거, 프로필 근거, 필수 여부, 중요도와 매칭 결과
- `match_score`: 검증된 요구사항 중요도를 사용해 서버에서 계산
- `action_plan`: 부족한 항목을 위한 준비 작업

보정 전 실험에서 나온 특정 점수는 후보자 능력의 절대 평가가 아닙니다. 공고 추출 품질과 요구사항 분류를 함께 검토해야 합니다.

### Fallback reason

대표적인 값:

- `llm_mock_mode`
- `external_llm_consent_required`
- `llm_not_configured`
- `llm_capacity_exhausted`
- `provider_timeout`
- `provider_rate_limited`
- `provider_capacity_exhausted`
- `provider_http_error`
- `provider_request_failed`
- `json_decode_failed`
- `schema_validation_failed`
- `job_evidence_id_invalid`
- `profile_evidence_id_invalid`

Fallback은 분석 요청 실패가 아닙니다. 정상적인 `200` 응답 안에서 `analysis_method="deterministic"`, `fallback_reason`과 `warnings`로 분석 경로를 설명합니다.

## 5. 프로필 삭제

`DELETE /users/me/profile`

- 삭제 성공: `204`
- 이미 프로필이 없음: `404`
- 삭제 후 `GET /users/me/profile`: `404`
- 삭제 후 `POST /job-analyses`: `409`

현재 API는 프로필만 삭제하며 사용자 계정과 보안 감사 이벤트는 유지합니다.

## URL fetch 보안 경계

- HTTP(S)만 허용
- credential 포함 URL 차단
- localhost·사설 IP 차단
- redirect마다 대상 재검증
- redirect 최대 3회
- 응답 최대 1MB
- fetch timeout 8초
- JavaScript 실행, 로그인·CAPTCHA 우회 미지원

## 정상 완료 기준

사용자는 Swagger에서 다음을 수행할 수 있어야 합니다.

1. 계정을 만들고 JWT로 인증합니다.
2. Markdown 이력서를 등록합니다.
3. 공개 공고 URL 또는 본문을 분석합니다.
4. 약 1분 안에 LLM 또는 명시적인 fallback 결과를 받습니다.
5. 프로필을 삭제하고 더 이상 조회·분석할 수 없음을 확인합니다.
