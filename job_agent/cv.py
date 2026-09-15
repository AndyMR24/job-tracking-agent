"""Local Markdown CV drafts assembled only from profile facts."""
from __future__ import annotations

from pathlib import Path

from .models import Job
from .profile import Profile


def generate(job: Job, profile: Profile, output: str | Path) -> tuple[Path, list[str]]:
    data = profile.data
    required = {r.text.lower() for r in job.requirements}
    chosen_skills = [s for s in data["skills"] if s["name"].lower() in required] or data["skills"]
    project_skills = {skill.lower() for project in data["projects"] for skill in project["technologies"]}
    projects = [p for p in data["projects"] if required & {s.lower() for s in p["technologies"]}] or data["projects"]
    lines = [f"# {data['identity']['name']}", "", data["identity"]["city"], "", "## Targeted application", f"Prepared locally for: {job.title}" + (f" at {job.company}" if job.company else ""), "", "## Education"]
    for education in data["education"]: lines += [f"### {education['degree']}", f"{education['institution']} | {education['period']}", education.get("detail", ""), ""]
    lines += ["## Relevant projects"]
    for project in projects:
        lines += [f"### {project['name']} | {', '.join(project['technologies'])}", project["description"], ""]
    lines += ["## Technical skills", ", ".join(s["name"] for s in chosen_skills), "", "## Languages"]
    lines += [f"{language}: {level}" for language, level in data["languages"].items()]
    lines += ["", "## Certifications"] + [f"- {item}" for item in data["certifications"]]
    path = Path(output); path.parent.mkdir(parents=True, exist_ok=True); path.write_text("\n".join(line for line in lines if line is not None) + "\n", encoding="utf-8")
    facts = ["education", "projects", "skills", "languages", "certifications"]
    return path, facts
