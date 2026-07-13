# ADR-0006: Frontend 구현 연기

## 상태
승인됨

## 배경
한정된 시간에 backend domain과 검증을 우선해야 하며 Swagger UI로 초기 API를 확인할 수 있습니다.

## 결정
공고·요구사항·분석 API가 안정되기 전까지 별도 frontend 구현을 연기합니다.

## 결과
Backend 완결성에 집중할 수 있지만 사용자 경험과 시각적 demo가 제한됩니다.

## 전환 조건
핵심 API 계약과 주요 실패 경로가 test로 안정되면 작은 읽기 중심 UI를 검토합니다.
