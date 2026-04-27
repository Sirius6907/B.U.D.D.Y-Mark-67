from __future__ import annotations

import json
import os
import sys
import threading
from dataclasses import asdict, dataclass
from pathlib import Path

__all__ = [
    "AppConfig",
    "CONFIG_FILE",
    "EXAMPLE_CONFIG_FILE",
    "LOG_DIR",
    "RUNTIME_DIR",
    "ensure_runtime_dirs",
    "get_api_key",
    "get_base_dir",
    "get_os",
    "load_config",
    "save_config",
    "update_config",
    "validate_runtime_config",
]


def get_base_dir() -> Path:
    """Get the absolute base directory of the project robustly."""
    if getattr(sys, "frozen", False):
        return Path(sys.executable).parent.resolve()
    return Path(__file__).resolve().parent.parent


BASE_DIR = get_base_dir()
CONFIG_DIR = BASE_DIR / "config"
CONFIG_FILE = CONFIG_DIR / "api_keys.json"
EXAMPLE_CONFIG_FILE = CONFIG_DIR / "api_keys.example.json"
ENV_FILE = BASE_DIR / ".env"
RUNTIME_DIR = BASE_DIR / ".buddy_runtime"
LOG_DIR = RUNTIME_DIR / "logs"


@dataclass(slots=True)
class AppConfig:
    gemini_api_key: str = ""
    telegram_bot_token: str = ""
    telegram_username: str = ""
    telegram_user_id: str = ""
    os_system: str = "windows"
    log_level: str = "INFO"
    environment: str = "production"

    def as_dict(self) -> dict:
        return asdict(self)


class GeminiKeyRotator:
    """Thread-safe round-robin rotator for Gemini API keys."""

    _instance = None
    _lock = threading.Lock()

    def __new__(cls):
        if cls._instance is None:
            with cls._lock:
                if cls._instance is None:
                    cls._instance = super().__new__(cls)
                    cls._instance._keys = []
                    cls._instance._index = 0
                    cls._instance._rotation_lock = threading.Lock()
        return cls._instance

    def set_keys(self, keys: list[str]) -> None:
        with self._rotation_lock:
            # Only reset index if the keys actually changed significantly
            clean_keys = [k.strip() for k in keys if k.strip()]
            if clean_keys != self._keys:
                self._keys = clean_keys
                self._index = 0

    def get_next_key(self) -> str | None:
        with self._rotation_lock:
            if not self._keys:
                return None
            key = self._keys[self._index]
            self._index = (self._index + 1) % len(self._keys)
            return key


_rotator = GeminiKeyRotator()


def ensure_runtime_dirs() -> None:
    CONFIG_DIR.mkdir(parents=True, exist_ok=True)
    RUNTIME_DIR.mkdir(parents=True, exist_ok=True)
    LOG_DIR.mkdir(parents=True, exist_ok=True)


def _read_json_file(path: Path, *, strict: bool = False) -> dict:
    if not path.exists():
        return {}
    try:
        return json.loads(path.read_text(encoding="utf-8"))
    except (OSError, json.JSONDecodeError) as exc:
        if strict:
            raise RuntimeError(f"Unable to read JSON config file: {path}") from exc
        return {}


def load_env_file(path: Path | None = None) -> dict[str, str]:
    env_path = path or ENV_FILE
    if not env_path.exists():
        return {}

    values: dict[str, str] = {}
    for raw_line in env_path.read_text(encoding="utf-8").splitlines():
        line = raw_line.strip()
        if not line or line.startswith("#") or "=" not in line:
            continue
        key, value = line.split("=", 1)
        key = key.strip()
        value = value.strip().strip("'\"")
        if key:
            values[key] = value
    return values


def load_config() -> AppConfig:
    ensure_runtime_dirs()
    file_data = _read_json_file(CONFIG_FILE, strict=True)
    example_data = _read_json_file(EXAMPLE_CONFIG_FILE)
    env_data = load_env_file()
    merged = {**example_data, **file_data}

    gemini_api_key = os.environ.get(
        "BUDDY_GEMINI_API_KEY",
        env_data.get("BUDDY_GEMINI_API_KEY", merged.get("gemini_api_key", "")),
    ).strip()
    telegram_bot_token = os.environ.get(
        "TELEGRAM_BOT_TOKEN",
        env_data.get("TELEGRAM_BOT_TOKEN", merged.get("telegram_bot_token", "")),
    ).strip()
    telegram_username = os.environ.get(
        "TELEGRAM_USERNAME",
        env_data.get("TELEGRAM_USERNAME", merged.get("telegram_username", "")),
    ).strip()
    telegram_user_id = os.environ.get(
        "TELEGRAM_USER_ID",
        env_data.get("TELEGRAM_USER_ID", merged.get("telegram_user_id", "")),
    ).strip()
    os_system = os.environ.get(
        "BUDDY_OS",
        env_data.get("BUDDY_OS", merged.get("os_system", "windows")),
    ).strip().lower() or "windows"
    log_level = os.environ.get(
        "BUDDY_LOG_LEVEL",
        env_data.get("BUDDY_LOG_LEVEL", merged.get("log_level", "INFO")),
    ).strip().upper() or "INFO"
    environment = os.environ.get(
        "BUDDY_ENV",
        env_data.get("BUDDY_ENV", merged.get("environment", "production")),
    ).strip().lower() or "production"

    return AppConfig(
        gemini_api_key=gemini_api_key or "",
        telegram_bot_token=telegram_bot_token or "",
        telegram_username=telegram_username or "",
        telegram_user_id=telegram_user_id or "",
        os_system=os_system,
        log_level=log_level,
        environment=environment,
    )


def save_config(config: AppConfig) -> None:
    ensure_runtime_dirs()
    env_values = load_env_file()
    env_values.update(
        {
            "BUDDY_GEMINI_API_KEY": config.gemini_api_key,
            "TELEGRAM_BOT_TOKEN": config.telegram_bot_token,
            "TELEGRAM_USERNAME": config.telegram_username,
            "TELEGRAM_USER_ID": str(config.telegram_user_id),
            "BUDDY_OS": config.os_system,
            "BUDDY_LOG_LEVEL": config.log_level,
            "BUDDY_ENV": config.environment,
        }
    )
    lines = [f"{key}={value}" for key, value in sorted(env_values.items()) if value != ""]
    ENV_FILE.write_text("\n".join(lines) + ("\n" if lines else ""), encoding="utf-8")


def update_config(**kwargs) -> AppConfig:
    config = load_config()
    for key, value in kwargs.items():
        if hasattr(config, key) and value is not None:
            setattr(config, key, value)
    save_config(config)
    return config


def get_api_key(required: bool = False) -> str:
    config = load_config()
    keys_str = config.gemini_api_key
    
    # Update rotator with current keys from config
    keys = [k.strip() for k in keys_str.split(",") if k.strip()]
    _rotator.set_keys(keys)
    
    key = _rotator.get_next_key()
    
    if required and not key:
        raise RuntimeError(
            "Gemini API key is not configured. Set BUDDY_GEMINI_API_KEY (comma-separated for rotation) or use config/api_keys.json."
        )
    return key or ""


def get_os() -> str:
    return load_config().os_system


def validate_runtime_config() -> list[str]:
    config = load_config()
    issues: list[str] = []
    if config.os_system not in {"windows", "mac", "linux"}:
        issues.append(f"Unsupported os_system '{config.os_system}' in config.")
    if config.log_level not in {"DEBUG", "INFO", "WARNING", "ERROR", "CRITICAL"}:
        issues.append(f"Unsupported log level '{config.log_level}'.")
    if not config.gemini_api_key:
        issues.append(
            "Gemini API key not configured. "
            "Set BUDDY_GEMINI_API_KEY in .env or config/api_keys.json."
        )
    if not ENV_FILE.exists():
        issues.append(
            f".env file not found at {ENV_FILE}. "
            "Create it with BUDDY_GEMINI_API_KEY=<your-key>."
        )
    return issues
