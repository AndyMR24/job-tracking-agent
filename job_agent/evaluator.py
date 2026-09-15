"""Explainable, deliberately conservative job-fit evaluation."""
from __future__ import annotations

from dataclasses import asdict, dataclass

from .models import Job
from .profile import Profile


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
    if any(role in title or any(word in title for word in role.split()) for role in roles):
        score += 15; matches.append("Title is related to a configured target role.")
    else:
        gaps.append("Title is not clearly among the configured target roles.")
    seniority = job.seniority
    if seniority == "unknown":
        seniority = next((level for level in ("intern", "trainee", "graduate", "entry", "junior", "associate", "senior", "lead", "principal", "staff") if level in title), "unknown")
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
    if "must be authorized to work" in body or "no sponsorship" in body:
        unknown.append("Work-authorization wording requires verification; no legal conclusion is made.")
    score = max(0, min(100, score))
    assessment = "rejected" if excluded else "recommended" if score >= 60 else "borderline"
    return Evaluation(score, assessment, excluded, matches, gaps, concerns, unknown)
