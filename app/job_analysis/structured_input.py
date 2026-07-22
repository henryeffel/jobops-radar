import re

from pydantic import BaseModel, Field

from app.identity.profile_models import UserProfile


HEADING = re.compile(r"^#{1,6}\s+(.+?)\s*$")


class EvidenceSection(BaseModel):
    evidence_id: str
    heading: str | None = None
    text: str = Field(min_length=1, max_length=1200)


class JobDocument(BaseModel):
    document_id: str = "job"
    sections: list[EvidenceSection]


class CandidateDocument(BaseModel):
    document_id: str = "candidate"
    summary: str | None
    skills: list[str]
    projects: list[str]
    education: list[str]
    certifications: list[str]
    sections: list[EvidenceSection]


class LLMComparisonInput(BaseModel):
    job: JobDocument
    candidate: CandidateDocument


def build_evidence_sections(
    text: str,
    prefix: str,
    character_budget: int,
) -> list[EvidenceSection]:
    sections: list[EvidenceSection] = []
    heading: str | None = None
    buffer: list[str] = []
    used = 0

    def flush() -> bool:
        nonlocal buffer, used
        content = "\n".join(part.strip() for part in buffer if part.strip()).strip()
        buffer = []
        if not content:
            return True
        content = content[:1200]
        if used + len(content) > character_budget:
            return False
        sections.append(
            EvidenceSection(
                evidence_id=f"{prefix}-{len(sections) + 1:03d}",
                heading=heading,
                text=content,
            )
        )
        used += len(content)
        return len(sections) < 80

    for raw_line in text.replace("\r\n", "\n").splitlines():
        line = raw_line.strip()
        match = HEADING.match(line)
        if match:
            if not flush():
                break
            heading = match.group(1).strip()
        elif not line:
            if not flush():
                break
        else:
            buffer.append(line)
    if len(sections) < 80:
        flush()
    return sections


def build_comparison_input(
    job_text: str,
    profile: UserProfile,
    max_input_chars: int,
) -> LLMComparisonInput:
    section_budget = max(1000, max_input_chars // 3)
    return LLMComparisonInput(
        job=JobDocument(
            sections=build_evidence_sections(job_text, "job", section_budget),
        ),
        candidate=CandidateDocument(
            summary=profile.summary,
            skills=profile.skills,
            projects=profile.projects,
            education=profile.education,
            certifications=profile.certifications,
            sections=build_evidence_sections(
                profile.resume_markdown,
                "candidate",
                section_budget,
            ),
        ),
    )
