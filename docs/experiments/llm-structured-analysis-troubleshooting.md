# LLM 구조화 분석 오류 개선 기록

## 문서 목적

이 문서는 JobOps Radar의 실제 LLM 호출 실패를 재현하고 원인을 분리해 안전하게 수정한 과정을 기록합니다. evidence ID 계약으로 실제 전체 이력서 구조화 성공을 확인했지만 provider 지연·용량 문제는 남아 있으므로 fallback과 관측 개선은 계속 필요합니다.

API 키, 전체 이력서, provider의 전체 raw response와 reasoning content는 이 문서와 일반 application log에 기록하지 않습니다.

## 기대 동작

`LLM_MOCK_MODE=false`일 때 채용공고와 사용자 프로필을 NVIDIA OpenAI-compatible endpoint에 전달하고 다음 계약을 만족하는 JSON을 받습니다.

```json
{
  "requirements": [
    {
      "name": "Python",
      "requirement_type": "skill",
      "is_required": true,
      "importance": 5,
      "job_evidence_ids": ["job-001"],
      "profile_evidence_ids": ["candidate-003"]
    }
  ]
}
```

서버는 공고와 이력서를 ID가 있는 section JSON으로 먼저 변환합니다. LLM은 원문을 복사하지 않고 존재하는 evidence ID만 반환하며, 서버는 ID를 원문 section으로 복원한 뒤 중요도 기반 적합도를 계산합니다. 검증 실패나 provider 장애에는 결정론적 분석으로 fallback하고 `warnings`를 반환해야 합니다.

## 지금까지 관찰한 결과

| 입력 | 시간 | 결과 | 확인 가능한 해석 |
| --- | ---: | --- | --- |
| 작은 synthetic 공고·프로필 | 53.8초 | invalid structured response | JSON decoding 또는 Pydantic schema 검증 단계 실패 |
| 작은 후속 요청 | 2.6초 | HTTP 503 `ResourceExhausted` | 무료 provider worker 용량 초과, JSON 계약과 무관 |
| 실제 `resume_sample.md` 첫 요청 | 2.1초 | provider request failure | provider 단계 실패, 분석 미수행 |
| 실제 이력서 재시도 | 26.5초 | application validation failure | HTTP 연결 이후 실패. 빈 content 또는 원문 근거 검증 실패 가능성 |
| evidence ID 구조 첫 호출 | 38.2초 | Pydantic `ValidationError` | 문자열 근거 문제는 제거됐으나 모델의 필드·타입이 schema와 불일치 |
| 안전한 JSON 변형 정규화 후 재호출 | 60초 초과 | 수동 종료 | provider가 제한 시간 안에 응답을 완성하지 못함 |
| 작은 evidence ID 입력 | 20.9초 | 성공, 요구사항 3개 | JSON과 evidence ID 계약 검증 통과. 우대 항목을 필수로 분류한 semantic 오류 발견 |
| 전체 입력 schema 진단 | 19.7초 | `profile_evidence_ids:too_long` | 일부 요구사항이 5개보다 많은 유효 후보 근거를 반환 |
| bounded ID 정규화 후 전체 입력 | 17.1초 | 성공, 요구사항 16개 | `analysis_method=llm`, 최초 점수 61. 필수 판정 substring 오탐은 후속 서버 규칙으로 수정 |

실패는 하나의 JSON 문제로 단정할 수 없습니다. provider 가용성·지연과 schema 준수 문제가 각각 관찰됐습니다.

## 실패 유형 분류

### 1. Transport와 provider 오류

- DNS·TLS·timeout
- HTTP 429 또는 503
- provider worker 용량 초과

이 오류는 모델 출력 계약을 수정해도 해결되지 않습니다. 60초 timeout과 무재시도 정책을 유지하고 즉시 fallback하는 것이 현재 대응입니다.

### 2. 응답 envelope 오류

- `choices`가 비어 있음
- `message.content`가 비어 있음
- JSON 대신 reasoning field에 결과가 존재함

provider별 OpenAI-compatible 응답 차이를 확인해야 합니다. reasoning 전체를 저장하지 않고 `choices_count`, `content_present`, `finish_reason`, `reasoning_present` 같은 metadata만 관측합니다.

### 3. JSON 표현 차이

- Markdown code fence 안의 JSON
- JSON 앞뒤 설명 문장
- 출력 token 부족으로 잘린 JSON
- `response_format`을 모델이 완전히 준수하지 않음

허용 가능한 정규화는 BOM·공백 제거와 단일 JSON code fence 제거까지로 제한합니다. 임의의 문자열에서 첫 `{`와 마지막 `}`를 무조건 잘라내는 방식은 잘못된 응답을 정상으로 오인할 수 있으므로 충분한 테스트 없이 사용하지 않습니다.

### 4. Schema 불일치

- 필수 필드 누락
- `importance`가 1~5 밖의 값
- boolean 대신 문자열 반환
- requirement type 변형
- 최대 항목 수 또는 문자열 길이 초과

Pydantic 검증은 유지합니다. provider 응답을 느슨하게 받아들이기보다 prompt와 schema 예시를 개선하고, 안전한 범위의 명시적 alias만 정규화합니다.

### 5. Evidence ID 검증

- 존재하지 않는 `job_evidence_id` 반환
- 후보자 section을 공고 근거로 사용하는 잘못된 prefix
- 직접 근거가 없는데 `profile_evidence_ids`를 채움
- 단일 문자열, `null`, singular field 같은 안전하게 정규화할 수 있는 표현 차이

현재 구현은 `job-###`, `candidate-###` section ID 집합을 만들고 존재하지 않는 ID를 거부합니다. 단일 ID 문자열, `null`, singular field와 단일 JSON code fence만 명시적으로 정규화합니다. LLM이 반환한 텍스트를 유사도만으로 근거로 인정하지 않습니다.

## 안전한 진단 계획

각 실패는 다음 reason code 중 하나로 분류합니다.

- `provider_timeout`
- `provider_rate_limited`
- `provider_capacity_exhausted`
- `provider_http_error`
- `empty_choices`
- `empty_content`
- `json_decode_failed`
- `schema_validation_failed`
- `job_evidence_mismatch`
- `profile_evidence_missing`
- `profile_evidence_mismatch`

개발 로그에는 다음 metadata만 기록합니다.

- reason code
- HTTP status
- elapsed milliseconds
- response character count
- requirement count
- finish reason
- fallback 사용 여부

기록하지 않는 값:

- API key와 authorization header
- 전체 prompt와 전체 raw response
- 전체 이력서와 개인정보
- reasoning content
- access token

## 수정 순서

1. `LLMAnalysisError`에 안정적인 reason code를 추가합니다.
2. OpenAI SDK 예외에서 HTTP status와 timeout을 분류합니다.
3. content 존재 여부와 finish reason만 관측하는 개발 로그를 추가합니다.
4. 단일 JSON code fence와 singleton evidence ID를 처리하는 작은 정규화 함수를 테스트와 함께 유지합니다.
5. evidence ID의 prefix와 존재 여부 검증 사례를 확장합니다.
6. synthetic 입력으로 정상, code fence, 잘린 JSON, schema 오류, 허위 근거를 모두 검증합니다.
7. 실제 이력서 호출은 최소 횟수로 다시 실행하고 reason code만 기록합니다.
8. 실제 성공 응답에서도 원문 근거와 점수 계산이 일치하는지 사람이 검토합니다.

## 완료 조건

다음 조건을 모두 충족해야 실제 LLM 경로가 검증됐다고 판단합니다.

- 실제 provider 응답이 Pydantic schema를 통과합니다.
- 모든 `job_evidence_ids`가 입력 공고 section에 존재합니다.
- matched로 계산되는 모든 항목에 유효한 `profile_evidence_ids`가 있습니다.
- 적합도는 모델 값이 아니라 서버 가중치 계산과 일치합니다.
- 실패 유형별 reason code와 fallback이 테스트됩니다.
- API 키, 이력서 원문, reasoning이 로그에 포함되지 않습니다.
- provider timeout 50초와 주변 처리 시간을 포함해 약 60초 안에 성공하거나 결정론적 fallback으로 종료합니다.

## 현재 결론

문제는 하나의 “JSON 오류”가 아니었습니다. provider 용량·지연, evidence 문자열 복사, ID 목록 상한과 서버의 필수 판정 규칙이 각각 독립적으로 실패했습니다. section ID 계약, bounded ID 정규화와 서버 판정으로 실제 전체 입력 성공을 확인했습니다. 최초 61점은 필수 판정 오탐 수정 전 실험값이므로 제품 성능 지표로 사용하지 않습니다. provider 실패 가능성은 남아 있어 결정론적 fallback과 reason-code observability가 계속 필요합니다.

## 관련 문서

- [2026-07-21 세션 로그](../session-logs/2026-07-21.md)
- [ADR-0014](../adr/0014-user-supplied-job-input-and-validated-llm-fallback.md)
- [AI 협업 개발](../ai-assisted-development.md)
- [리스크 목록](../project/risk-register.md)
