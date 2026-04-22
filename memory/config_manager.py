from config import CONFIG_FILE, ensure_runtime_dirs, get_api_key, load_config, update_config


def ensure_config_dir() -> None:
    ensure_runtime_dirs()


def config_exists() -> bool:
    return CONFIG_FILE.exists()


def save_api_keys(gemini_api_key: str) -> None:
    update_config(gemini_api_key=gemini_api_key.strip())


def load_api_keys() -> dict:
    return load_config().as_dict()


def get_gemini_key() -> str | None:
    return get_api_key(required=False) or None


def is_configured() -> bool:
    key = get_gemini_key()
    return bool(key and len(key) > 15)
