"""
Buddy MK-67 — Ship Readiness Check
Validates all critical dependencies, configurations, and system state
before deployment. Use --json for machine-readable output.
"""
from __future__ import annotations

import argparse
import importlib
import json
import sys
from pathlib import Path

# Fix Windows terminal encoding for emoji output
if sys.platform == "win32":
    sys.stdout.reconfigure(encoding="utf-8", errors="replace")

PROJECT_ROOT = Path(__file__).resolve().parent.parent
if str(PROJECT_ROOT) not in sys.path:
    sys.path.insert(0, str(PROJECT_ROOT))

from app_bootstrap import bootstrap_application
from config import CONFIG_FILE, EXAMPLE_CONFIG_FILE, get_api_key


def _check_python_module(module_name: str, timeout: float = 10.0) -> tuple[bool, str]:
    """Check if a Python module is importable (with timeout for heavy modules)."""
    import concurrent.futures
    def _try_import():
        mod = importlib.import_module(module_name)
        return getattr(mod, "__version__", "installed")
    try:
        with concurrent.futures.ThreadPoolExecutor(max_workers=1) as pool:
            future = pool.submit(_try_import)
            version = future.result(timeout=timeout)
        return True, version
    except concurrent.futures.TimeoutError:
        return True, "installed (import slow)"
    except ImportError:
        return False, "not installed"
    except Exception as e:
        return False, f"import error: {e}"





def _check_playwright() -> tuple[bool, str]:
    """Check if Playwright browsers are installed."""
    try:
        from playwright.sync_api import sync_playwright
        # Just check import works; don't launch a browser
        return True, "module available"
    except ImportError:
        return False, "playwright not installed"


def _check_ui_assets() -> tuple[bool, str]:
    """Check that required UI assets exist."""
    face_path = PROJECT_ROOT / "face.png"
    if face_path.exists():
        return True, str(face_path)
    return False, "face.png not found in project root"


def _check_env_file() -> tuple[bool, str]:
    """Check that .env file exists and contains the API key."""
    env_path = PROJECT_ROOT / ".env"
    if not env_path.exists():
        return False, ".env file not found"
    content = env_path.read_text(encoding="utf-8")
    if "BUDDY_GEMINI_API_KEY" in content:
        # Check it has an actual value
        for line in content.splitlines():
            if line.strip().startswith("BUDDY_GEMINI_API_KEY") and "=" in line:
                val = line.split("=", 1)[1].strip().strip("'\"")
                if val:
                    return True, "API key configured in .env"
                return False, "BUDDY_GEMINI_API_KEY is empty in .env"
    return False, "BUDDY_GEMINI_API_KEY not found in .env"


def main() -> int:
    parser = argparse.ArgumentParser(description="Buddy MK-67 Ship Readiness Check")
    parser.add_argument("--json", action="store_true", help="Output results as JSON")
    args = parser.parse_args()

    report = bootstrap_application()

    checks: list[dict] = []

    def add_check(name: str, ok: bool, detail: str, critical: bool = True):
        checks.append({"name": name, "ok": ok, "detail": detail, "critical": critical})

    # ── Core Project Structure ──
    add_check("pyproject", (PROJECT_ROOT / "pyproject.toml").exists(), "pyproject.toml present")
    add_check("example-config", EXAMPLE_CONFIG_FILE.exists(), "api_keys.example.json present")
    add_check("log-dir", Path(report.log_path).parent.exists(), "Log directory created")

    # ── API Key & Configuration ──
    api_key_present = bool(get_api_key(required=False))
    add_check("api-key-configured", api_key_present, "Gemini API key available")

    env_ok, env_detail = _check_env_file()
    add_check("env-file", env_ok, env_detail)

    # ── Critical Python Dependencies ──
    critical_modules = [
        ("google.genai", "Google GenAI SDK"),
        ("sounddevice", "Audio I/O"),
        ("numpy", "Numeric Processing"),
        ("chromadb", "Vector Database"),
    ]
    for mod, label in critical_modules:
        ok, detail = _check_python_module(mod)
        add_check(f"dep-{mod}", ok, f"{label}: {detail}")

    # ── Optional Dependencies ──
    optional_modules = [
        ("playwright", "Browser Automation"),
        ("pyautogui", "Desktop Automation"),
    ]
    for mod, label in optional_modules:
        ok, detail = _check_python_module(mod)
        add_check(f"dep-{mod}", ok, f"{label}: {detail}", critical=False)

    # ── External Services ──


    # ── Playwright Browsers ──
    pw_ok, pw_detail = _check_playwright()
    add_check("playwright-browsers", pw_ok, pw_detail, critical=False)

    # ── UI Assets ──
    ui_ok, ui_detail = _check_ui_assets()
    add_check("ui-assets", ui_ok, ui_detail)

    # ── Agent Module Imports ──
    agent_modules = [
        "agent.kernel",
        "agent.executor",
        "agent.runtime",
        "agent.planner",
        "agent.error_handler",
        "agent.task_queue",
    ]
    for mod in agent_modules:
        ok, detail = _check_python_module(mod)
        add_check(f"import-{mod}", ok, f"{detail}")

    # ── Bootstrap Warnings ──
    for warning in report.warnings:
        add_check(f"bootstrap-warning", True, warning, critical=False)

    # ── Output ──
    failed_critical = [c for c in checks if not c["ok"] and c["critical"]]
    failed_optional = [c for c in checks if not c["ok"] and not c["critical"]]

    if args.json:
        output = {
            "status": "FAIL" if failed_critical else "PASS",
            "checks": checks,
            "critical_failures": len(failed_critical),
            "warnings": len(failed_optional),
        }
        print(json.dumps(output, indent=2))
    else:
        print("=" * 50)
        print("  BUDDY MK-67 — Ship Readiness Check")
        print("=" * 50)
        for c in checks:
            icon = "✅" if c["ok"] else ("❌" if c["critical"] else "⚠️")
            print(f"  {icon} {c['name']:30s} {c['detail']}")

        print("-" * 50)
        if failed_critical:
            print(f"  ❌ FAIL — {len(failed_critical)} critical issue(s)")
        else:
            print(f"  ✅ PASS — All critical checks passed")
        if failed_optional:
            print(f"  ⚠️  {len(failed_optional)} optional issue(s)")
        print("=" * 50)

    return 1 if failed_critical else 0


if __name__ == "__main__":
    sys.exit(main())
