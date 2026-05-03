"""Unit tests for runtime.browser.state — BrowserState capture and diff."""

import time

from runtime.browser.state import BrowserState, _compute_dom_hash, diff_states


class TestBrowserState:
    def test_frozen_dataclass(self):
        state = BrowserState(url="https://example.com", title="Example")
        assert state.url == "https://example.com"
        assert state.title == "Example"

    def test_default_values(self):
        state = BrowserState()
        assert state.url == ""
        assert state.title == ""
        assert state.tab_count == 0
        assert state.visible_text_snippet == ""
        assert state.dom_hash == ""
        assert state.load_state == "unknown"
        assert state.timestamp == 0.0

    def test_to_dict(self):
        state = BrowserState(url="https://google.com", title="Google", tab_count=3)
        d = state.to_dict()
        assert d["url"] == "https://google.com"
        assert d["title"] == "Google"
        assert d["tab_count"] == 3
        assert "dom_hash" in d

    def test_to_dict_truncates_snippet(self):
        long_text = "x" * 1000
        state = BrowserState(visible_text_snippet=long_text)
        d = state.to_dict()
        assert len(d["visible_text_snippet"]) == 200

    def test_compute_dom_hash_empty(self):
        assert _compute_dom_hash("") == ""

    def test_compute_dom_hash_deterministic(self):
        h1 = _compute_dom_hash("hello world")
        h2 = _compute_dom_hash("hello world")
        assert h1 == h2
        assert len(h1) == 12

    def test_compute_dom_hash_different_for_different_text(self):
        h1 = _compute_dom_hash("hello")
        h2 = _compute_dom_hash("world")
        assert h1 != h2


class TestDiffStates:
    def test_no_changes(self):
        s = BrowserState(url="https://a.com", title="A")
        diff = diff_states(s, s)
        assert diff == {}

    def test_url_change(self):
        before = BrowserState(url="https://a.com")
        after = BrowserState(url="https://b.com")
        diff = diff_states(before, after)
        assert "url" in diff
        assert diff["url"]["before"] == "https://a.com"
        assert diff["url"]["after"] == "https://b.com"

    def test_multiple_changes(self):
        before = BrowserState(url="https://a.com", title="A", tab_count=1)
        after = BrowserState(url="https://b.com", title="B", tab_count=2)
        diff = diff_states(before, after)
        assert "url" in diff
        assert "title" in diff
        assert "tab_count" in diff

    def test_dom_hash_change_detected(self):
        before = BrowserState(dom_hash="abc123")
        after = BrowserState(dom_hash="def456")
        diff = diff_states(before, after)
        assert "dom_hash" in diff

    def test_load_state_change(self):
        before = BrowserState(load_state="loading")
        after = BrowserState(load_state="domcontentloaded")
        diff = diff_states(before, after)
        assert "load_state" in diff
