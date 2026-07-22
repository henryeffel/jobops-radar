# Frontend MVP 구현 현황

기준일: 2026-07-21

## 구현 결과

`mvp-plan.md`에 정의한 화면 흐름을 React, TypeScript, Vite 기반 SPA로 구현했습니다.

- 회원가입과 로그인
- `sessionStorage` 기반 로그인 세션과 보호된 dashboard
- Markdown 이력서 등록, 수정, 조회, 삭제
- 채용공고 URL 또는 본문 직접 입력
- 외부 LLM 전송에 대한 명시적 사용자 동의
- 최대 1분가량의 분석 대기를 설명하는 loading 상태
- 점수, 분석 방식, fallback 사유, 일치·부족 항목, 근거, 준비 계획 표시
- 모바일과 desktop 반응형 layout
- keyboard focus, label, `aria-live`, reduced-motion 처리
- FastAPI 개발 origin CORS allowlist

## 검증 결과

- `npm.cmd run build`: 통과
- Vite 개발 서버 `/`: HTTP 200
- Vite module `/src/main.tsx`: HTTP 200
- FastAPI CORS preflight: HTTP 200 및 올바른 `access-control-allow-origin`
- `python -m pytest`: 78 passed

## MVP 경계

현재 결과는 로컬에서 backend와 frontend를 함께 실행할 수 있는 frontend MVP입니다. AWS 공개 배포, production domain·HTTPS, HttpOnly cookie 기반 인증 강화, 실제 브라우저별 수동 QA는 배포 단계의 후속 작업입니다.
