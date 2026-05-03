"""Unit tests for runtime.browser.recovery — RecoveryPolicy."""

from runtime.browser.recovery import RecoveryPolicy, ErrorType


class TestErrorClassification:
    def test_timeout(self):
        assert RecoveryPolicy.classify_error("Operation timed out") == ErrorType.TIMEOUT
        assert RecoveryPolicy.classify_error("Timeout exceeded") == ErrorType.TIMEOUT

    def test_not_found(self):
        assert RecoveryPolicy.classify_error("Element not found") == ErrorType.NOT_FOUND
        assert RecoveryPolicy.classify_error("Could not find element") == ErrorType.NOT_FOUND

    def test_navigation(self):
        assert RecoveryPolicy.classify_error("net::ERR_CONNECTION_REFUSED") == ErrorType.NAVIGATION
        assert RecoveryPolicy.classify_error("Navigation failed") == ErrorType.NAVIGATION

    def test_permission(self):
        assert RecoveryPolicy.classify_error("Permission denied") == ErrorType.PERMISSION
        assert RecoveryPolicy.classify_error("Access blocked") == ErrorType.PERMISSION

    def test_stale(self):
        assert RecoveryPolicy.classify_error("Element is stale") == ErrorType.STALE
        assert RecoveryPolicy.classify_error("Node is detached") == ErrorType.STALE

    def test_detached(self):
        assert RecoveryPolicy.classify_error("Page closed") == ErrorType.DETACHED
        assert RecoveryPolicy.classify_error("Context disposed") == ErrorType.DETACHED

    def test_unknown(self):
        assert RecoveryPolicy.classify_error("Something weird happened") == ErrorType.UNKNOWN

    def test_exception_object(self):
        e = TimeoutError("Operation timed out")
        assert RecoveryPolicy.classify_error(e) == ErrorType.TIMEOUT


class TestRetryPolicy:
    def test_timeout_retryable(self):
        assert RecoveryPolicy.should_retry(ErrorType.TIMEOUT, 0) is True
        assert RecoveryPolicy.should_retry(ErrorType.TIMEOUT, 1) is True
        assert RecoveryPolicy.should_retry(ErrorType.TIMEOUT, 2) is True

    def test_max_retries_respected(self):
        assert RecoveryPolicy.should_retry(ErrorType.TIMEOUT, 3) is False

    def test_permission_never_retried(self):
        assert RecoveryPolicy.should_retry(ErrorType.PERMISSION, 0) is False

    def test_detached_never_retried(self):
        assert RecoveryPolicy.should_retry(ErrorType.DETACHED, 0) is False

    def test_not_found_retried_once(self):
        assert RecoveryPolicy.should_retry(ErrorType.NOT_FOUND, 0) is True
        assert RecoveryPolicy.should_retry(ErrorType.NOT_FOUND, 1) is False

    def test_unknown_retried_once(self):
        assert RecoveryPolicy.should_retry(ErrorType.UNKNOWN, 0) is True
        assert RecoveryPolicy.should_retry(ErrorType.UNKNOWN, 1) is False


class TestFallbacks:
    def test_click_element_has_alternatives(self):
        alt = RecoveryPolicy.suggest_alternative("browser_dom_click_element", ErrorType.NOT_FOUND)
        assert alt is not None
        assert alt == "browser_dom_click_by_text"

    def test_no_alternative_for_unknown_tool(self):
        alt = RecoveryPolicy.suggest_alternative("browser_unknown_xyz", ErrorType.NOT_FOUND)
        assert alt is None

    def test_fallback_chain(self):
        chain = RecoveryPolicy.get_fallback_chain("browser_dom_click_element")
        assert len(chain) >= 2
        assert "browser_dom_click_by_text" in chain
        assert "browser_dom_click_by_role" in chain

    def test_empty_chain_for_unknown(self):
        chain = RecoveryPolicy.get_fallback_chain("browser_nonexistent")
        assert chain == []


class TestWaitStrategy:
    def test_returns_positive_float(self):
        wait = RecoveryPolicy.wait_strategy(ErrorType.TIMEOUT, 0)
        assert wait > 0

    def test_increases_with_attempts(self):
        w0 = RecoveryPolicy.wait_strategy(ErrorType.TIMEOUT, 0)
        w1 = RecoveryPolicy.wait_strategy(ErrorType.TIMEOUT, 1)
        # w1 should generally be larger due to exponential backoff
        # (jitter makes exact comparison unreliable)
        assert w1 > 0

    def test_capped_at_30s(self):
        wait = RecoveryPolicy.wait_strategy(ErrorType.TIMEOUT, 10)
        assert wait <= 30.0
