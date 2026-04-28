from __future__ import annotations

from pathlib import Path

from memory.profiles import ProfileManager


def test_profile_manager_creates_canonical_files(tmp_path: Path):
    manager = ProfileManager(tmp_path)

    assert manager.user_path.exists()
    assert manager.soul_path.exists()
    assert manager.heartbeat_path.exists()


def test_profile_manager_updates_user_profile_by_section(tmp_path: Path):
    manager = ProfileManager(tmp_path)

    manager.update_user("identity", "name", "Chandan Kumar Behera")
    manager.update_user("career_targets", "target_role", "Software Engineer")

    content = manager.load_user_context()

    assert "## Identity" in content
    assert "- name: Chandan Kumar Behera" in content
    assert "## Career Targets" in content
    assert "- target_role: Software Engineer" in content
