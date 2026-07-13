# ADR-0001: FastAPI 사용

## 상태
승인됨

## 배경
JobOps Radar에는 type 기반 API, 빠른 반복 개발, 명확한 API 문서가 필요합니다.

## 결정
HTTP framework로 FastAPI를 사용합니다. Type 기반 validation, dependency system, OpenAPI schema, `/docs`의 Swagger UI를 활용합니다.

## 결과

장점:
- 목표 직무의 Python/FastAPI 기술과 일치합니다.
- 적은 설정으로 대화형 API 문서를 제공합니다.
- Pydantic 설정과 schema를 직접 연결할 수 있습니다.

단점:
- Async 성능이 자동으로 확보되는 것은 아니며 blocking dependency를 주의해야 합니다.
- Framework 편의 기능이 service 경계나 test를 대신하지 않습니다.

## 검토한 대안
- Flask: core는 작지만 validation과 API 문서 작업이 더 필요합니다.
- Django REST Framework: 성숙하지만 현재 MVP에는 무겁습니다.
