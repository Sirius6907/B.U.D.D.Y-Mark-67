from __future__ import annotations

import re
import uuid

from agent.models import ActionResult
from career.approval_gate import CareerApprovalGate
from career.application_drafter import ApplicationDrafter
from career.github_manager import GitHubCareerManager
from career.job_search import JobSearchAgent
from career.linkedin_agent import LinkedInAgent
from career.models import CandidateProfile, CareerDraft
from career.referral_finder import ReferralFinder


class CareerOrchestrator:
    def __init__(self, memory=None, approval_callback=None):
        self.memory = memory
        self.approval_gate = CareerApprovalGate(approval_callback)
        self.github = GitHubCareerManager()
        self.linkedin = LinkedInAgent()
        self.jobs = JobSearchAgent()
        self.applications = ApplicationDrafter()
        self.referrals = ReferralFinder()
        self._drafts: dict[str, CareerDraft] = {}

    async def handle_command(self, text: str) -> ActionResult:
        lowered = text.lower()
        approval_match = re.search(r"approve draft ([a-f0-9-]+)", lowered)
        if approval_match:
            return await self._submit_draft(approval_match.group(1))

        if any(token in lowered for token in ("message", "referral", "apply", "post", "connect")):
            return await self._prepare_external_draft(text)
        if "github" in lowered:
            result = await self.github.audit_profile()
            candidate = self._candidate_profile()
            summary = result["summary"]
            observations = {
                **result,
                "stage": "review",
                "candidate_profile": candidate.__dict__,
            }
            self._write_heartbeat(
                current_workflow="career_github_review",
                pending_approval=False,
                active_draft_id="",
            )
            return ActionResult(status="success", summary=summary, observations=observations)
        if "linkedin" in lowered:
            result = await self.linkedin.get_profile_summary()
            self._write_heartbeat(
                current_workflow="career_linkedin_review",
                pending_approval=False,
                active_draft_id="",
            )
            return ActionResult(status="success", summary=result["summary"], observations={**result, "stage": "review"})
        if "job" in lowered:
            jobs = await self.jobs.search_jobs(text)
            candidate = self._candidate_profile()
            self._write_heartbeat(
                current_workflow="career_job_search",
                pending_approval=False,
                active_draft_id="",
            )
            return ActionResult(
                status="success",
                summary="Prepared LinkedIn job search draft.",
                observations={"jobs": jobs, "stage": "review", "candidate_profile": candidate.__dict__},
            )
        draft = await self.applications.generate_resume(text)
        self._write_heartbeat(
            current_workflow="career_resume_draft",
            pending_approval=False,
            active_draft_id="",
        )
        return ActionResult(status="success", summary=draft, observations={"mode": "draft", "stage": "review"})

    def _candidate_profile(self) -> CandidateProfile:
        profile = CandidateProfile()
        if self.memory is None or not hasattr(self.memory, "get_user_profile"):
            return profile
        data = self._parse_profile_markdown(self.memory.get_user_profile())
        profile.name = data.get("identity", {}).get("name", "")
        target_role = data.get("career_targets", {}).get("target_role")
        if target_role:
            profile.target_roles.append(target_role)
        skills = data.get("skills", {})
        profile.skills.extend(str(value) for value in skills.values() if value)
        profile.links = {
            key: value
            for key, value in data.get("platform_links", {}).items()
            if value
        }
        return profile

    async def _prepare_external_draft(self, text: str) -> ActionResult:
        lowered = text.lower()
        if "referral" in lowered:
            body = await self.referrals.draft_referral_message({"name": "recruiter"}, {"title": text})
            action_type = "referral_message"
            title = "Referral Outreach Draft"
        elif "linkedin" in lowered:
            request = await self.linkedin.draft_connection_request("contact", text)
            body = request["body"]
            action_type = "linkedin_message"
            title = request["title"]
        elif "apply" in lowered:
            body = await self.applications.generate_cover_letter(text, "Target Company")
            action_type = "job_application"
            title = "Application Draft"
        else:
            body = await self.applications.generate_resume(text)
            action_type = "career_action"
            title = "Career Draft"

        draft = CareerDraft(
            draft_id=str(uuid.uuid4()),
            action_type=action_type,
            title=title,
            body=body,
            target=text,
            metadata={"stage": "review"},
        )
        self._drafts[draft.draft_id] = draft
        self._write_heartbeat(
            current_workflow=f"career_{action_type}",
            pending_approval=True,
            active_draft_id=draft.draft_id,
        )
        return ActionResult(
            status="pending_approval",
            summary=f"Draft ready for approval: {draft.title}",
            needs_approval=True,
            observations={
                "stage": "review",
                "draft_id": draft.draft_id,
                "draft": draft.__dict__,
                "candidate_profile": self._candidate_profile().__dict__,
            },
        )

    async def _submit_draft(self, draft_id: str) -> ActionResult:
        draft = self._drafts.get(draft_id)
        if draft is None:
            return ActionResult(status="error", summary=f"Unknown draft: {draft_id}", retryable=False)
        approved = await self.approval_gate.draft_and_approve(
            draft.action_type,
            {"title": draft.title, "body": draft.body, "summary": draft.body},
        )
        if not approved:
            self._write_heartbeat(
                current_workflow=f"career_{draft.action_type}",
                pending_approval=True,
                active_draft_id=draft.draft_id,
            )
            return ActionResult(
                status="pending_approval",
                summary=f"Approval still required for {draft.title}",
                needs_approval=True,
                observations={"stage": "review", "draft_id": draft.draft_id, "draft": draft.__dict__},
            )
        self._drafts.pop(draft_id, None)
        self._write_heartbeat(
            current_workflow=f"career_{draft.action_type}",
            pending_approval=False,
            active_draft_id="",
        )
        return ActionResult(
            status="success",
            summary=f"Approved and submitted: {draft.title}",
            observations={"stage": "submit", "draft_id": draft_id, "draft": draft.__dict__},
        )

    def _write_heartbeat(self, **status) -> None:
        if self.memory is not None and hasattr(self.memory, "update_heartbeat"):
            self.memory.update_heartbeat(status)

    @staticmethod
    def _parse_profile_markdown(content: str) -> dict[str, dict[str, str]]:
        data: dict[str, dict[str, str]] = {}
        current_section = ""
        for raw_line in content.splitlines():
            line = raw_line.strip()
            if line.startswith("## "):
                current_section = line[3:].strip().lower().replace(" ", "_")
                data.setdefault(current_section, {})
                continue
            if current_section and line.startswith("- ") and ":" in line:
                key, value = line[2:].split(":", 1)
                data[current_section][key.strip()] = value.strip()
        return data
