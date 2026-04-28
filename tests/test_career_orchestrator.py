from __future__ import annotations

import pytest

from career.orchestrator import CareerOrchestrator
from memory.profiles import ProfileManager


class _Memory:
    def __init__(self, tmp_path):
        self.profile_manager = ProfileManager(tmp_path / "profiles")
        self.heartbeat_updates: list[dict] = []

    def get_user_profile(self) -> str:
        return self.profile_manager.load_user_context()

    def update_heartbeat(self, status: dict) -> None:
        self.heartbeat_updates.append(dict(status))
        self.profile_manager.write_heartbeat(status)


@pytest.mark.asyncio
async def test_career_orchestrator_uses_seeded_profile_for_review(tmp_path):
    memory = _Memory(tmp_path)
    memory.profile_manager.update_user("identity", "name", "Chandan Kumar Behera")
    memory.profile_manager.update_user("career_targets", "target_role", "Software Engineer")

    orchestrator = CareerOrchestrator(memory=memory)
    result = await orchestrator.handle_command("analyze my github profile")

    assert result.status == "success"
    assert result.observations["stage"] == "review"
    assert result.observations["candidate_profile"]["name"] == "Chandan Kumar Behera"
    assert "Software Engineer" in result.observations["candidate_profile"]["target_roles"]


@pytest.mark.asyncio
async def test_career_orchestrator_requires_draft_then_approval_for_external_actions(tmp_path):
    memory = _Memory(tmp_path)
    memory.profile_manager.update_user("identity", "name", "Chandan Kumar Behera")
    orchestrator = CareerOrchestrator(memory=memory, approval_callback=lambda _: True)

    draft_result = await orchestrator.handle_command("send a linkedin referral message to a recruiter")

    assert draft_result.status == "pending_approval"
    assert draft_result.needs_approval is True
    assert draft_result.observations["stage"] == "review"
    draft_id = draft_result.observations["draft_id"]
    assert memory.heartbeat_updates[-1]["pending_approval"] is True

    submit_result = await orchestrator.handle_command(f"approve draft {draft_id}")

    assert submit_result.status == "success"
    assert submit_result.observations["stage"] == "submit"
    assert memory.heartbeat_updates[-1]["pending_approval"] is False
