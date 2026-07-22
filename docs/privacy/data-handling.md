# 사용자 데이터 처리 범위

## 목적

JobOps Radar MVP가 저장하거나 외부로 전송하는 사용자 데이터의 범위를 설명합니다. 이 문서는 법률 자문이나 완성된 개인정보 처리방침이 아니라 현재 구현의 기술적 경계입니다.

## 저장 데이터

- 계정 이메일
- Argon2로 해싱한 비밀번호
- 사용자가 입력한 Markdown 이력서 원문
- 이력서에서 구조화한 요약, 기술, 프로젝트, 학력과 자격 항목
- 회원가입과 로그인 성공·실패 보안 이벤트

비밀번호 평문, access token, raw authentication request와 LLM reasoning은 저장하지 않습니다.

## 외부 LLM 전송

`POST /job-analyses` 요청마다 `consent_to_external_llm=true`를 명시한 경우에만 외부 LLM 분석을 허용합니다. 동의를 보내지 않으면 공고와 이력서는 외부 LLM에 전송되지 않고 결정론적 분석을 사용합니다.

LLM에 전달하는 데이터:

- 사용자가 분석하려는 채용공고의 section JSON
- 사용자의 이력서 section JSON과 구조화 프로필
- 각 section을 참조하기 위한 evidence ID

API key, 로그인 비밀번호, JWT와 감사 로그는 LLM prompt에 포함하지 않습니다. 외부 provider의 자체 보존 정책은 JobOps Radar가 통제하지 못하므로 공개 서비스 전 provider 정책 확인과 사용자 고지가 필요합니다.

## 조회와 삭제

- `GET /users/me/profile`: 인증된 현재 사용자의 이력서 프로필 조회
- `PUT /users/me/profile`: 현재 사용자의 프로필 생성·교체
- `DELETE /users/me/profile`: 현재 사용자의 이력서 원문과 구조화 프로필 삭제

삭제 후 프로필 조회는 `404`, 공고 분석은 `409`를 반환합니다. 계정과 보안 감사 이벤트 삭제는 현재 MVP 범위에 포함되지 않습니다.

## 로그 원칙

일반 application log에 다음 값을 기록하지 않습니다.

- API key와 authorization header
- 이력서·공고 전체 원문
- LLM 전체 raw response와 reasoning
- 비밀번호와 access token

LLM 장애 진단에는 reason code, HTTP status, elapsed time, 응답 길이와 fallback 여부 같은 비식별 metadata만 사용합니다.

## 현재 한계

- 사용자 계정 전체 삭제 기능은 없습니다.
- 분석 결과는 현재 별도 테이블에 영속화하지 않습니다.
- 데이터 보존 기간과 backup 삭제 정책은 정해지지 않았습니다.
- 공개 배포를 위한 법적 개인정보 처리방침과 사용자 약관은 별도로 필요합니다.
