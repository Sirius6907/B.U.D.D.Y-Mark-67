import pytest
import time
from agent.kernel import ModelTelemetry, HealthCheck, CircuitBreaker

def test_model_telemetry():
    """Test telemetry calculations."""
    telemetry = ModelTelemetry(calls=10, errors=2, total_latency_ms=1000.0)
    assert telemetry.avg_latency_ms == 100.0
    assert telemetry.error_rate == 0.2

def test_model_telemetry_zero_calls():
    """Test telemetry calculations when no calls exist."""
    telemetry = ModelTelemetry(calls=0)
    assert telemetry.avg_latency_ms == 0.0
    assert telemetry.error_rate == 0.0

def test_health_check_defaults():
    """Test health check initialization."""
    health = HealthCheck()
    assert health.status == "unknown"
    assert not health.circuit_open
    assert health.fast_telemetry.calls == 0

def test_circuit_breaker_logic():
    """Test standard open/close circuit breaker logic."""
    cb = CircuitBreaker(threshold=3, reset_seconds=0.1)
    assert not cb.is_open

    cb.record_failure()
    cb.record_failure()
    assert not cb.is_open

    cb.record_failure()
    assert cb.is_open

    cb.record_success()
    assert not cb.is_open

def test_circuit_breaker_auto_reset():
    """Test circuit breaker auto-reset cooldown."""
    cb = CircuitBreaker(threshold=2, reset_seconds=0.1)
    cb.record_failure()
    cb.record_failure()
    assert cb.is_open

    # Wait for cooldown
    time.sleep(0.15)
    assert not cb.is_open
