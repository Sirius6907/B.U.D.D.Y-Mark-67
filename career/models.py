from __future__ import annotations

from dataclasses import dataclass, field
from typing import Any


@dataclass
class CandidateProfile:
    name: str = ""
    target_roles: list[str] = field(default_factory=list)
    skills: list[str] = field(default_factory=list)
    links: dict[str, str] = field(default_factory=dict)


@dataclass
class PortfolioSnapshot:
    highlights: list[str] = field(default_factory=list)
    repos: list[dict[str, Any]] = field(default_factory=list)


@dataclass
class JobLead:
    title: str
    company: str
    location: str = ""
    url: str = ""


@dataclass
class JobAnalysis:
    lead: JobLead
    fit_score: float = 0.0
    gaps: list[str] = field(default_factory=list)


@dataclass
class ApplicationDraft:
    title: str
    summary: str
    attachments: list[str] = field(default_factory=list)


@dataclass
class OutreachDraft:
    recipient: str
    message: str


@dataclass
class ReferralThread:
    company: str
    contacts: list[str] = field(default_factory=list)


@dataclass
class CareerDraft:
    draft_id: str
    action_type: str
    title: str
    body: str
    target: str = ""
    metadata: dict[str, Any] = field(default_factory=dict)
