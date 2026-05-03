from pathlib import Path


def test_domain_tools_do_not_import_other_domain_tools():
    root = Path("actions")
    forbidden = []
    for path in root.rglob("*.py"):
        text = path.read_text(encoding="utf-8", errors="replace")
        if "from actions." in text and "\\__init__.py" not in str(path):
            if any(part in text for part in ("from actions.files", "from actions.process", "from actions.network")):
                forbidden.append(path)
    assert forbidden == []
