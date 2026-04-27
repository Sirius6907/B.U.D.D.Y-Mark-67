import os
import tempfile
from pathlib import Path
import pytest
from unittest.mock import patch

from config.runtime import AppConfig


@pytest.fixture(autouse=True)
def mock_env_vars(monkeypatch):
    """Ensure tests don't accidentally hit production APIs unless explicitly configured."""
    monkeypatch.setenv("BUDDY_ENV", "test")
    monkeypatch.setenv("BUDDY_GEMINI_API_KEY", "test-key-123")
    monkeypatch.setenv("TELEGRAM_BOT_TOKEN", "test-bot-token")


@pytest.fixture
def test_config():
    """Provides a safe test configuration."""
    return AppConfig(
        gemini_api_key="test-key-123",
        telegram_bot_token="test-bot-token",
        os_system="windows",
        log_level="DEBUG",
        environment="test",
    )


@pytest.fixture
def tmp_buddy_dir():
    """Provides a temporary directory structure mimicking the Buddy runtime."""
    with tempfile.TemporaryDirectory() as tmp_dir:
        tmp_path = Path(tmp_dir)
        
        # Create subdirectories
        (tmp_path / "config").mkdir()
        (tmp_path / "memory").mkdir()
        (tmp_path / ".buddy_runtime" / "logs").mkdir(parents=True)
        
        with patch("config.runtime.BASE_DIR", tmp_path), \
             patch("config.runtime.CONFIG_DIR", tmp_path / "config"), \
             patch("config.runtime.RUNTIME_DIR", tmp_path / ".buddy_runtime"), \
             patch("config.runtime.LOG_DIR", tmp_path / ".buddy_runtime" / "logs"), \
             patch("memory.memory_manager.BASE_DIR", tmp_path), \
             patch("memory.memory_manager.MEMORY_DIR", tmp_path / "memory"), \
             patch("memory.memory_manager.SQLITE_PATH", tmp_path / "memory" / "memory.db"), \
             patch("memory.memory_manager.CHROMA_PATH", tmp_path / "memory" / "chroma_db"):
            yield tmp_path
