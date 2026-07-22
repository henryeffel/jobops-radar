import re
from collections import defaultdict


HEADING_PATTERN = re.compile(r"^(#{1,6})\s+(.+?)\s*$")
BULLET_PATTERN = re.compile(r"^\s*[-*+]\s+(.+?)\s*$")


def _normalize_heading(value: str) -> str:
    return re.sub(r"[^a-z0-9가-힣]+", " ", value.lower()).strip()


def _split_sections(markdown: str) -> dict[str, list[str]]:
    sections: dict[str, list[str]] = defaultdict(list)
    current = ""
    for line in markdown.replace("\r\n", "\n").splitlines():
        match = HEADING_PATTERN.match(line)
        if match:
            current = _normalize_heading(match.group(2))
            continue
        if current and line.strip() not in {"", "---"}:
            sections[current].append(line.rstrip())
    return dict(sections)


def _section_text(sections: dict[str, list[str]], *names: str) -> str | None:
    for name in names:
        lines = sections.get(name)
        if lines:
            return "\n".join(lines).strip()
    return None


def _bullet_items(text: str | None) -> list[str]:
    if not text:
        return []
    return [
        match.group(1).strip()
        for line in text.splitlines()
        if (match := BULLET_PATTERN.match(line))
    ]


MAJOR_SECTIONS = {
    "summary",
    "skills",
    "projects",
    "education",
    "certifications",
    "certifications training",
    "experience",
    "work experience",
}


def _top_level_entries(markdown: str, parent: str) -> list[str]:
    entries: list[str] = []
    inside_parent = False
    parent_level = 0
    for line in markdown.replace("\r\n", "\n").splitlines():
        match = HEADING_PATTERN.match(line)
        if not match:
            continue
        level = len(match.group(1))
        heading = match.group(2).strip()
        normalized = _normalize_heading(heading)
        if normalized == parent:
            inside_parent = True
            parent_level = level
        elif inside_parent and normalized in MAJOR_SECTIONS:
            break
        elif inside_parent and level <= parent_level:
            break
        elif inside_parent and level == parent_level + 1:
            entries.append(heading)
    return entries


def parse_resume_markdown(markdown: str) -> dict[str, object]:
    """Extract stable profile fields without guessing facts absent from the resume."""
    sections = _split_sections(markdown)
    skills_text = _section_text(sections, "skills", "기술", "기술 스택")
    certifications_text = _section_text(
        sections,
        "certifications training",
        "certifications",
        "자격증 교육",
        "자격증",
    )
    return {
        "summary": _section_text(sections, "summary", "요약", "소개"),
        "skills": _bullet_items(skills_text),
        "projects": _top_level_entries(markdown, "projects"),
        "education": _top_level_entries(markdown, "education"),
        "certifications": _bullet_items(certifications_text),
    }
