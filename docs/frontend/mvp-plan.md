# 프론트엔드 MVP 계획

## 목표

일반 사용자가 Swagger, JSON과 JWT 구조를 몰라도 웹 화면에서 JobOps Radar의 핵심 기능을 사용할 수 있게 합니다.

```text
회원가입·로그인
  → 이력서 등록·확인
  → 채용공고 URL 또는 본문 입력
  → 분석 진행 상태 확인
  → 점수·근거·부족 역량·준비 계획 확인
  → 프로필 삭제
```

프론트엔드 MVP는 로컬 브라우저에서 이 전체 흐름이 동작하는 단계입니다. AWS 공개 배포, custom domain과 production cookie 인증은 다음 배포 단계에서 완료합니다.

## 기술 선택

- React
- TypeScript
- Vite
- React Router
- native Fetch 기반 API client
- CSS variables와 responsive layout

현재 제품은 로그인 이후 사용하는 단일 사용자 dashboard가 중심이고 SSR이 핵심 요구사항이 아니므로 정적 React SPA를 사용합니다. frontend는 `frontend/` 디렉터리에 두고 기존 FastAPI backend와 독립적으로 build합니다.

## 화면 범위

### 랜딩

- 제품이 해결하는 문제
- 분석 과정과 개인정보 경계
- 시작·로그인 진입점
- 점수는 합격 확률이 아니라 문서 근거 일치도라는 안내

### 회원가입·로그인

- 이메일과 비밀번호 입력
- 입력 validation
- 중복 이메일, 잘못된 인증과 server 오류 표시
- 로그인 성공 후 dashboard 이동

초기 frontend MVP는 기존 Bearer JWT API와 연결하기 위해 token을 browser session storage에 보관합니다. localStorage 장기 저장은 사용하지 않습니다. AWS 공개 배포 전 HttpOnly secure cookie 방식으로 전환하거나 별도 ADR에서 현재 방식을 수용해야 합니다.

### 프로필

- Markdown 이력서 입력
- 저장·교체
- 구조화된 summary, skills, projects, education, certifications 표시
- 프로필 삭제 confirmation
- 프로필이 없으면 분석 전에 등록하도록 안내

### 채용공고 분석

- 공개 채용공고 URL 입력
- HTML·본문 직접 입력 fallback
- 외부 LLM 전송 명시적 checkbox
- 분석 중 최대 약 1분이 걸릴 수 있다는 상태 표시
- URL과 본문 중 하나 이상 요구

### 결과

- 문서 근거 일치도 점수
- `llm` 또는 `deterministic` 분석 방식
- fallback reason의 사용자용 설명
- matched·missing 항목
- 필수·우대와 중요도
- 공고·프로필 근거
- 부족 항목 준비 계획
- 점수 한계 안내

## 사용자용 fallback 메시지

backend reason code를 그대로 주 오류 문구로 노출하지 않고 이해 가능한 설명으로 변환합니다.

| reason | 사용자 메시지 |
| --- | --- |
| `llm_mock_mode` | 현재 기본 분석 모드로 결과를 만들었습니다. |
| `external_llm_consent_required` | 외부 AI 전송 동의 없이 기본 분석을 사용했습니다. |
| `provider_timeout` | AI 응답이 지연되어 기본 분석 결과를 표시합니다. |
| `provider_capacity_exhausted` | AI 사용량이 많아 기본 분석 결과를 표시합니다. |
| `schema_validation_failed` | AI 결과를 안전하게 검증할 수 없어 기본 분석을 사용했습니다. |
| 기타 provider 오류 | AI 분석을 사용할 수 없어 기본 분석 결과를 표시합니다. |

## 상태와 오류 처리

- 모든 요청에 loading, success, empty, error 상태를 둡니다.
- `401`: session을 제거하고 로그인 화면으로 이동합니다.
- 프로필 조회 `404`: 오류가 아닌 empty profile 상태로 처리합니다.
- 분석 `409`: 프로필 등록 화면으로 안내합니다.
- URL fetch `422`: 공고 본문 직접 입력을 제안합니다.
- LLM fallback `200`: 실패 화면이 아니라 분석 방식이 다른 정상 결과로 표시합니다.

## 접근성과 반응형

- keyboard로 모든 form과 button 사용
- form label과 오류 메시지 연결
- 색상만으로 matched·missing을 구분하지 않음
- mobile 360px 이상에서 핵심 흐름 사용 가능
- 분석 진행 상태에 `aria-live` 사용
- reduced-motion 환경 존중

## 로컬 실행

```powershell
# backend
python -m uvicorn app.main:app --reload

# frontend
Set-Location frontend
npm install
npm run dev
```

개발 frontend origin은 `http://127.0.0.1:5173`이며 backend CORS allowlist에 명시합니다. production에서는 same-origin reverse proxy 또는 명시적인 production origin만 허용합니다.

## 완료 조건

다음 항목이 모두 충족되면 프론트엔드 MVP를 완료로 판단합니다.

1. 사용자가 UI에서 회원가입하고 로그인할 수 있습니다.
2. 로그인하지 않은 사용자는 dashboard에 접근할 수 없습니다.
3. Markdown 이력서를 등록하고 구조화 결과를 확인할 수 있습니다.
4. URL 또는 본문으로 공고 분석을 요청할 수 있습니다.
5. 외부 LLM 동의를 사용자가 직접 선택할 수 있습니다.
6. 분석 중 상태와 약 1분 대기 가능성을 확인할 수 있습니다.
7. 점수, 분석 방식, matched·missing, 근거와 준비 계획을 읽을 수 있습니다.
8. fallback 결과를 실패 페이지가 아닌 설명 가능한 정상 결과로 확인할 수 있습니다.
9. 사용자가 자신의 프로필을 삭제하고 empty 상태를 확인할 수 있습니다.
10. mobile과 desktop layout에서 핵심 흐름이 동작합니다.
11. production build가 성공합니다.
12. 기존 backend 전체 테스트가 통과합니다.

## 프론트엔드 MVP 비목표

- PDF·DOCX 이력서 upload와 OCR
- GitHub repository 전체 분석
- 소셜 로그인
- refresh token과 장기 session
- 분석 history·공유 링크
- 결제
- 관리자 dashboard
- 다국어 번역 시스템
- AWS infrastructure 자동 생성

## AWS 배포 단계

프론트엔드 MVP 후 다음을 별도 단계로 수행합니다.

1. HttpOnly secure cookie 또는 승인된 production token 전략
2. frontend/backend production container
3. same-origin HTTPS reverse proxy
4. PostgreSQL backup과 secret 관리
5. EC2 기반 첫 공개 배포
6. Route 53 domain과 TLS
7. CloudWatch log·alarm
8. GitHub Actions 자동 배포

초기 AWS 목표는 새 사용자가 공개 URL에 접속해 가입부터 실제 LLM 분석과 프로필 삭제까지 수행하는 것입니다. 트래픽·운영 필요가 생기면 frontend는 Amplify Hosting, backend는 ECS Fargate, DB는 RDS PostgreSQL로 분리합니다.

## 관련 문서

- [Swagger backend MVP 상태](../project/mvp-status.md)
- [Backend API 가이드](../api/mvp-api-guide.md)
- [시스템 구조](../architecture/system-overview.md)
- [사용자 데이터 처리](../privacy/data-handling.md)
- [LLM 오류 개선 기록](../experiments/llm-structured-analysis-troubleshooting.md)
