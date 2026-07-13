# ADR-0002: Backend-first MVP

## 상태
승인됨

## 배경
핵심 가치는 공고 수집, 요구사항 구조화, 역량 차이 분석에 있으며 초기에는 한 명이 개발합니다.

## 결정
Frontend보다 backend domain, API, persistence, test를 먼저 완성합니다.

## 결과
핵심 규칙을 UI와 분리해 검증하고 목표 backend 역량을 선명하게 보여줄 수 있습니다. 반면 초기에는 사용자용 화면이 없고 API client나 Swagger UI가 필요합니다.

## 검토한 대안
- Full-stack 동시 개발: 시각적 결과는 빠르지만 핵심 backend 검증이 분산됩니다.
- 문서만 작성: 결정은 남지만 실행 증거가 부족합니다.
