from config import runtime as runtime_config
from config.runtime import AppConfig, LOG_DIR, ensure_runtime_dirs, validate_runtime_config


def test_runtime_dirs_can_be_created():
    ensure_runtime_dirs()
    assert LOG_DIR.exists()


def test_app_config_defaults_are_production_safe():
    config = AppConfig()
    assert config.environment == "production"
    assert config.log_level == "INFO"


def test_runtime_config_validation_accepts_known_defaults():
    issues = validate_runtime_config()
    assert isinstance(issues, list)


def test_load_config_reads_env_file(tmp_path, monkeypatch):
    env_file = tmp_path / ".env"
    env_file.write_text(
        "\n".join(
            [
                "BUDDY_GEMINI_API_KEY=test-gemini-key",
                "BUDDY_OS=windows",
                "BUDDY_LOG_LEVEL=debug",
                "BUDDY_ENV=production",
            ]
        ),
        encoding="utf-8",
    )
    monkeypatch.setattr(runtime_config, "ENV_FILE", env_file)
    monkeypatch.setattr(runtime_config, "CONFIG_FILE", tmp_path / "api_keys.json")
    monkeypatch.setattr(runtime_config, "EXAMPLE_CONFIG_FILE", tmp_path / "api_keys.example.json")
    monkeypatch.delenv("BUDDY_GEMINI_API_KEY", raising=False)
    monkeypatch.delenv("BUDDY_OS", raising=False)
    monkeypatch.delenv("BUDDY_LOG_LEVEL", raising=False)
    monkeypatch.delenv("BUDDY_ENV", raising=False)

    config = runtime_config.load_config()

    assert config.gemini_api_key == "test-gemini-key"
    assert config.os_system == "windows"
    assert config.log_level == "DEBUG"
    assert config.environment == "production"
