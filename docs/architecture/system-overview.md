# 시스템 구조 개요

```text
사용자
  |-- 회원가입·로그인 ----------------------> Identity/Auth
  |-- Markdown 이력서 ---------------------> UserProfile
  |-- 공고 URL 또는 HTML·본문 --------------> Job Analysis
                                                   |
                         +-------------------------+-------------------------+
                         |                                                   |
                URL Fetch / HTML Parser                              Profile Matcher
                SSRF·크기·시간 제한                                  근거·가중치 검증
                         |                                                   |
                         +-------------------------+-------------------------+
                                                   |
                              +--------------------+--------------------+
                              |                                         |
                    NVIDIA LLM 구조화 분석                    결정론적 기술 사전 fallback
                    원문 근거 재검증                           재현 가능한 제한 분석

FastAPI Router
  |-- JobPosting / JobRequirement
  |-- Identity / UserProfile
  |-- JobAnalysis
  `-- AuditLog
           |
     SQLAlchemy + Alembic
           |
     SQLite / PostgreSQL
```

1. 현재 배포 단위는 하나입니다.
2. 각 도메인은 service/model/schema 경계로 분리합니다.
3. 외부 채용 API는 adapter 계층으로 격리하며 현재 MVP 입력은 사용자 제공 URL·본문입니다.
4. MSA 전환은 현재 요구사항이 아니라 미래의 조건부 선택입니다.
5. LLM은 검증 가능한 보조 분석기이며 provider 실패나 근거 검증 실패 시 결정론적 분석을 사용합니다.
6. URL fetch는 HTTP(S) 공개 주소만 허용하고 로그인·CAPTCHA·JavaScript 우회를 지원하지 않습니다.
