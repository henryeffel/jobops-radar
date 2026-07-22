import json

from openai import APIStatusError, APITimeoutError, OpenAI, RateLimitError
from pydantic import AliasChoices, BaseModel, Field, ValidationError, field_validator

from app.core.config import Settings
from app.job_analysis.structured_input import LLMComparisonInput


class LLMRequirement(BaseModel):
    name: str = Field(min_length=1, max_length=100)
    requirement_type: str = Field(min_length=1, max_length=50)
    job_evidence_ids: list[str] = Field(
        min_length=1,
        max_length=5,
        validation_alias=AliasChoices("job_evidence_ids", "job_evidence_id"),
    )
    profile_evidence_ids: list[str] = Field(
        default_factory=list,
        max_length=5,
        validation_alias=AliasChoices(
            "profile_evidence_ids",
            "profile_evidence_id",
        ),
    )

    @field_validator("job_evidence_ids", "profile_evidence_ids", mode="before")
    @classmethod
    def normalize_evidence_ids(cls, value):
        if value is None:
            return []
        if isinstance(value, str):
            return [value]
        if isinstance(value, list) and all(isinstance(item, str) for item in value):
            return list(dict.fromkeys(value))[:5]
        return value


class LLMAnalysis(BaseModel):
    requirements: list[LLMRequirement] = Field(max_length=50)


class LLMAnalysisError(RuntimeError):
    def __init__(self, message: str, reason_code: str = "llm_error") -> None:
        self.reason_code = reason_code
        super().__init__(message)


def _decode_json_content(content: str) -> object:
    cleaned = content.strip().lstrip("\ufeff")
    if cleaned.startswith("```json") and cleaned.endswith("```"):
        cleaned = cleaned[7:-3].strip()
    elif cleaned.startswith("```") and cleaned.endswith("```"):
        cleaned = cleaned[3:-3].strip()
    return json.loads(cleaned)


def _validation_summary(exc: ValidationError) -> str:
    details = []
    for error in exc.errors(include_url=False, include_input=False):
        location = ".".join(str(part) for part in error["loc"])
        details.append(f"{location}:{error['type']}")
    return ", ".join(details[:10])


def _validate_evidence_ids(
    result: LLMAnalysis,
    comparison_input: LLMComparisonInput,
) -> None:
    job_ids = {section.evidence_id for section in comparison_input.job.sections}
    profile_ids = {
        section.evidence_id for section in comparison_input.candidate.sections
    }
    for requirement in result.requirements:
        if not set(requirement.job_evidence_ids).issubset(job_ids):
            raise LLMAnalysisError(
                "LLM returned an unknown job evidence ID",
                "job_evidence_id_invalid",
            )
        if not set(requirement.profile_evidence_ids).issubset(profile_ids):
            raise LLMAnalysisError(
                "LLM returned an unknown profile evidence ID",
                "profile_evidence_id_invalid",
            )


def analyze_with_llm(
    comparison_input: LLMComparisonInput,
    settings: Settings,
) -> LLMAnalysis:
    if not settings.llm_api_key:
        raise LLMAnalysisError("LLM_API_KEY is not configured", "llm_not_configured")
    client = OpenAI(
        base_url=settings.llm_base_url,
        api_key=settings.llm_api_key,
        timeout=settings.llm_timeout_seconds,
        max_retries=0,
    )
    input_json = comparison_input.model_dump_json()
    if len(input_json) > settings.llm_max_input_chars:
        raise LLMAnalysisError(
            "Structured LLM input exceeds the configured limit",
            "llm_input_too_large",
        )
    prompt = f"""Analyze the structured job posting against the structured candidate profile.
Return JSON only with this shape:
{{"requirements":[{{"name":"...","requirement_type":"skill|experience|operations|architecture|culture|language|education","job_evidence_ids":["job-001"],"profile_evidence_ids":["candidate-001"]}}]}}

Rules:
- Extract only requirements explicitly supported by the job posting.
- Reference only evidence_id values that exist in the input JSON.
- Every requirement needs at least one job_evidence_id.
- Use profile_evidence_ids only when those sections directly support a match; otherwise return an empty list.
- Never copy or rewrite evidence text in the output.
- Do not classify required/preferred status or calculate importance; the server does that from the referenced job sections.
- Do not include private data unrelated to the comparison.

INPUT JSON:
{input_json}
"""
    try:
        response = client.chat.completions.create(
            model=settings.llm_model,
            messages=[
                {"role": "system", "content": "You are a precise job requirement extraction service."},
                {"role": "user", "content": prompt},
            ],
            temperature=0,
            max_tokens=settings.llm_max_output_tokens,
            response_format={"type": "json_object"},
            extra_body={"chat_template_kwargs": {"enable_thinking": False}},
        )
        content = response.choices[0].message.content
        if not content:
            raise LLMAnalysisError("LLM returned an empty response", "empty_content")
        result = LLMAnalysis.model_validate(_decode_json_content(content))
    except ValidationError as exc:
        raise LLMAnalysisError(
            f"LLM response failed schema validation: {_validation_summary(exc)}",
            "schema_validation_failed",
        ) from exc
    except (IndexError, json.JSONDecodeError) as exc:
        raise LLMAnalysisError(
            "LLM returned invalid JSON content",
            "json_decode_failed",
        ) from exc
    except LLMAnalysisError:
        raise
    except APITimeoutError as exc:
        raise LLMAnalysisError("LLM request timed out", "provider_timeout") from exc
    except RateLimitError as exc:
        raise LLMAnalysisError(
            "LLM provider rate limit was reached",
            "provider_rate_limited",
        ) from exc
    except APIStatusError as exc:
        reason = (
            "provider_capacity_exhausted"
            if exc.status_code == 503
            else "provider_http_error"
        )
        raise LLMAnalysisError("LLM provider returned an error", reason) from exc
    except Exception as exc:
        raise LLMAnalysisError("LLM request failed", "provider_request_failed") from exc
    _validate_evidence_ids(result, comparison_input)
    return result
