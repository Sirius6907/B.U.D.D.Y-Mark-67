"""Unit tests for runtime.browser.engine — BrowserEngine."""

from unittest.mock import MagicMock, patch
import pytest

from runtime.browser.engine import BrowserEngine
from runtime.contracts.models import RiskLevel


class TestBrowserEngineSingleton:
    def test_singleton(self):
        """BrowserEngine must be a singleton."""
        # Reset singleton for test isolation
        BrowserEngine._instance = None
        e1 = BrowserEngine()
        e2 = BrowserEngine()
        assert e1 is e2
        # Cleanup
        BrowserEngine._instance = None


class TestBrowserEngineErrorResult:
    def test_error_result_structure(self):
        """_error_result must return a valid ToolResult dict."""
        BrowserEngine._instance = None
        engine = BrowserEngine()
        result = engine._error_result(
            "browser_nav_navigate_to_url",
            "navigate",
            RuntimeError("Test error"),
        )
        assert result["tool_name"] == "browser_nav_navigate_to_url"
        assert result["operation"] == "navigate"
        assert result["status"] == "error"
        assert "error_type" in result["structured_data"]
        assert "retryable" in result["structured_data"]
        assert "alternative_tool" in result["structured_data"]
        assert "wait_seconds" in result["structured_data"]
        BrowserEngine._instance = None

    def test_error_result_classifies_timeout(self):
        BrowserEngine._instance = None
        engine = BrowserEngine()
        result = engine._error_result(
            "browser_nav_navigate_to_url",
            "navigate",
            TimeoutError("Connection timed out"),
        )
        assert result["structured_data"]["error_type"] == "timeout"
        assert result["structured_data"]["retryable"] is True
        BrowserEngine._instance = None

    def test_error_result_classifies_permission(self):
        BrowserEngine._instance = None
        engine = BrowserEngine()
        result = engine._error_result(
            "browser_auth_login_with_credentials",
            "login",
            PermissionError("Access denied"),
        )
        assert result["structured_data"]["error_type"] == "permission"
        assert result["structured_data"]["retryable"] is False
        BrowserEngine._instance = None


class TestBrowserEngineWithMockedSession:
    """Test engine methods with a mocked _BrowserSession."""

    @pytest.fixture(autouse=True)
    def setup_engine(self):
        BrowserEngine._instance = None
        self.engine = BrowserEngine()
        yield
        BrowserEngine._instance = None

    def _mock_session(self):
        sess = MagicMock()
        sess.run = MagicMock(side_effect=lambda coro: coro)
        sess.get_url = MagicMock(return_value="https://example.com")
        sess.get_text = MagicMock(return_value="Example page text")
        sess._page = MagicMock()
        sess._page.is_closed = MagicMock(return_value=False)
        sess._page.context = MagicMock()
        sess._page.context.pages = [sess._page]
        return sess

    @patch("runtime.browser.engine._get_session")
    def test_navigate_returns_tool_result(self, mock_get):
        sess = self._mock_session()
        sess.go_to = MagicMock(return_value="Opened: https://example.com")
        mock_get.return_value = sess

        result = self.engine.navigate("https://example.com")

        assert result["tool_name"] == "browser_nav_navigate_to_url"
        assert result["operation"] == "navigate"
        assert result["status"] == "success"
        assert "url_requested" in result["structured_data"]

    @patch("runtime.browser.engine._get_session")
    def test_search_returns_tool_result(self, mock_get):
        sess = self._mock_session()
        sess.search = MagicMock(return_value="Opened: https://google.com/search?q=test")
        mock_get.return_value = sess

        result = self.engine.search("test", "google")

        assert result["tool_name"] == "browser_nav_search_google"
        assert result["structured_data"]["query"] == "test"

    @patch("runtime.browser.engine._get_session")
    def test_click_returns_tool_result(self, mock_get):
        sess = self._mock_session()
        sess.click = MagicMock(return_value="Clicked text: 'Sign In'")
        mock_get.return_value = sess

        result = self.engine.click(text="Sign In")

        assert result["tool_name"] == "browser_dom_click_by_text"
        assert result["status"] == "success"

    @patch("runtime.browser.engine._get_session")
    def test_get_current_url_returns_tool_result(self, mock_get):
        sess = self._mock_session()
        mock_get.return_value = sess

        result = self.engine.get_current_url()

        assert result["tool_name"] == "browser_nav_get_current_url"
        assert result["structured_data"]["url"] == "https://example.com"
        assert result["idempotent"] is True

    @patch("runtime.browser.engine._get_session")
    def test_screenshot_returns_tool_result(self, mock_get):
        sess = self._mock_session()
        sess.screenshot = MagicMock(return_value="Screenshot saved: /tmp/test.png")
        mock_get.return_value = sess

        result = self.engine.screenshot("/tmp/test.png")

        assert result["tool_name"] == "browser_media_take_screenshot"
        assert result["status"] == "success"

    @patch("runtime.browser.engine._get_session")
    def test_navigate_error_includes_recovery_metadata(self, mock_get):
        sess = self._mock_session()
        sess.go_to = MagicMock(side_effect=TimeoutError("Connection timed out"))
        # capture_state also needs to work
        sess.get_url = MagicMock(return_value="about:blank")
        sess.get_text = MagicMock(return_value="")
        mock_get.return_value = sess

        result = self.engine.navigate("https://example.com")

        assert result["status"] == "error"
        assert result["structured_data"]["error_type"] == "timeout"
        assert result["structured_data"]["retryable"] is True
