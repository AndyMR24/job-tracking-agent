"""Explainable, deliberately conservative job-fit evaluation."""
from __future__ import annotations

import re
from dataclasses import asdict, dataclass

from .models import Job
from .profile import Profile


def _matches_target_role(title: str, roles: list[str]) -> bool:
    """Recognize small, explicit title variants without matching generic words."""
    normalized = " ".join(title.lower().replace("/", " ").split())
    for role in roles:
        target = " ".join(role.lower().replace("/", " ").split())
        if target in normalized:
            return True
        if target == "data scientist" and "data science" in normalized:
            return True
        if target == "python developer" and "python" in normalized and "developer" in normalized:
            return True
        if target == "software developer" and "software" in normalized and "developer" in normalized:
            return True
    return False


@dataclass
class Evaluation:
    score: int
    assessment: str
    excluded: bool
    strong_matches: list[str]
    potential_gaps: list[str]
    concerns: list[str]
    uncertainties: list[str]

    def to_dict(self) -> dict:
        return asdict(self)


def evaluate(job: Job, profile: Profile, config: dict) -> Evaluation:
    score = 50
    matches: list[str] = []
    gaps: list[str] = []
    concerns: list[str] = []
    unknown: list[str] = []
    excluded = False
    title = job.title.lower()
    roles = [x.lower() for x in config["target_roles"]]
    if _matches_target_role(title, roles):
        score += 15; matches.append("Title is related to a configured target role.")
    else:
        gaps.append("Title is not clearly among the configured target roles.")
    seniority = job.seniority
    if seniority == "unknown":
        seniority = next((level for level in ("intern", "trainee", "graduate", "entry", "junior", "associate", "senior", "lead", "principal", "staff") if re.search(rf"\b{re.escape(level)}\b", title)), "unknown")
    if seniority in {"senior", "lead", "principal", "staff"}:
        score -= 45; excluded = True; concerns.append("The posting is explicitly senior-level while the profile has no professional employment experience.")
    elif seniority in {"junior", "graduate", "entry", "trainee", "intern", "associate"}:
        score += 12; matches.append("Seniority appears compatible with an early-career search.")
    elif seniority == "unknown":
        unknown.append("Seniority is not stated clearly.")
    for requirement in job.requirements:
        term = requirement.text.lower()
        if term in profile.skills:
            score += 8 if requirement.kind == "mandatory" else 4
            matches.append(f"Confirmed skill: {requirement.text}.")
        elif "master" in term:
            if requirement.kind == "mandatory":
                score -= 50; excluded = True; concerns.append("A Master's degree is explicitly required; the profile records a Bachelor's degree.")
            else:
                score -= 10; gaps.append("A Master's degree is mentioned but the profile records a Bachelor's degree.")
        elif "year" in term and "experience" in term:
            score -= 25 if requirement.kind == "mandatory" else 8
            concerns.append("Professional-experience requirement is not satisfied by projects or thesis work.")
        elif requirement.kind == "mandatory":
            score -= 18; gaps.append(f"Mandatory requirement not confirmed by profile: {requirement.text}.")
        elif requirement.kind in {"preferred", "useful"}:
            score -= 4; gaps.append(f"Preferred/useful requirement not confirmed: {requirement.text}.")
        else:
            unknown.append(f"Requirement needs review: {requirement.text}.")
    if job.metadata.get("description_is_snippet"):
        score -= 5
        unknown.append("The source provides only a description snippet; additional requirements may be unavailable.")
    elif not job.requirements:
        score -= 5
        unknown.append("The listing does not expose explicit requirements; technical qualifications could not be fully verified.")
    if job.arrangement == "remote":
        score += 6; matches.append("Germany-wide remote work is enabled in the configuration.")
    elif job.arrangement in {"hybrid", "onsite"}:
        if job.location and any(x.lower() in job.location.lower() for x in config["locations"]):
            score += 4; matches.append("Location is among configured preferences.")
        elif job.location:
            score -= 15; concerns.append("Hybrid/onsite location is outside the configured location list; commute needs review.")
        else:
            unknown.append("Hybrid/onsite posting has no stated location.")
    else:
        unknown.append("Work arrangement is unknown.")
    body = " ".join(filter(None, [job.description, job.qualifications])).lower()
    sponsorship_terms = ("must be authorized to work", "no sponsorship", "visa sponsorship", "requires sponsorship", "sponsorship is unavailable", "sponsorship unavailable")
    if any(term in body for term in sponsorship_terms):
        unknown.append("Work-authorization or sponsorship wording requires verification; no legal conclusion is made.")
    score = max(0, min(100, score))
    assessment = "rejected" if excluded else "recommended" if score >= 60 else "borderline"
    return Evaluation(score, assessment, excluded, matches, gaps, concerns, unknown)





