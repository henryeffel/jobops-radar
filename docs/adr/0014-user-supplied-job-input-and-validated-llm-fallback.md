# ADR-0014: 사용자 제공 공고 입력과 검증된 LLM fallback

## 상태

승인됨

## 배경

Saramin 공식 API 승인이 지연되면서 외부 승인 여부가 제품의 핵심 흐름을 막았습니다. JobOps Radar가 검증해야 하는 핵심 가치는 대량 공고 수집이 아니라 사용자가 관심 있는 공고 하나를 자신의 프로필과 비교해 설명 가능한 결과를 얻는 것입니다.

채용 사이트마다 HTML 구조, JavaScript 렌더링, 로그인, CAPTCHA, 이용약관이 다르므로 범용 자동 수집을 보장할 수 없습니다. 또한 LLM은 다양한 표현의 요구사항을 찾는 데 유용하지만 timeout, provider 용량 부족, 잘못된 JSON, 원문에 없는 근거 생성 가능성이 있습니다.

## 결정

사용자가 공개 채용공고의 URL을 직접 제출하는 흐름을 기본으로 하고, 수집이 불가능하거나 허용되지 않는 사이트에는 공고 HTML·본문 직접 입력을 fallback으로 제공합니다. 로그인, CAPTCHA, JavaScript 실행 또는 접근 제한 우회는 구현하지 않습니다.

URL fetch는 HTTP(S)만 허용하고 credential 포함 URL, 사설·로컬 주소를 차단합니다. redirect마다 목적지를 다시 검증하며 timeout, redirect 횟수와 응답 크기를 제한합니다.

분석은 다음 두 경로를 사용합니다.

1. `LLM_MOCK_MODE=false`이고 키가 설정되면 OpenAI-compatible NVIDIA endpoint에 구조화 JSON을 요청합니다.
2. 공고·프로필을 ID가 있는 section JSON으로 만들고, LLM이 반환한 evidence ID가 실제 입력 section에 존재하는지 검증합니다.
3. timeout, provider 오류, 잘못된 JSON 또는 근거 검증 실패 시 결정론적 기술 사전 분석으로 전환하고 응답에 경고를 포함합니다.

적합도는 검증을 통과한 요구사항의 중요도 가중치로 서버가 계산합니다. 모델의 reasoning 출력은 저장하거나 사용자에게 반환하지 않습니다. API 키는 환경변수에서만 읽습니다.

## 결과와 trade-off

외부 공고 API 승인 없이도 URL 하나를 중심으로 실제 사용자 흐름을 검증할 수 있고, 본문 직접 입력으로 사이트별 실패를 복구할 수 있습니다. SSRF와 무제한 다운로드 위험을 줄이며 LLM 실패가 전체 분석 실패로 전파되지 않습니다.

반면 HTML 구조 변경과 동적 렌더링에 취약하고 모든 사이트를 지원하지 않습니다. 결정론적 fallback은 알려진 기술 사전 밖의 요구사항을 놓칠 수 있습니다. 무료 LLM provider는 지연과 용량 초과가 발생하며, 현재 실제 이력서 검증에서는 provider 요청 실패와 구조화 응답 검증 실패가 관찰됐습니다. 따라서 현재 LLM 경로는 검증된 보조 기능이지 안정적인 단일 진실 공급원이 아닙니다.

## 대체하는 결정

ADR-0008의 “승인 전에는 공고 페이지를 가져오지 않는다”는 제품 입력 전략을 대체합니다. 대량 scraping이나 접근 제한 우회 금지는 유지합니다. ADR-0010의 외부 공급자 격리 원칙은 유지하지만 Saramin adapter는 현재 MVP 경로에서 제외합니다.

## 검토한 대안

1. Saramin API 승인까지 개발을 중단합니다.
2. 사이트별 scraper와 headless browser를 구현합니다.
3. LLM 결과를 검증 없이 그대로 적합도에 사용합니다.
4. LLM 장애 시 전체 요청을 실패시킵니다.

## 관련 문서

- `docs/architecture/system-overview.md`
- `docs/project/risk-register.md`
- `docs/session-logs/2026-07-21.md`
- `README.md`
