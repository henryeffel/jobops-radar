import json
import logging
import re
from dataclasses import dataclass

from app.core.config import Settings, get_settings
from app.core.request_tracing import get_request_id
from app.identity.profile_models import UserProfile
from app.integrations.llm_api import LLMAnalysisError, analyze_with_llm
from app.job_analysis.fetcher import extract_visible_text, fetch_job_content
from app.job_analysis.llm_guard import LLMCapacityError, LLMConcurrencyGuard
from app.job_analysis.structured_input import build_comparison_input


logger = logging.getLogger(__name__)
_settings = get_settings()
llm_concurrency_guard = LLMConcurrencyGuard(
    _settings.llm_max_concurrency,
    _settings.llm_wait_timeout_seconds,
)


@dataclass(frozen=True)
class RequirementDefinition:
    name: str
    requirement_type: str
    aliases: tuple[str, ...]
    profile_aliases: tuple[str, ...] = ()


REQUIREMENTS = (
    RequirementDefinition("Python", "skill", ("python",)),
    RequirementDefinition("FastAPI", "skill", ("fastapi",)),
    RequirementDefinition("Django", "skill", ("django",)),
    RequirementDefinition("Flask", "skill", ("flask",)),
    RequirementDefinition(
        "SQL",
        "skill",
        ("sql", "postgresql", "mysql"),
        ("sql", "postgresql", "mysql", "sqlalchemy"),
    ),
    RequirementDefinition("SQLAlchemy", "skill", ("sqlalchemy",)),
    RequirementDefinition("Alembic", "skill", ("alembic",)),
    RequirementDefinition("REST API", "architecture", ("rest api", "restful")),
    RequirementDefinition("Git", "skill", ("git", "github")),
    RequirementDefinition("Linux", "operations", ("linux",)),
    RequirementDefinition("Docker", "operations", ("docker", "container")),
    RequirementDefinition("Kubernetes", "operations", ("kubernetes", "k8s")),
    RequirementDefinition("AWS", "operations", ("aws", "amazon web services")),
    RequirementDefinition("Azure", "operations", ("azure",)),
    RequirementDefinition("GCP", "operations", ("gcp", "google cloud")),
    RequirementDefinition("RAG", "architecture", ("rag", "retrieval augmented")),
    RequirementDefinition("LLM", "skill", ("llm", "large language model", "생성형 ai")),
    RequirementDefinition("Machine Learning", "skill", ("machine learning", "머신러닝")),
    RequirementDefinition("CI/CD", "operations", ("ci/cd", "continuous integration")),
    RequirementDefinition("Testing", "skill", ("pytest", "unit test", "테스트")),
)

REQUIRED_MARKERS = ("required", "필수", "자격요건", "자격 요건")
PREFERRED_MARKERS = ("preferred", "nice to have", "우대", "선호")


def _contains(text: str, alias: str) -> bool:
    return re.search(rf"(?<![a-z0-9]){re.escape(alias)}(?![a-z0-9])", text) is not None


def _evidence(text: str, aliases: tuple[str, ...]) -> str:
    lines = [line.strip() for line in text.splitlines() if line.strip()]
    for line in lines:
        lowered = line.lower()
        if any(_contains(lowered, alias) for alias in aliases):
            return line[:500]
    return ""


def _profile_text(profile: UserProfile) -> str:
    return "\n".join(
        [
            profile.summary or "",
            *profile.skills,
            *profile.projects,
            *profile.education,
            *profile.certifications,
            profile.resume_markdown,
        ]
    )


def _classify_evidence_sections(sections) -> tuple[bool, int]:
    headings = "\n".join(section.heading or "" for section in sections).lower()
    text = "\n".join(section.text for section in sections).lower()
    preferred_heading = (
        re.search(r"\bpreferred\b|\bnice[- ]to[- ]have\b", headings)
        or "우대" in headings
        or "선호" in headings
    )
    if preferred_heading:
        return False, 3
    required_heading = (
        re.search(r"\brequired\b|\bmust[- ]have\b", headings)
        or "필수" in headings
        or "자격요건" in headings
        or "자격 요건" in headings
    )
    explicit_required_text = (
        re.search(r"\brequired qualification(?:s)?\b|\byou must have\b", text)
        or "필수 자격요건" in text
        or "필수 자격 요건" in text
    )
    if required_heading or explicit_required_text:
        return True, 5
    return False, 2


def _finalize(
    results: list[dict[str, object]],
    analysis_method: str,
    warnings: list[str] | None = None,
    fallback_reason: str | None = None,
) -> dict[str, object]:
    total_weight = sum(int(item["importance"]) for item in results)
    matched_weight = sum(int(item["importance"]) for item in results if item["matched"])
    score = round(matched_weight / total_weight * 100) if total_weight else 0
    missing = [item for item in results if not item["matched"]]
    missing.sort(key=lambda item: (not bool(item["is_required"]), -int(item["importance"])))
    return {
        "analysis_method": analysis_method,
        "fallback_reason": fallback_reason,
        "match_score": score,
        "requirements": results,
        "matched_skills": [item["name"] for item in results if item["matched"]],
        "missing_skills": [item["name"] for item in missing],
        "action_plan": [
            {
                "skill": item["name"],
                "priority": "high" if item["is_required"] else "medium",
                "reason": item["evidence"],
                "action": f"Build a small, testable project using {item['name']} and add the result to your profile.",
            }
            for item in missing
        ],
        "warnings": warnings or [],
    }


def _analyze_deterministically(text: str, profile: UserProfile) -> dict[str, object]:
    job_text = text.lower()
    profile_text = _profile_text(profile).lower()
    results: list[dict[str, object]] = []
    for definition in REQUIREMENTS:
        if not any(_contains(job_text, alias) for alias in definition.aliases):
            continue
        evidence = _evidence(text, definition.aliases)
        is_required = any(marker in evidence.lower() for marker in REQUIRED_MARKERS)
        profile_aliases = definition.profile_aliases or definition.aliases
        matched = any(_contains(profile_text, alias) for alias in profile_aliases)
        results.append(
            {
                "name": definition.name,
                "requirement_type": definition.requirement_type,
                "is_required": is_required,
                "importance": 5 if is_required else 3,
                "matched": matched,
                "evidence": evidence,
                "profile_evidence": None,
            }
        )
    warnings = [] if results else ["No supported requirements were detected; review the source text manually."]
    return _finalize(results, "deterministic", warnings)


def analyze_job_text(
    text: str,
    profile: UserProfile,
    settings: Settings | None = None,
    allow_external_llm: bool = True,
) -> dict[str, object]:
    settings = settings or get_settings()
    if settings.llm_mock_mode:
        fallback = _analyze_deterministically(text, profile)
        fallback["fallback_reason"] = "llm_mock_mode"
        return fallback
    if not allow_external_llm:
        fallback = _analyze_deterministically(text, profile)
        fallback["fallback_reason"] = "external_llm_consent_required"
        fallback["warnings"] = [
            "External LLM analysis was not used because consent was not provided.",
            *fallback["warnings"],
        ]
        return fallback
    comparison_input = build_comparison_input(
        text,
        profile,
        settings.llm_max_input_chars,
    )
    try:
        llm_result = llm_concurrency_guard.run(
            lambda: analyze_with_llm(comparison_input, settings)
        )
        job_sections = {
            section.evidence_id: section
            for section in comparison_input.job.sections
        }
        profile_evidence = {
            section.evidence_id: section.text
            for section in comparison_input.candidate.sections
        }
        results = []
        for item in llm_result.requirements:
            referenced_job_sections = [
                job_sections[evidence_id]
                for evidence_id in item.job_evidence_ids
            ]
            is_required, importance = _classify_evidence_sections(
                referenced_job_sections
            )
            results.append({
                "name": item.name,
                "requirement_type": item.requirement_type,
                "is_required": is_required,
                "importance": importance,
                "matched": bool(item.profile_evidence_ids),
                "evidence": "\n".join(
                    section.text for section in referenced_job_sections
                ),
                "profile_evidence": "\n".join(
                    profile_evidence[evidence_id]
                    for evidence_id in item.profile_evidence_ids
                ) or None,
            })
        return _finalize(results, "llm")
    except (LLMAnalysisError, LLMCapacityError) as exc:
        fallback_reason = getattr(
            exc,
            "reason_code",
            "llm_capacity_exhausted",
        )
        logger.warning(
            json.dumps(
                {
                    "event": "llm_fallback",
                    "request_id": get_request_id(),
                    "reason": fallback_reason,
                },
                separators=(",", ":"),
                sort_keys=True,
            )
        )
        fallback = _analyze_deterministically(text, profile)
        fallback["fallback_reason"] = fallback_reason
        fallback["warnings"] = [
            "LLM analysis was unavailable; deterministic analysis was used.",
            *fallback["warnings"],
        ]
        return fallback


def analyze_job(
    profile: UserProfile,
    source_url: str | None,
    content: str | None,
    allow_external_llm: bool = False,
) -> dict[str, object]:
    if content:
        title, text = extract_visible_text(content)
        resolved_url = source_url
        input_method = "content"
    else:
        resolved_url, title, text = fetch_job_content(source_url or "")
        input_method = "url"
    analysis = analyze_job_text(
        text,
        profile,
        allow_external_llm=allow_external_llm,
    )
    return {
        "source_url": resolved_url,
        "page_title": title,
        "input_method": input_method,
        "extracted_text": text,
        **analysis,
    }
