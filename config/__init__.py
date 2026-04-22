from config.runtime import (
    AppConfig,
    CONFIG_FILE,
    EXAMPLE_CONFIG_FILE,
    LOG_DIR,
    RUNTIME_DIR,
    ensure_runtime_dirs,
    get_api_key,
    get_base_dir,
    get_os,
    load_config,
    save_config,
    update_config,
    validate_runtime_config,
)


def get_config() -> dict:
    return load_config().as_dict()


def is_windows() -> bool:
    return get_os() == "windows"


def is_mac() -> bool:
    return get_os() == "mac"


def is_linux() -> bool:
    return get_os() == "linux"
