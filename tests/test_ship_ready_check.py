from __future__ import annotations

import subprocess
import sys
from pathlib import Path


def test_ship_ready_check_runs_as_script():
    project_root = Path(__file__).resolve().parent.parent
    result = subprocess.run(
        [sys.executable, "scripts/ship_ready_check.py"],
        cwd=project_root,
        capture_output=True,
        text=True,
        timeout=20,
    )

    assert "Ship Readiness Check" in result.stdout
    assert "ModuleNotFoundError" not in result.stderr
    assert result.returncode in {0, 1}
