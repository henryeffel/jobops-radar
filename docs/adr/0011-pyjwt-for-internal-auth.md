# ADR-0011: 내부 인증에 PyJWT 사용

## 상태
승인됨

## 배경
이 프로젝트에는 Identity Provider가 아니라 작고 검증 가능한 자체 로그인 흐름이 필요합니다.

## 결정
수명이 짧은 HS256 access token에 PyJWT를 사용하고 비밀번호는 Argon2로 해싱합니다. Token에는 `sub`, `iat`, `exp`, `type` claim을 포함합니다.

## 검토한 대안
1. Server-side session
2. 외부 Managed Identity Provider

## 결과
의존성과 검증 과정이 작고 명시적입니다. 반면 하나의 서명 비밀 키를 공유하며 token 폐기 기능이 없습니다.

## 전환 조건
- 여러 서비스가 token을 검증해야 할 때
- 키 교체 또는 token 폐기 요구사항이 생길 때
