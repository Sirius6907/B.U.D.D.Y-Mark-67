from runtime.gating.policy import evaluate_gate
from runtime.validation.files import validate_existing_path
from runtime.verification.files import verify_file_written


def test_high_risk_delete_requires_approval():
    decision = evaluate_gate("HIGH", dry_run=False)
    assert decision.status == "approval_required"


def test_validate_existing_path_returns_path_object(tmp_path):
    target = tmp_path / "note.txt"
    target.write_text("hello", encoding="utf-8")
    resolved = validate_existing_path(target)
    assert resolved == target


def test_verify_file_written_confirms_size(tmp_path):
    target = tmp_path / "note.txt"
    target.write_text("hello", encoding="utf-8")
    record = verify_file_written(target, expected_size=5)
    assert record.status == "verified"
    assert record.observed_state["size"] == 5
