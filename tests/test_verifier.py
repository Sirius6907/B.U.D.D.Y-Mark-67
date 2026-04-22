import shutil
from pathlib import Path

from agent.models import ActionResult
from agent.verifier import VerificationEngine, verify_file_write


def _make_test_dir(name: str) -> Path:
    base = Path.cwd() / "tests" / ".tmp_verifier" / name
    if base.exists():
        shutil.rmtree(base)
    base.mkdir(parents=True, exist_ok=True)
    return base


def test_verify_file_write_passes_when_file_exists():
    temp_dir = _make_test_dir("exists")
    target = temp_dir / "notes.txt"
    target.write_text("hello", encoding="utf-8")
    result = ActionResult(
        status="success",
        summary="wrote file",
        changed_state={"path": str(target)},
    )

    verified = verify_file_write(result)
    assert verified is True
    shutil.rmtree(temp_dir)


def test_verification_engine_rejects_missing_written_file():
    temp_dir = _make_test_dir("missing")
    target = temp_dir / "missing.txt"
    result = ActionResult(
        status="success",
        summary="wrote file",
        changed_state={"path": str(target)},
    )

    from agent.models import RiskTier, TaskNode

    node = TaskNode(
        node_id="write-file",
        objective="Write file",
        tool="file_controller",
        parameters={"action": "write", "path": str(target.parent), "name": target.name},
        expected_outcome="File exists",
        risk_tier=RiskTier.TIER_2,
    )
    verified, critique = VerificationEngine().verify_sync(node, result)
    assert verified is False
    assert "could not be verified" in critique.lower()
    shutil.rmtree(temp_dir)
