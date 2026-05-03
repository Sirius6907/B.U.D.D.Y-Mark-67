from runtime.contracts.models import RiskLevel, ToolResult, VerificationRecord
from runtime.results.builder import build_tool_result


def test_tool_result_contains_idempotency_and_state_contracts():
    result = build_tool_result(
        tool_name="file_read_metadata",
        operation="read_metadata",
        risk_level=RiskLevel.LOW,
        status="success",
        summary="metadata read",
        structured_data={"path": "C:/tmp/a.txt"},
        idempotent=True,
        preconditions=["path exists"],
        postconditions=["metadata returned"],
    )
    assert result["idempotent"] is True
    assert result["preconditions"] == ["path exists"]
    assert result["postconditions"] == ["metadata returned"]
    assert result["verification"]["status"] == "not_applicable"


def test_verification_record_defaults_to_not_applicable():
    record = VerificationRecord()
    assert record.status == "not_applicable"
    assert record.observed_state == {}
