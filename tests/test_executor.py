from agent.executor import call_tool_structured
from agent.models import TaskNode


def test_call_tool_structured_marks_browser_error_strings_as_failures(monkeypatch):
    monkeypatch.setattr("agent.executor.call_tool", lambda *args, **kwargs: "Type error: Locator.clear: Element is not an input")

    result = call_tool_structured(
        TaskNode(
            node_id="1",
            objective="Type into the browser field",
            tool="browser_control",
            parameters={"action": "type", "text": "hello"},
            expected_outcome="Text is typed",
        )
    )

    assert result.status == "error"
    assert "Type error" in result.summary


def test_call_tool_structured_does_not_require_approval_for_send_message_success(monkeypatch):
    monkeypatch.setattr("agent.executor.call_tool", lambda *args, **kwargs: "Message sent to Rajaa via WhatsApp.")

    result = call_tool_structured(
        TaskNode(
            node_id="1",
            objective="Send a WhatsApp message",
            tool="send_message",
            parameters={"receiver": "Rajaa", "message_text": "Hii", "platform": "WhatsApp"},
            expected_outcome="Message is sent",
        )
    )

    assert result.status == "success"
    assert result.needs_approval is False
