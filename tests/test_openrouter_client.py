from agent.openrouter_client import _extract_message_content


def test_extract_message_content_handles_string():
    assert _extract_message_content(" hello ") == "hello"


def test_extract_message_content_handles_openrouter_content_blocks():
    content = [
        {"type": "text", "text": "First line"},
        {"type": "text", "text": "Second line"},
    ]

    assert _extract_message_content(content) == "First line\nSecond line"


def test_extract_message_content_handles_none():
    assert _extract_message_content(None) == ""
