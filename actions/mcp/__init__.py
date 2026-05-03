from __future__ import annotations

from importlib import import_module
from pathlib import Path


_ROOT = Path(__file__).resolve().parent


for module_path in sorted(_ROOT.glob("*.py")):
    if module_path.stem == "__init__":
        continue
    import_module(f"{__name__}.{module_path.stem}")
