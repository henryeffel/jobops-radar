# Karrot Identity Service 사례 연구

## 1. 공고 요약
Identity/Auth 플랫폼, OIDC 기반 외부 로그인, B2B 계정, 고가용성, 보안·개인정보, 인증 UX, AI 협업 개발이 주요 요구사항입니다.

## 2. 도메인 문제
로그인과 세션 생명주기, token 발급·폐기, 계정 보안, 조직 멤버십, 감사 가능성을 다뤄야 합니다.

## 3. 예상 실패 시나리오
반복 로그인 실패, 탈취된 refresh token, 세션 저장소 장애, token 검증 오류, 만료된 서명 키, 계정 존재 여부 노출이 있습니다.

## 4. 현재 역량 차이
일치: Python, FastAPI, SQLAlchemy, validation, testing

부분 일치: JWT, 인증 설계, 감사 로그

부족: 운영 환경 OIDC, Redis session 운영, 대규모 트래픽 운영, Kafka/gRPC, Kubernetes

## 5. 프로젝트에 반영한 변경
Identity와 Audit 모듈, 인증 설계 문서, Modular Monolith ADR, fixture provider 경계를 추가했습니다.

## 6. 명시적인 비목표
완전한 OIDC Provider, 운영 규모의 Microservices, 대규모 트래픽 경험 주장, Kubernetes 배포는 현재 범위가 아닙니다.

## 7. 배운 점
신뢰할 수 있는 산출물은 큰 Identity Platform을 만들었다는 주장이 아니라, 범위를 좁힌 보안 경계와 실패 동작을 테스트로 증명하는 것입니다. 아키텍처를 확장하기 전에 모르는 부분과 전환 조건을 먼저 드러내야 합니다.
