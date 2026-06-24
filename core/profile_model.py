"""Runner profile: structured data model + helpers.

Design choice (Head of Data 102):
- STORED structured (nested objects) so the chat agent can patch single
  fields later ("race moved to November" -> goal.race_date).
- DISPLAYED flat, like the wireframe's Marie card (see `to_display_rows`).
- One thing the wireframe lumps together we deliberately split: the
  "3 sessions/week max" cap is `availability`, the "right-knee niggle" is a
  `constraint`. They feed the planner differently (structure vs. intensity).
"""
from __future__ import annotations

import re
from datetime import date
from typing import Literal, Optional

from pydantic import BaseModel, Field, field_validator

DAYS = ["Mon", "Tue", "Wed", "Thu", "Fri", "Sat", "Sun"]
GENDERS = ["female", "male", "other", "prefer_not_to_say"]
CONSTRAINT_KINDS = ["injury", "preference", "other"]
SEVERITIES = ["mild", "moderate", "severe"]

_TIME_RE = re.compile(r"^\d{1,2}:\d{2}(:\d{2})?$")  # MM:SS or HH:MM:SS


class Identity(BaseModel):
    first_name: str = ""
    city: Optional[str] = None
    gender: Optional[str] = None
    @field_validator("gender")
    @classmethod
    def _gender_known(cls, v: Optional[str]) -> Optional[str]:
        if v in (None, ""):
            return None
        v = v.strip().lower()          # normalise "Female" -> "female"
        if v not in GENDERS:
            raise ValueError(f"gender must be one of {GENDERS}")
        return v

class Goal(BaseModel):
    race_type: str = ""                       # "10k", "half-marathon", ...
    target_distance_km: Optional[float] = Field(default=None, ge=0)
    target_time: Optional[str] = None         # "00:50:00" or "50:00"
    race_date: Optional[date] = None
    horizon_weeks: Optional[int] = Field(default=None, ge=1, le=104)

    @field_validator("target_time")
    @classmethod
    def _time_format(cls, v: Optional[str]) -> Optional[str]:
        if v in (None, ""):
            return None
        if not _TIME_RE.match(v):
            raise ValueError("target_time must look like MM:SS or HH:MM:SS")
        return v


class Availability(BaseModel):
    sessions_per_week: int = Field(default=3, ge=1, le=14)
    preferred_days: list[str] = Field(default_factory=list)
    max_session_min: Optional[int] = Field(default=None, ge=10, le=600)

    @field_validator("preferred_days")
    @classmethod
    def _days_known(cls, v: list[str]) -> list[str]:
        bad = [d for d in v if d not in DAYS]
        if bad:
            raise ValueError(f"unknown day(s): {bad}")
        return v


class Constraint(BaseModel):
    kind: Literal["injury", "preference", "other"] = "other"
    area: Optional[str] = None                # "right knee"
    note: str = ""                            # "niggle"
    severity: Optional[str] = None            # mild | moderate | severe
    active: bool = True

    @field_validator("severity")
    @classmethod
    def _severity_known(cls, v: Optional[str]) -> Optional[str]:
        if v in (None, ""):
            return None
        if v not in SEVERITIES:
            raise ValueError(f"severity must be one of {SEVERITIES}")
        return v


class RunnerProfile(BaseModel):
    identity: Identity = Field(default_factory=Identity)
    goal: Goal = Field(default_factory=Goal)
    availability: Availability = Field(default_factory=Availability)
    constraints: list[Constraint] = Field(default_factory=list)
    notes: str = ""


# --------------------------------------------------------------------------- #
# Helpers
# --------------------------------------------------------------------------- #
def default_profile() -> RunnerProfile:
    """Seed used on first launch (Day 1 hard-coded runner)."""
    return RunnerProfile(
        identity=Identity(first_name="Marie", city="Lyon", gender="female"),
        goal=Goal(race_type="10k", target_distance_km=10, target_time="00:50:00", horizon_weeks=10),
        availability=Availability(
            sessions_per_week=3, preferred_days=["Tue", "Thu", "Sat"]
        ),
        constraints=[
            Constraint(kind="injury", area="right knee", note="niggle",
                       severity="mild", active=True)
        ],
    )


def _goal_phrase(g: Goal) -> str:
    bits = []
    if g.race_type:
        bits.append(g.race_type)
    if g.target_time:
        bits.append(f"under {g.target_time}")
    if g.horizon_weeks:
        bits.append(f"in {g.horizon_weeks} weeks")
    elif g.race_date:
        bits.append(f"by {g.race_date.isoformat()}")
    return ", ".join(bits) or "—"


def _availability_phrase(p: RunnerProfile) -> str:
    # sessions/week used to be crammed into constraints — moved it here
    parts = [f"{p.availability.sessions_per_week} sessions/week"]
    if p.availability.preferred_days:
        parts.append(", ".join(p.availability.preferred_days))
    if p.availability.max_session_min:
        parts.append(f"≤ {p.availability.max_session_min} min/session")
    return ", ".join(parts)


def _constraints_phrase(p: RunnerProfile) -> str:
    # each active injury on its own line so multiple injuries don't pile up
    parts = []
    for c in p.constraints:
        if not c.active:
            continue
        label = f"{c.area}: {c.note}" if c.area and c.note else (c.area or c.note)
        if label:
            parts.append(label.capitalize())
    return "<br>".join(parts) if parts else "—"


def to_display_rows(p: RunnerProfile) -> list[tuple[str, str]]:
    """Flatten the structured profile into the wireframe's label/value rows."""
    return [
        ("First name", p.identity.first_name or "—"),
        ("City", p.identity.city or "—"),
        ("Gender", p.identity.gender or "—"),
        ("Goals", _goal_phrase(p.goal)),
        ("Availability", _availability_phrase(p)),
        ("Constraints & injuries", _constraints_phrase(p)),
    ]


def _constraints_phrase_text(p: RunnerProfile) -> str:
    parts = []
    for c in p.constraints:
        if not c.active:
            continue
        label = f"{c.area}: {c.note}" if c.area and c.note else (c.area or c.note)
        if label:
            parts.append(label.capitalize())
    return "\n".join(parts) if parts else "None"


def profile_to_prompt(p: RunnerProfile) -> str:
    """Serialize the coaching-relevant profile for the LLM context."""
    lines = ["RUNNER PROFILE", f"- Name: {p.identity.first_name or 'unknown'}"]
    if p.identity.city:
        lines.append(f"- City: {p.identity.city}")
    if p.identity.gender:
        lines.append(f"- Gender: {p.identity.gender}")
    lines.append(f"- Goal: {_goal_phrase(p.goal)}")
    lines.append(
        f"- Availability: {p.availability.sessions_per_week} sessions/week"
        + (
            f", preferred {', '.join(p.availability.preferred_days)}"
            if p.availability.preferred_days
            else ""
        )
        + (
            f", ≤ {p.availability.max_session_min} min/session"
            if p.availability.max_session_min
            else ""
        )
    )
    active = [c for c in p.constraints if c.active]
    if active:
        lines.append("- Constraints / injuries:")
        for c in active:
            where = f" ({c.area})" if c.area else ""
            lines.append(f"    • [{c.kind}] {c.note}{where}")
    if p.notes:
        lines.append(f"- Notes: {p.notes}")
    return "\n".join(lines)